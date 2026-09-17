# Atelier 2 — Pipeline CI avec GitHub Actions

Séance 2 du Bloc DevOps. Objectif : mettre en place un pipeline d'intégration continue (lint, tests en matrice,
cache, artefacts) sur une application Flask fournie, et le rendre obligatoire avant tout merge sur `main`.

## Contenu du dossier

| Chemin | Rôle |
|--------|------|
| `app.py` | Application Flask fournie : `alert_threshold`, `sanitize_input`, endpoints `/health` et `/status` |
| `test_app.py` | Tests unitaires pytest (3 fournis + `test_status_endpoint` ajouté) |
| `requirements.txt` | Dépendances : flask, pytest, pytest-cov, flake8 (versions figées) |
| `.flake8` | Configuration du lint (`max-line-length = 100`) |
| `test-screen/` | Captures d'écran servant de preuves pour chaque étape |

Le workflow est dans [`.github/workflows/ci.yml`](../.github/workflows/ci.yml), à la racine du dépôt : c'est le seul emplacement lu par GitHub.

## Lancer en local

```bash
cd atelier-2
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -v --cov=app --cov-report=term
flake8 . --exclude=.venv
```

## Le pipeline

```
 pull request ou push sur main
            │
            ▼
        ┌──────┐   ✅   ┌─ test (3.10) ─┐
        │ lint │ ─────► ├─ test (3.11) ─┤  en parallèle
        └──────┘        └─ test (3.12) ─┘
            │ ❌               │
            ▼                  ▼
     tests non lancés    rapport de couverture
                          (artefact, même en cas d'échec)
```

| Élément | Réglage |
|---------|---------|
| Déclencheurs | `pull_request` (toutes les PR), `push` limité à `main` |
| Job `lint` | flake8 sur Python 3.12 |
| Job `test` | pytest + couverture, `needs: lint`, matrice Python 3.10 / 3.11 / 3.12 |
| Cache | `actions/cache` sur `~/.cache/pip`, clé basée sur `hashFiles('atelier-2/requirements.txt')` |
| Artefacts | `coverage-<version>` (rapport HTML), envoyés avec `if: always()` |
| Protection | les 4 checks `lint`, `test (3.10)`, `test (3.11)`, `test (3.12)` sont obligatoires pour merger sur `main` |

## Travail réalisé

### 1. Découverte de l'application — PR #15
Application `starter-app` intégrée dans `atelier-2/` **sans modification du code** (`app.py` et `test_app.py` identiques à l'archive).
Seul ajustement : `flake8-config.txt` renommé en `.flake8`, nom attendu par le sujet. Fichiers macOS de l'archive (`.DS_Store`, `__MACOSX/`) écartés.

En local (Python 3.14) : **3 tests passent**, flake8 ne signale rien.

Constats :
- **`/status` n'a aucun test** → ajouté à l'étape 4.
- `app.run(debug=True)` : mode debug Flask si l'application est lancée directement — acceptable en démo, jamais en production.

### 2. Premier workflow minimal — PR #16
Un seul job `test` : `actions/checkout`, `actions/setup-python`, `pip install`, `pytest`.
L'application étant dans `atelier-2/`, les commandes s'exécutent avec `defaults.run.working-directory: atelier-2`.
Run vert dans l'onglet Actions, logs : `3 passed`.

### 3. Déclencheurs push & pull request — PR #16
- **Avant** (`on: [push, pull_request]`) : le commit `b7c37da` a déclenché **2 runs**, `push` et `pull_request`.
- **Après** (`push: branches: [main]`) : le commit `d9eab2f` n'a déclenché **que** `pull_request`.
- Après le merge, run `push` sur `main` (`e429174`) : le déclencheur push fonctionne toujours, mais uniquement sur `main`.

Filtre fait sur `branches` et non sur `paths` (qui filtre les fichiers modifiés, pas la branche).

### 4. Job de lint séparé — PR #17
- Jobs `lint` et `test` séparés, reliés par `needs: lint`.
- **Fail-fast vérifié** : un `import os` inutile (`0737189`) fait échouer `lint` (`F401 'os' imported but unused`) et `test` est **skipped** ; corrigé dans `1da7ada`.
- **Test ajouté** : `test_status_endpoint` vérifie le code 200 et le contenu JSON de `/status` (`b00c7db`) → `4 passed`.

Captures : [lint en échec, test ignoré](test-screen/etape4-lint-echoue-test-skipped.png) · [4 tests passent](test-screen/etape4-logs-4-passed.png)

### 5. Matrix build — PR #18
`strategy.matrix.python-version: ["3.10", "3.11", "3.12"]`, versions entre guillemets (sinon YAML lit `3.10` comme `3.1`).
La version installée est reliée à `${{ matrix.python-version }}`. Vérifié dans les logs de chaque job :

| Job | Python réellement utilisé |
|-----|---------------------------|
| `test (3.10)` | 3.10.21 |
| `test (3.11)` | 3.11.16 |
| `test (3.12)` | 3.12.14 |

Captures : [4 checks](test-screen/etape5-pr-4-checks-matrice.png) · [3.10](test-screen/etape5-logs-python-3.10.png) · [3.11](test-screen/etape5-logs-python-3.11.png) · [3.12](test-screen/etape5-logs-python-3.12.png)

### 6. Cache & artifacts — PR #19
- **Cache pip** : 1er run `Cache not found` puis `Cache saved` ; 2e run (re-run) `Cache restored from key: pip-Linux-3.10-77a39170…`.
  La clé contient l'empreinte de `requirements.txt` : modifier une dépendance change la clé et reconstruit le cache.
  Piège évité : `hashFiles` ne suit pas `working-directory`, le chemin complet `atelier-2/requirements.txt` est nécessaire.
- **Artefacts** : `coverage-3.10`, `coverage-3.11`, `coverage-3.12` (noms distincts, sinon conflit entre jobs de la matrice).
  Couverture de `app.py` : **93 %** — seule la ligne `app.run(debug=True)` n'est pas exécutée par les tests.
- Gain de temps non visible ici (4 petites dépendances) : le cache pip conserve les téléchargements, pas l'installation.

Captures : [checks](test-screen/etape6-pr-checks.png) · [cache vide](test-screen/etape6-cache-not-found-run1.png) · [cache restauré](test-screen/etape6-cache-restored-run2.png) · [rapport HTML](test-screen/etape6-rapport-couverture-html.png)

### 7. Statut CI obligatoire — PR #20
- Ruleset `protection-main` : **Require status checks to pass** avec `lint`, `test (3.10)`, `test (3.11)`, `test (3.12)`.
- **Test du blocage** : `test_alert_threshold` cassé volontairement (`4f62b39`, `assert 25 == 30`) → checks rouges, **merge bloqué**.
  `test (3.10)` et `test (3.11)` apparaissent *Cancelled* : fail-fast de la matrice, qui annule les autres jobs dès le premier échec.
- **`if: always()` vérifié** : les 3 artefacts de couverture ont été envoyés malgré l'échec.
- **Déblocage** : test rétabli (`355edfd`) → 4 checks verts, bouton de merge redevenu actif **sans intervention**, merge fait sans bypass.

Groupe d'une seule personne : pendant le test, la revue obligatoire a été désactivée temporairement (0 approbation, pas de Code Owners)
pour que seule la CI bloque le merge. Elle a été remise ensuite (1 approbation + Code Owners).

Captures : [checks requis](test-screen/etape7-ruleset-checks-requis.png) · [PR bloquée](test-screen/etape7-pr-bloquee-ci-rouge.png) · [PR débloquée](test-screen/etape7-pr-debloquee-ci-verte.png)

### 8. Badge & consolidation — PR #21
Badge de statut ajouté en haut du [README racine](../README.md), avec une description du pipeline.
URL : `https://github.com/MartinFraysse/DevOps-ESIEA/actions/workflows/ci.yml/badge.svg?branch=main` → affiche **passing**.

Capture : [badge](test-screen/etape8-badge-ci-passing.png)

Point d'attention : le merge de la PR #20 a gardé le titre proposé par GitHub (`Test/ci rouge (#20)`), qui ne respecte pas
Conventional Commits. `main` étant protégée contre la réécriture, il n'est pas corrigé ; les titres sont vérifiés avant chaque merge depuis.

## Checklist de livrable

| Point | État |
|-------|------|
| Pipeline sur `main`, déclenché sur push et pull request | ✅ |
| Jobs `lint` et `test` séparés, `needs: lint` | ✅ |
| Tests en matrice sur au moins 2 versions de Python | ✅ 3 versions |
| Cache pip actif (`Cache restored` au 2e run) | ✅ |
| Rapport de couverture en artefact, y compris en cas d'échec | ✅ |
| Checks CI obligatoires, testés avec une PR cassée puis corrigée | ✅ |
| Badge CI visible et fonctionnel | ✅ |
| Au moins un test ajouté par le groupe (`/status`) | ✅ |
