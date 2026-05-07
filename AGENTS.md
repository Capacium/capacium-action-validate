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
