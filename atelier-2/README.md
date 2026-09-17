# Atelier 2 — Pipeline CI avec GitHub Actions

Séance 2 du Bloc DevOps. Objectif : mettre en place un pipeline d'intégration continue (lint, tests en matrice,
cache, artefacts) sur une application Flask fournie, et le rendre obligatoire avant tout merge sur `main`.

## Contenu du dossier

| Chemin | Rôle |
|--------|------|
| `app.py` | Application Flask fournie : `alert_threshold`, `sanitize_input`, endpoints `/health` et `/status` |
| `test_app.py` | Tests unitaires pytest |
| `requirements.txt` | Dépendances : flask, pytest, pytest-cov, flake8 (versions figées) |
| `.flake8` | Configuration du lint (`max-line-length = 100`) |

Le workflow GitHub Actions vivra dans `.github/workflows/` à la racine du dépôt (seul emplacement lu par GitHub).

## Lancer en local

```bash
cd atelier-2
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -v
flake8 . --max-line-length=100 --exclude=.venv
```

## Travail réalisé

### 1. Découverte de l'application fournie
Application `starter-app` intégrée dans `atelier-2/` **sans modification du code** (`app.py` et `test_app.py` identiques à l'archive).
Seul ajustement : `flake8-config.txt` de l'archive renommé en `.flake8`, nom attendu par le sujet et lu automatiquement par flake8.
Fichiers macOS parasites de l'archive (`.DS_Store`, `__MACOSX/`) écartés.

Vérification locale (Python 3.14) :
- `pytest -v` → **3 tests passent** (`test_alert_threshold`, `test_sanitize_input_escapes_html`, `test_health_endpoint`).
- `flake8 . --max-line-length=100 --exclude=.venv` → **aucune erreur**.

Constats à la lecture du code :
- **`/status` n'a aucun test** → à ajouter à l'étape 4.
- `app.run(debug=True)` : mode debug Flask actif si l'application est lancée directement — acceptable en démo, à ne jamais exposer en production.
