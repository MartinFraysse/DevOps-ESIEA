# Étape 3 — Build multi-stage : on installe dans un stage "builder", on n'emporte que le résultat.

# ---- Stage 1 : builder -------------------------------------------------------
FROM python:3.12 AS builder

# Environnement isolé : tout ce qu'on installe atterrit dans /opt/venv, facile à copier d'un bloc.
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
# --no-cache-dir : le cache pip ne sert à rien dans une image.
RUN pip install --no-cache-dir -r requirements.txt

# ---- Stage 2 : image finale --------------------------------------------------
FROM python:3.12-slim

# Étape 7 — Relie automatiquement le package ghcr.io au dépôt GitHub.
LABEL org.opencontainers.image.source="https://github.com/MartinFraysse/DevOps-ESIEA"
LABEL org.opencontainers.image.description="Application Flask de l'atelier 3 (Bloc DevOps ESIEA)"

# Seul le venv est rapatrié : ni compilateurs, ni outils de build, ni cache du stage builder.
COPY --from=builder /opt/venv /opt/venv
# Piège : l'ENV du stage builder n'existe plus ici, il faut le redéclarer.
ENV PATH="/opt/venv/bin:$PATH"

RUN useradd --create-home --uid 1000 appuser

WORKDIR /app
COPY app.py .

USER appuser

EXPOSE 5000

# Étape 6 — Sonde de santé en Python pur : curl/wget sont absents de l'image slim.
# urlopen lève une exception (code de sortie 1) si /health ne répond pas ou renvoie une erreur HTTP.
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/health', timeout=2)"]

# Serveur WSGI de production à la place du serveur de développement Flask.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"]
