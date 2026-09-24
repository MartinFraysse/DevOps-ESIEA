# Atelier 4 — Pipeline CI/CD de bout en bout

Dans cette séance, j'ai complété la CI des séances précédentes pour qu'un push sur `main` aille jusqu'au
déploiement : l'image Docker est construite et publiée sur ghcr.io, puis déployée en blue/green, avec un rollback
automatique si la nouvelle version ne marche pas. Le point de départ était le code final de l'atelier 3.

## Le pipeline

```
 pull request                     push sur main (= merge d'une PR)
      │                                   │
      ▼                                   ▼
   ┌──────┐   ┌──────────────────┐   ┌────────────────┐   ┌──────────────────────┐
   │ lint │ ► │ test 3.10/11/12  │ ► │ build-and-push │ ► │ deploy               │
   └──────┘   └──────────────────┘   └────────────────┘   │ environment:         │
                                        image sur ghcr.io  │ production           │
   sur une PR : build-and-push           tags : <sha> +    │ (attend mon          │
   et deploy sont skipped                latest            │  approbation)        │
                                                           └──────────────────────┘
```

| Job | Quand | Ce qu'il fait |
|-----|-------|---------------|
| `lint` | PR et push sur `main` | flake8 |
| `test` | après `lint` | pytest + couverture sur Python 3.10, 3.11 et 3.12 |
| `build-and-push` | après `test`, push sur `main` seulement | construit l'image et la pousse sur ghcr.io avec le tag du SHA + `latest` |
| `deploy` | après `build-and-push`, push sur `main` seulement | attend l'approbation (environment `production`) puis lance `deploy/deploy.sh` |

`lint` et `test` tournent aussi sur les PR, parce que les règles de `main` demandent ces 4 checks pour merger.

## La stratégie de déploiement : blue/green

```
                    ┌─────────────┐
 curl :8080  ─────► │    nginx    │ ──── trafic ────► app-blue  (version en prod)
                    └─────────────┘                        │
                                                           ├──► redis
                        après la bascule ─ ─ ─► app-green (nouvelle version)
```

Il y a deux copies de l'app, `blue` et `green`. Une seule reçoit le trafic. Pour déployer, `deploy.sh` lance la
nouvelle version sur la couleur libre et la teste. Si elle marche, nginx passe dessus et l'ancienne est arrêtée.
Si elle ne marche pas, le script l'arrête et la production ne bouge pas.

Il y a deux sortes de rollback :

- **automatique** (étapes 4 et 8) : si `/health` ne répond pas 200, ou si `/status` ne renvoie pas la bonne
  couleur et le bon SHA, la bascule n'a pas lieu ;
- **manuel** (étape 7) : si on trouve un problème après le déploiement, on fait un `git revert` et le pipeline
  redéploie la version d'avant.

**Limite :** en CI, le job `deploy` tourne sur une machine neuve à chaque fois, donc la « production » est
simulée et repart de zéro à chaque run (détails à l'étape 5). La bascule blue ↔ green se voit en local.

## Lancer en local

Il faut Docker avec Compose, et `jq`.

```bash
git clone https://github.com/MartinFraysse/DevOps-ESIEA.git
cd DevOps-ESIEA/atelier-4

# construire l'image avec le SHA du commit
docker build --build-arg GIT_SHA=$(git rev-parse HEAD) -t ghcr.io/martinfraysse/devops-web:local .

# déployer (le 1er lancement démarre aussi redis et nginx)
./deploy/deploy.sh local "$(git rev-parse HEAD)"
curl localhost:8080/status        # {"commit":"...","deploy_color":"blue",...}

# relancer la même commande fait basculer sur green
./deploy/deploy.sh local "$(git rev-parse HEAD)"
```

On peut aussi déployer une image publiée par la CI : `./deploy/deploy.sh <sha> <sha>`.

Pour tout arrêter : `docker compose --profile blue --profile green down` (ajouter `-v` pour vider Redis), puis
supprimer `deploy/.active-color` et `deploy/nginx/active.conf`.

**Lancer les tests :** `pip install -r requirements-dev.txt` puis `pytest -v`.

## Fichiers

| Fichier | Rôle |
|---------|------|
| `app.py` | L'app Flask : `/health` vérifie Redis, `/status` renvoie la couleur et le SHA du commit |
| `test_app.py` | Les tests (dont `/health` avec Redis en panne) |
| `Dockerfile` | L'image multi-stage de l'atelier 3, avec en plus le SHA du commit (`GIT_SHA`) |
| `docker-compose.yml` | `redis` + `nginx`, et `app-blue` / `app-green` avec des profiles |
| `deploy/deploy.sh` | Le script de déploiement blue/green avec rollback |
| `deploy/nginx/app.conf.template` | Le modèle de config nginx (le script en fait `active.conf`) |
| `.env.example` | Exemple de config locale (`IMAGE_TAG`) |
| `../.github/workflows/ci.yml` | Le pipeline (à la racine du dépôt, seul endroit lu par GitHub) |
| `screens/` | Mes captures d'écran pour chaque étape |

## Checklist

| Demandé | Fait | Preuve |
|---------|------|--------|
| 4 jobs enchaînés `lint` → `test` → `build-and-push` → `deploy`, build et deploy seulement sur `main` | Oui | Étape 5 |
| Image sur ghcr.io avec un tag SHA + `latest` | Oui | Étape 2 |
| Blue/green en local, avec une vraie bascule (`deploy_color` change) | blue → green | Étape 4 |
| Rollback automatique testé (health cassé → l'ancienne version reste) | Redis coupé | Étape 4 |
| Job `deploy` dans `environment: production` | Avec approbation | Étape 5 |
| Un vrai push qui déclenche tout jusqu'au déploiement | Version 1.1 | Étape 6 |
| Rollback manuel avec `git revert` | Retour à 1.0 | Étape 7 |
| `/health` vérifie Redis, testé Redis démarré et coupé | 200 / 503 | Étape 1 |
| `/status` renvoie le SHA, vérifié par le smoke test, testé avec un SHA faux | `deadbeef` refusé | Étape 8 |
| README qui décrit le pipeline et la stratégie de déploiement | Oui | Ce fichier |

---

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

(Depuis l'étape 8, le script prend aussi le SHA attendu en 2e argument.)

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

## Étape 5 — Job `deploy` dans la CI

Le pipeline a maintenant 4 jobs : `lint` → `test` → `build-and-push` → `deploy`. Le job `deploy` tourne après
`build-and-push`, seulement sur un push sur `main`, et appelle `deploy.sh` avec le SHA du commit : il déploie donc
exactement l'image qui vient d'être construite.

Le job est dans un `environment: production`. Dans les réglages du dépôt (*Settings → Environments*), j'ai mis
une règle **Required reviewers** : le déploiement attend que je l'approuve avant de partir. C'est un garde-fou
avant de toucher la production, même si ici elle est simulée. Ce réglage se fait dans GitHub, pas dans le YAML.

**Limite :** chaque job tourne sur une machine neuve, qui est supprimée à la fin. Il n'y a donc ni
`.active-color`, ni image, ni conteneur d'un run à l'autre : en CI, chaque déploiement est un premier
déploiement (sur `blue`). C'est pour ça que `deploy.sh` démarre lui-même `redis` et `nginx`, et que l'image est
téléchargée depuis ghcr.io. La vraie bascule blue ↔ green est testée en local (étape 4). Pour garder l'état
entre deux déploiements, il faudrait déployer sur un vrai serveur.

Sur une pull request, `build-and-push` et `deploy` sont `skipped` : on ne publie et on ne déploie rien tant que ce
n'est pas mergé sur `main` :

![PR : build et deploy skipped](screens/etape5-pr-build-deploy-skipped.png)

Après un push sur `main`, les 4 jobs s'enchaînent et `deploy` attend mon approbation :

![4 jobs, deploy en attente](screens/etape5-4-jobs-deploy-en-attente.png)

## Étape 6 — Test de bout en bout

J'ai fait un vrai changement visible de l'extérieur : `/status` renvoie `"version":"1.1"` au lieu de `"1.0"`
(PR #38). Après le merge sur `main`, tout le pipeline s'est déroulé tout seul ; la seule action manuelle a été
d'approuver le déploiement. Dans les logs du job `deploy`, nginx renvoie bien la version 1.1 :

![deploy version 1.1](screens/etape6-deploy-version-1-1.png)

## Étape 7 — Rollback manuel avec `git revert`

On imagine qu'on découvre un problème avec la version 1.1 **après** son déploiement. Le rollback automatique de
l'étape 4 ne peut rien faire ici : la 1.1 répondait bien sur `/health`, donc elle a été validée.

Au lieu de modifier la production à la main, j'annule le commit avec Git et je laisse le pipeline redéployer :

```bash
git switch main && git pull
git log --oneline -5                       # le commit à annuler : 815826f (#38)
git switch -c revert/version-1-1
git revert 815826f                         # commit fait par squash = un seul parent, pas besoin de -m
git show HEAD                              # je relis le diff avant de pousser
git push -u origin revert/version-1-1      # puis PR #39 et merge
```

Le diff ne change qu'une ligne (`version="1.1"` redevient `"1.0"`) et `app.py` est revenu exactement comme avant
la PR #38. Comme `main` est protégée, le revert passe lui aussi par une PR. Après le merge et l'approbation, la
production renvoie de nouveau la version 1.0 :

![deploy version 1.0 après le revert](screens/etape7-deploy-version-1-0.png)

## Étape 8 — Vérifier que c'est la bonne version qui est déployée

Jusqu'ici, le smoke test vérifiait seulement `deploy_color`. Deux images différentes avec la même couleur
passaient le test : on savait que la couleur répondait, mais pas quel code tournait dedans.

- La CI donne le SHA du commit au build (`--build-arg GIT_SHA=...`), et le `Dockerfile` le met dans une variable
  d'environnement de l'image (`ARG` + `ENV` dans le dernier stage, tout en bas pour garder le cache).
- `/status` renvoie ce SHA dans un champ `commit`.
- `deploy.sh` prend un 2e argument, le SHA attendu. La CI lui passe `github.sha`. Si `/status` ne renvoie pas ce
  SHA, le déploiement échoue comme un `/health` cassé : la nouvelle couleur est arrêtée et le trafic ne bouge pas.

Le SHA est mis dans l'image au moment du **build**, pas au déploiement : si `deploy.sh` donnait lui-même le SHA
au conteneur puis le comparait avec… ce même SHA, le test serait toujours bon et ne prouverait rien.

Pour tester en local :

```bash
docker build --build-arg GIT_SHA=$(git rev-parse HEAD) -t ghcr.io/martinfraysse/devops-web:local .
./deploy/deploy.sh local "$(git rev-parse HEAD)"   # bon SHA : bascule
./deploy/deploy.sh local deadbeef                  # SHA faux : refusé, la couleur ne change pas
```

Avec un SHA faux, le déploiement est refusé et la couleur active ne change pas :

![SHA faux refusé](screens/etape8-sha-faux-rejete.png)
