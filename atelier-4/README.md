# Atelier 4 — Pipeline CI/CD de bout en bout

Point de départ : les fichiers finaux de l'atelier 3 (app Flask + Redis, Dockerfile multi-stage, docker-compose).

Le compte rendu complet de la séance sera ajouté ici à la fin de l'atelier.

## Étape 1 — Un `/health` qui vérifie vraiment quelque chose

Avant, `/health` renvoyait toujours `200`, même si Redis était arrêté. Le script de déploiement va se servir de
`/health` pour savoir si une nouvelle version marche : avec un `200` fixe, une version cassée serait mise en
production comme une bonne.

Maintenant, `/health` envoie un `PING` à Redis :

- Redis répond → **200** `{"redis":"ok","status":"ok"}`
- Redis ne répond pas → **503** `{"redis":"down","status":"error"}`

J'ai ajouté un timeout de 2 secondes sur la connexion à Redis. Sans ça, `/health` peut rester bloqué au lieu de
renvoyer 503.

Côté tests, le test de `/health` utilise maintenant `fakeredis` (il n'y a pas de Redis dans la CI), et j'ai ajouté
un test qui vérifie le 503 avec un faux Redis en panne.

Test en vrai : `200` avec Redis démarré, puis `503` après `docker compose stop redis` :

![health 200 puis 503](screens/etape1-health-200-puis-503.png)

## Étape 2 — Job `build-and-push`

J'ai ajouté un 3e job à la CI : `build-and-push`. Il construit l'image Docker (le Dockerfile multi-stage de
l'atelier 3) et la pousse sur ghcr.io avec deux tags :

- **le SHA du commit** : il ne bouge jamais, donc on sait exactement quelle version tourne ;
- **`latest`** : toujours la dernière image, il change à chaque push.

Le job attend que `test` soit vert (`needs: test`) et ne tourne que sur un push sur `main`. Sur une pull request
il est `skipped`, pour ne pas publier une image à chaque PR.

Deux points de config à ne pas oublier :

- `permissions: packages: write` dans le job, sinon le `GITHUB_TOKEN` n'a pas le droit de pousser l'image ;
- le package `devops-web` avait été créé à la main à l'atelier 3, donc il a fallu autoriser le dépôt dans
  *Package settings → Manage Actions access* (rôle **Write**), sinon erreur 403.

![Manage Actions access](screens/etape2-actions-access.png)

Le Dockerfile reçoit aussi le SHA du commit (`--build-arg GIT_SHA`), il servira à l'étape 8.

Après le merge, le pipeline a tourné sur `main` : `build-and-push` est passé après `test`, et l'image est sur
ghcr.io avec le tag du SHA et `latest` (même image) :

![package avec les tags sha et latest](screens/etape2-package-tags.png)

## Étape 3 — Environnement blue/green

Le `docker-compose.yml` a maintenant 4 services :

| Service | Démarre | Rôle |
|---------|---------|------|
| `redis` | toujours | la base, comme à l'atelier 3 |
| `nginx` | toujours | reçoit le trafic sur le port 8080 et l'envoie vers la couleur active |
| `app-blue` | avec `--profile blue` | l'app avec `DEPLOY_COLOR=blue` |
| `app-green` | avec `--profile green` | la même app avec `DEPLOY_COLOR=green` |

Les `profiles` sont seulement sur les deux apps : `redis` et `nginx` doivent tourner quelle que soit la couleur.
Les apps n'ont plus de `ports`, tout passe par nginx.

`/status` renvoie maintenant la couleur (`deploy_color`), ce qui permet de voir vers quelle app nginx envoie le
trafic.

La config de nginx est créée à partir de `deploy/nginx/app.conf.template`, en remplaçant `COLOR` par la couleur
active. Le fichier obtenu, `deploy/nginx/active.conf`, n'est pas dans Git : le script de l'étape 4 le réécrit à
chaque bascule. Deux pièges :

- nginx refuse de démarrer si l'app vers laquelle il envoie le trafic n'est pas lancée. Avec `resolver` et une
  variable dans `proxy_pass`, nginx ne cherche l'app qu'au moment de la requête : il démarre quand même et
  renvoie 502 en attendant ;
- il faut monter le **dossier** `deploy/nginx` dans nginx, pas juste le fichier, sinon nginx ne voit pas les
  changements quand le fichier est réécrit.

Pour tester en local :

```bash
docker build -t ghcr.io/martinfraysse/devops-web:local .
sed "s/COLOR/blue/" deploy/nginx/app.conf.template > deploy/nginx/active.conf
export IMAGE_TAG=local
docker compose up -d                   # redis + nginx seulement
docker compose --profile blue up -d    # + app-blue
curl localhost:8080/status             # {"deploy_color":"blue", ...}
```

## Étape 4 — Script de déploiement et rollback

Le script `deploy/deploy.sh` déploie une image sur la couleur qui ne sert pas le trafic, et ne bascule que si la
nouvelle version marche :

```
./deploy/deploy.sh <tag de l'image>      # ex : ./deploy/deploy.sh local
```

1. il lit la couleur active dans `deploy/.active-color` (fichier pas dans Git). S'il n'existe pas, c'est le
   premier déploiement : le script démarre `redis` et `nginx` ;
2. il lance l'autre couleur avec la nouvelle image ;
3. il attend que `/health` réponde 200 (10 essais, 3 secondes entre chaque, parce que l'app met un peu de temps à
   démarrer), puis fait un smoke test : `/status` doit renvoyer la bonne couleur ;
4. **si tout est bon** : il réécrit la config nginx, fait `nginx -s reload` (pas besoin de redémarrer nginx),
   enregistre la nouvelle couleur, et seulement après il arrête l'ancienne. Dans l'autre ordre, plus personne ne
   répondrait pendant quelques secondes ;
   **sinon** : il arrête la nouvelle version et sort en erreur. La couleur active ne change pas.

Les appels à `/health` et `/status` sont faits depuis le conteneur nginx (`docker compose exec nginx wget ...`),
parce que les apps n'ont pas de port ouvert sur la machine.

J'ai utilisé `--no-deps` pour lancer la nouvelle couleur : sans ça, Docker Compose relance Redis tout seul (à
cause du `depends_on`), et on ne peut plus tester le cas où Redis est arrêté.

J'ai vérifié le script avec `shellcheck`, il ne signale rien.

**Déploiement qui marche** : la couleur passe de `blue` à `green`, et nginx envoie bien le trafic vers `green` :

![bascule ok](screens/etape4-bascule-ok.png)

**Déploiement qui échoue** : Redis est arrêté, donc `/health` renvoie 503. Après 10 essais le script abandonne,
arrête `blue`, et `green` reste la couleur active :

![échec, couleur inchangée](screens/etape4-echec-couleur-inchangee.png)
