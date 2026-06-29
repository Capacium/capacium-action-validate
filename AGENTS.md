# Capacium Action Validate — Agents Guide

## Language
**English is REQUIRED for ALL Capacium content.**

## Project
GitHub Action (composite) to validate `capability.yaml` manifests in any repo.

## Tech Stack
- Composite GitHub Action (YAML)
- Python 3 + PyYAML (installed at runtime)

## Key Files
| File | Purpose |
|------|---------|
| `action.yml` | Action definition (inputs, outputs, runs) |
| `validate.py` | Manifest validation — checks schema, required fields |
| `sync_version.py` | Version sync with release tags |

## Action Inputs
| Input | Default | Description |
|-------|---------|-------------|
| `strict` | `false` | Fail on warnings |
| `sync_version` | `false` | Sync version from git tag |

## Testing
```bash
python3 validate.py --manifest capability.yaml
python3 sync_version.py
```

## Where to work — Forgejo-first

- **Canonical origin:** Forgejo `git@git.langevc.com:capacium/capacium-action-validate.git` — work **here**.
- **GitHub** `github.com/Capacium/capacium-action-validate` is a read-only mirror (force-pushed from Forgejo) — do **not** push there.
- **Local clone:** `~/Documents/repositories/forgejo/capacium/capacium-action-validate` (layout `<provider>/<org>/<repo>`); remotes `origin`=Forgejo, `github`=mirror.
- Pull requests on Forgejo. CI: Forgejo for dev; some workflows are guarded to GitHub (hybrid) — see `capacium-internal-docs/docs/develop/forgejo-first-workflow.md`.
