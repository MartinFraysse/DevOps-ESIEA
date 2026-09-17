# DevOps-ESIEA

Dépôt de l'atelier **Git avancé & collaboratif** — Bloc DevOps, ESIEA S9.

## Stratégie de branches : trunk-based development

- `main` est la **seule branche permanente**. Elle doit toujours rester stable.
- Tout travail se fait sur une **branche courte** (quelques heures, 2 jours maximum), créée depuis `main`.
- Une branche courte revient dans `main` **uniquement via une Pull Request**.

## Convention de nommage des branches

Format : `<type>/<description>`

| Type       | Usage                                  | Exemple                   |
|------------|----------------------------------------|---------------------------|
| `feat`     | Nouvelle fonctionnalité                | `feat/page-connexion`     |
| `fix`      | Correction de bug                      | `fix/crash-au-demarrage`  |
| `docs`     | Documentation uniquement               | `docs/guide-contribution` |
| `chore`    | Maintenance, configuration, outillage  | `chore/update-gitignore`  |
| `refactor` | Restructuration sans changement de comportement | `refactor/module-auth` |
| `test`     | Ajout ou correction de tests           | `test/api-utilisateurs`   |
| `ci`       | Pipeline d'intégration continue        | `ci/github-actions`       |

Règles : minuscules, mots séparés par des tirets, pas d'espaces ni d'accents.

Les messages de commit suivent le même vocabulaire ([Conventional Commits](https://www.conventionalcommits.org/fr/)) :
`<type>(<scope>): <description>` — par exemple `feat(calc): ajoute power`.
Le scope (zone touchée : `calc`, `contributing`, `github`, `hooks`...) est recommandé.

## Règle de merge

- **Aucun push direct sur `main`** : uniquement des Pull Request.
- La PR doit être à jour avec `main` et passer les vérifications avant d'être fusionnée.
- Mode de merge : **Squash and merge**.
- La branche est **supprimée après le merge**.

## Workflow type

```bash
git switch main && git pull              # partir d'un main à jour
git switch -c feat/ma-fonctionnalite     # créer une branche courte
# ... travailler, committer ...
git push -u origin feat/ma-fonctionnalite
# ouvrir la Pull Request sur GitHub, puis Squash and merge
git switch main && git pull              # récupérer le résultat
git branch -d feat/ma-fonctionnalite     # nettoyer la branche locale
```

## Activer le hook anti-secret

Après chaque clone :

```bash
git config core.hooksPath hooks
```

## Membres

- Martin Fraysse — groupe d'une seule personne.

Les commits apparaissent sous deux identités (commits locaux et squash-merges GitHub) :
le fichier `.mailmap` les regroupe pour `git shortlog -sn`.

## Travail réalisé — Séance 1 (Git avancé & collaboratif)

### 1. Dépôt et stratégie de branches
Dépôt publié sur GitHub, stratégie **trunk-based** documentée ci-dessus (nommage, règle de merge),
`.gitignore` posé dès le premier commit (secrets, IDE, dépendances, artefacts Python).

### 2. Rebase interactif — PR #1
Branche `docs/guide-contribution` volontairement brouillonne (4 commits : faute de frappe, `wip`, message vague)
nettoyée avant la PR avec `git rebase -i main` : `pick`, `squash`, `fixup`, `reword`. Branche jamais partagée avant le rebase.

### 3. Conflit de merge — PR #2 et #3
`docs/titre-guide` et `docs/titre-contribuer`, parties du même commit, modifiaient la ligne 1 de `CONTRIBUTING.md`.
Après le merge de #2, le merge de `origin/main` dans la seconde branche a échoué ; résolution manuelle (commit e7d9e23), sans marqueur résiduel.
**Cause** : deux titres concurrents. **Choix** : « Contribuer au projet », formulation orientée action.

### 4. Incident — bisect et cherry-pick
- **Bisect (PR #4)** : `add(2, 3)` renvoyait `-1`. `git bisect run python3 test_add.py` entre `d74b8f7` (bon) et `7f81a43` (mauvais)
  a isolé le commit fautif **a8c9e0e `feat(calc): ajoute mul`**, qui remplaçait `a + b` par `a - b`. Corrigé dans la même PR.
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
- Hook `hooks/pre-commit` : refuse les lignes ajoutées contenant une clé AWS, un jeton GitHub/Slack, une clé d'API `sk-…`,
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
