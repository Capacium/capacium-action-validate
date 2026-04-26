# Capacium Validate Action

[![GitHub Marketplace](https://img.shields.io/badge/Marketplace-Capacium_Validate-blue?logo=github)](https://github.com/marketplace/actions/capacium-validate)
![GitHub Actions](https://img.shields.io/badge/actions-composite-brightgreen)
![License](https://img.shields.io/badge/license-Apache--2.0-blue)
![CI](https://github.com/Capacium/capacium-action-validate/actions/workflows/ci.yml/badge.svg)

GitHub Action to validate `capability.yaml` manifest files for the [Capacium](https://github.com/Capacium) ecosystem.

Works with: `capability.yaml` | `capability.yml` | Bundles | MCP Servers | AI Agent Skills

## Quick Start

```yaml
name: Validate
on: [push]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: Capacium/capacium-action-validate@v1
```

## Inputs

| Name | Required | Default | Description |
|------|----------|---------|-------------|
| `manifest-path` | No | `capability.yaml` | Path to the manifest file to validate |
| `strict-mode` | No | `false` | Fail on warnings in addition to errors |
| `exchange-metadata-output` | No | `false` | Generate normalized Exchange metadata artifact |

## Outputs

| Name | Description |
|------|-------------|
| `valid` | Boolean indicating whether the manifest passed validation |
| `findings-count` | Total number of findings (errors + warnings) |
| `error-count` | Number of errors found |
| `warning-count` | Number of warnings found |

## Full Example

```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: Capacium/capacium-action-validate@v1
        id: validate
        with:
          manifest-path: capability.yaml
          strict-mode: 'true'
          exchange-metadata-output: 'true'

      - name: Check validation result
        if: steps.validate.outputs.valid == 'false'
        run: |
          echo "Validation failed!"
          echo "Errors: ${{ steps.validate.outputs.error-count }}"
          echo "Warnings: ${{ steps.validate.outputs.warning-count }}"
          exit 1
```

## Local Development

```bash
pip install pyyaml
python src/validate.py
```

Set environment variables to customize:

```bash
MANIFEST_PATH=path/to/capability.yaml python src/validate.py
STRICT_MODE=true python src/validate.py
EXCHANGE_METADATA_OUTPUT=true python src/validate.py
```

## License

Apache-2.0
