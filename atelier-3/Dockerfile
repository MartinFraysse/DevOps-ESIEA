# Étape 1 — Dockerfile naïf : une seule étape, image de base complète.
# Volontairement non optimisé (taille, root, pas de .dockerignore) : corrigé aux étapes suivantes.
FROM python:3.12

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

EXPOSE 5000

# --host=0.0.0.0 : sans ça Flask n'écoute que sur 127.0.0.1 *dans* le conteneur,
# et l'application reste injoignable depuis l'hôte malgré le port publié.
CMD ["flask", "--app", "app", "run", "--host=0.0.0.0", "--port=5000"]
