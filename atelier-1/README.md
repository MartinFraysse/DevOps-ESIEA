# Atelier 1 — Git avancé & collaboratif

Séance 1 du Bloc DevOps. Objectif : pratiquer les commandes Git avancées et les réglages collaboratifs de GitHub.

## Contenu du dossier

| Chemin | Rôle |
|--------|------|
| `src/calc.py` | Petite calculatrice servant de support au bisect et au cherry-pick |
| `preuves/` | Traces de la séance : capture du rebase, journal du bisect, script de test |

Fichiers créés pendant cette séance mais placés à la racine, car ils s'appliquent à tout le dépôt :
`.github/CODEOWNERS`, `hooks/pre-commit`, `.mailmap`, `.gitignore`, `CONTRIBUTING.md`.

Utilisation :

```bash
python3 atelier-1/src/calc.py add 2 3      # 5.0
python3 atelier-1/src/calc.py mean 1 2 3 4 # 2.5
```

> Pendant la séance, la calculatrice se trouvait dans `src/calc.py` à la racine : les SHA et PR cités ci-dessous
> font référence à cet emplacement (`git log --follow atelier-1/src/calc.py` pour suivre l'historique).

## Travail réalisé

### 1. Dépôt et stratégie de branches
Dépôt publié sur GitHub, stratégie **trunk-based** documentée dans le [README racine](../README.md) (nommage, règle de merge),
`.gitignore` posé dès le premier commit (secrets, IDE, dépendances, artefacts Python).

### 2. Rebase interactif — PR #1
Branche `docs/guide-contribution` volontairement brouillonne (4 commits : faute de frappe, `wip`, message vague)
nettoyée avant la PR avec `git rebase -i main` : `pick`, `squash`, `fixup`, `reword`. Branche jamais partagée avant le rebase.
Preuve : [`preuves/rebase-avant-apres.jpg`](preuves/rebase-avant-apres.jpg) (4 commits avant, 2 après).

### 3. Conflit de merge — PR #2 et #3
`docs/titre-guide` et `docs/titre-contribuer`, parties du même commit, modifiaient la ligne 1 de `CONTRIBUTING.md`.
Après le merge de #2, le merge de `origin/main` dans la seconde branche a échoué ; résolution manuelle (commit e7d9e23), sans marqueur résiduel.
**Cause** : deux titres concurrents. **Choix** : « Contribuer au projet », formulation orientée action.

### 4. Incident — bisect et cherry-pick
- **Bisect (PR #4)** : `add(2, 3)` renvoyait `-1`. `git bisect run python3 ../test_add.py` entre `d74b8f7` (bon) et `7f81a43` (mauvais)
  a isolé le commit fautif **a8c9e0e `feat(calc): ajoute mul`**, qui remplaçait `a + b` par `a - b`. Corrigé dans la même PR.
  Preuves : [`preuves/test_add.py`](preuves/test_add.py) (test reproductible, gardé hors du dépôt pendant le bisect) et [`preuves/bisect-log.txt`](preuves/bisect-log.txt).
- **Cherry-pick (PR #6)** : le hotfix division par zéro `bd5a853` (sur `main`) a été porté seul sur la branche figée `release/1.0`
  avec `git cherry-pick` → `e7fa763`. Même modification, SHA différent (nouveau commit, parent différent).

### 5. CODEOWNERS et revue — PR #7 à #9
`.github/CODEOWNERS` découpe le dépôt en zones (`*`, `*.py`, `*.md`, `/.github/`), syntaxe validée par
`gh api repos/MartinFraysse/DevOps-ESIEA/codeowners/errors`. Revue de fond sur #8 (`mean` échouait sur un générateur) :
correctif ajouté dans la PR, point 2 traité dans #9.
Limite : groupe d'une personne, GitHub interdit d'approuver sa propre PR — un second Code Owner (formateur) est nécessaire pour une approbation formelle.

### 6. Protection de branche et de tags
Rulesets GitHub actifs :
- `protection-main` (branche par défaut) : PR obligatoire, 1 approbation, revue Code Owner, historique linéaire,
  squash-merge uniquement, suppression et force-push interdits. Push direct sur `main` testé : refusé.
- `protection-tags` (`refs/tags/v*`) : déplacement, suppression et force-push interdits, sans exception.
  Suppression testée : `git push origin :refs/tags/v1.0.0` → refusée (`GH013: Cannot delete this tag`).

Exception assumée : le rôle *Repository admin* peut contourner la règle **uniquement via une PR** (`bypass_mode: pull_request`),
jamais par push direct. Avec un groupe d'une seule personne, personne ne peut approuver les PR (GitHub interdit d'approuver
sa propre PR) : sans cette exception, aucun merge ne serait possible. Dès qu'un second relecteur (formateur) est Code Owner,
l'exception est à retirer pour que la revue s'applique aussi aux administrateurs.

### 7. Sécurité du dépôt — PR #10
- Hook [`hooks/pre-commit`](../hooks/pre-commit) (racine du dépôt) : refuse les lignes ajoutées contenant une clé AWS, un jeton GitHub/Slack, une clé d'API `sk-…`,
  une clé privée PEM ou une affectation en dur (`password = "…"`). Testé : faux secrets refusés, commit normal accepté.
- Commit `29ce25e` signé avec une clé SSH (`gpg.format ssh`) enregistrée comme *Signing Key* sur GitHub → badge **Verified**.

### 8. Conventional Commits et SemVer
Tous les commits de `main` suivent `type(scope): description`.

| Tag | Cible | Justification |
|-----|-------|---------------|
| `v1.0.0` | `release/1.0` | Première release : calculatrice + hotfix division par zéro |
| `v1.1.0` | `main` | Nouvelles fonctionnalités rétrocompatibles (`power`, `mean` en CLI) + correctifs → incrément **MINOR** |

Aucun changement cassant l'interface (`add`, `sub`, `mul`, `div`, `mod`, `mean`) : pas de MAJOR.
`mean([])` lève désormais `ValueError` au lieu de `ZeroDivisionError` : traité comme un correctif (PATCH),
l'ancien comportement étant un plantage non documenté et non un contrat de l'API.
