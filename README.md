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
`<type>: <description>` — par exemple `feat: ajoute la page de connexion`.

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

## Membres

- Martin Fraysse
