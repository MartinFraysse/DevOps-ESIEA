# Atelier 3 — Conteneurisation Docker

Séance 3 du Bloc DevOps. Objectif : conteneuriser l'application Flask de la séance 2, optimiser l'image
(non-root, multi-stage), orchestrer `web` + `redis` avec Docker Compose et publier l'image sur un registry.

## Contenu du dossier

| Chemin | Rôle |
|--------|------|
| `app.py` | Application Flask fournie (starter-app) : `alert_threshold`, `sanitize_input`, `/health`, `/status` |
| `test_app.py` | Tests unitaires pytest fournis |
| `requirements.txt` | Dépendances figées : flask, redis, pytest, pytest-cov, flake8, fakeredis |
| `.flake8` | Configuration du lint (`max-line-length = 100`) |
| `Dockerfile` | Image de l'application |
| `screens/` | Captures d'écran servant de preuves pour chaque étape |

## Étape 1 — Premier Dockerfile naïf

Premier jet volontairement simple : une seule étape, image complète `python:3.12`, on copie le code, on installe
les dépendances, on démarre l'application.

```dockerfile
FROM python:3.12
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 5000
CMD ["flask", "--app", "app", "run", "--host=0.0.0.0", "--port=5000"]
```

**Piège évité :** le `app.run(debug=True)` de `app.py` écoute par défaut sur `127.0.0.1`, c'est-à-dire
uniquement à l'intérieur du conteneur. Le conteneur tournerait sans erreur mais resterait injoignable depuis
l'hôte, même avec `-p`. On démarre donc Flask avec `--host=0.0.0.0` pour écouter sur toutes les interfaces
du conteneur.

```bash
cd atelier-3
docker build -t devops-web:naive .
docker run -d --name web-naive -p 5000:5000 devops-web:naive
curl http://localhost:5000/health
```

### Preuves

| Fichier | Origine | Ce qu'il montre |
|---------|---------|-----------------|
| [`etape1-docker-build.png`](screens/etape1-docker-build.png) | Fin de `docker build -t devops-web:naive .`, depuis `atelier-3/` | Image construite et taguée `devops-web:naive` |
| [`etape1-docker-ps.png`](screens/etape1-docker-ps.png) | `docker ps`, après `docker run -d --name web-naive -p 5000:5000 devops-web:naive` | Conteneur `Up`, port publié `0.0.0.0:5000->5000/tcp` |
| [`etape1-curl-health-status.png`](screens/etape1-curl-health-status.png) | `curl http://localhost:5000/health` et `/status`, lancés **depuis l'hôte** | `{"status":"ok"}` et le JSON de `/status` : l'application est joignable hors du conteneur |

![docker build](screens/etape1-docker-build.png)

![docker ps](screens/etape1-docker-ps.png)

![curl /health et /status depuis l'hôte](screens/etape1-curl-health-status.png)
