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

# Seul le venv est rapatrié : ni compilateurs, ni outils de build, ni cache du stage builder.
COPY --from=builder /opt/venv /opt/venv
# Piège : l'ENV du stage builder n'existe plus ici, il faut le redéclarer.
ENV PATH="/opt/venv/bin:$PATH"

RUN useradd --create-home --uid 1000 appuser

WORKDIR /app
COPY app.py .

USER appuser

EXPOSE 5000

# Serveur WSGI de production à la place du serveur de développement Flask.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"]
