# DevOps-ESIEA

Dépôt des ateliers du **Bloc DevOps** — ESIEA S9.

## Ateliers

| Dossier | Séance | Sujet |
|---------|--------|-------|
| [`atelier-1/`](atelier-1/) | 1 | Git avancé & collaboratif |
| [`atelier-2/`](atelier-2/) | 2 | Pipeline CI avec GitHub Actions |

Chaque dossier contient son propre `README.md` qui documente le travail réalisé pendant la séance.

## Organisation du dépôt

```
.
├── .github/CODEOWNERS   # propriétaires par zone (doit rester à la racine pour GitHub)
├── .gitignore           # exclusions communes à tous les ateliers
├── hooks/pre-commit     # hook anti-secret, appliqué à tout le dépôt
├── atelier-1/
└── atelier-2/
```

Les fichiers de la racine s'appliquent à tout le dépôt ; tout ce qui est propre à une séance vit dans son dossier.

## Stratégie de branches : trunk-based development

- `main` est la **seule branche permanente**. Elle doit toujours rester stable.
- Tout travail se fait sur une **branche courte** (quelques heures, 2 jours maximum), créée depuis `main`.
- Une branche courte revient dans `main` **uniquement via une Pull Request**.
- Exception : les branches de release figées (`release/<version>`), qui ne reçoivent que des correctifs par cherry-pick.

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
- Les tags de release `v*` sont protégés (ni déplacement ni suppression) ; détails dans [`atelier-1/`](atelier-1/README.md#6-protection-de-branche-et-de-tags).

## Workflow type

```bash
git switch main && git pull              # partir d'un main à jour
git switch -c feat/ma-fonctionnalite     # créer une branche courte
# ... travailler, committer ...
git push -u origin feat/ma-fonctionnalite
# ouvrir la Pull Request sur GitHub, puis Squash and merge
git switch main && git pull              # récupérer le résultat
git branch -D feat/ma-fonctionnalite     # nettoyer la branche locale (-D : le squash crée un nouveau commit)
```

## Activer le hook anti-secret

Après chaque clone :

```bash
git config core.hooksPath hooks
```

## Membres

- Martin Fraysse — groupe d'une seule personne.

Les commits arrivent sur `main` par squash-merge GitHub, sous l'identité `MartinFraysse` ; seul le commit initial
porte l'identité locale `Martin`. `git shortlog -sn` affiche donc deux lignes pour une même personne.
