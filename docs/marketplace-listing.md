# GitHub Marketplace Listing — Capacium Validate

## Listing Info

| Field | Value |
|-------|-------|
| Name | Capacium Validate |
| Description | Validate capability.yaml manifest files for the Capacium ecosystem |
| Categories | Code Quality, Continuous Integration |
| Plans | Free (public repositories), Free (private repositories) |

## About

The Capacium Validate Action ensures that `capability.yaml` manifest files
conform to the Capacium specification before they are published to the
Capacium Exchange. It validates schema correctness, kind/variant enum values,
semantic versioning, dependency constraints, and package structure.

## Key Features

- **Schema Validation**: Required fields, enum kinds, semver format
- **Fingerprint Integrity**: SHA-256 content fingerprinting
- **Package Lint**: Structural hygiene checks (expected files, dot-files, README)
- **Exchange Metadata**: Generates normalized JSON artifact for Exchange ingestion
- **Strict Mode**: Optional fail-on-warnings for CI enforcements

## Screenshots

_Screenshots to add: validation output example, pull request check annotation_

## Developer Program Application

This section is for the GitHub Developer Program application.

### Application Fields

1. **Company or Developer Name**: Capacium
2. **Contact Email**: _(to be added)_
3. **App Type**: GitHub Action (composite)
4. **Primary Language/Platform**: Python (stdlib), YAML
5. **Number of Users**: Targeting Capacium ecosystem — initial launch
6. **Integration Description**: Validates Capacium manifests on push/PR;
   outputs metadata for Exchange sync; enforces package quality gates

### Materials Checklist

- [x] Public repository with README
- [x] Apache-2.0 LICENSE
- [x] action.yml with branding (icon + color)
- [x] CI workflow (validates own manifest)
- [x] Input/output documentation
- [x] Usage examples
- [ ] Verified Marketplace badge (after listing approval)

### Developer Program Submission Notes

- Listing category: "Code Quality" (primary), "Continuous Integration" (secondary)
- Composite action — no Docker required, fast execution on all runners
- Runs on ubuntu-latest only (pip install pyyaml)
- First-time listing: will go through GitHub Marketplace review
