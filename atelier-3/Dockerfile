# Étapes 1-2 — Dockerfile naïf : une seule étape, image de base complète.
# Étape 2 : exécution en utilisateur non-root + .dockerignore pour limiter le contexte de build.
FROM python:3.12

WORKDIR /app

COPY . .

# Installé en root : l'utilisateur applicatif n'a pas le droit d'écrire dans le site-packages système.
RUN pip install -r requirements.txt

# Utilisateur dédié, sans droits d'écriture sur le code (fichiers copiés restés propriété de root).
RUN useradd --create-home --uid 1000 appuser

# USER en dernier : toutes les instructions suivantes, et le processus du conteneur, tournent en appuser.
USER appuser

EXPOSE 5000

# --host=0.0.0.0 : sans ça Flask n'écoute que sur 127.0.0.1 *dans* le conteneur,
# et l'application reste injoignable depuis l'hôte malgré le port publié.
CMD ["flask", "--app", "app", "run", "--host=0.0.0.0", "--port=5000"]
