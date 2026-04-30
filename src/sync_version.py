"""Sync capability.yaml version with GitHub release tag.

Reads the manifest, compares version with RELEASE_TAG (stripping 'v' prefix),
updates the file if they differ, commits and pushes via the GitHub Actions
provided GITHUB_TOKEN.
"""

import os
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("::error::PyYAML is required. Run: pip install pyyaml")
    sys.exit(1)

MANIFEST_PATH = Path(os.environ.get("MANIFEST_PATH", "capability.yaml"))
RELEASE_TAG = os.environ.get("RELEASE_TAG", "").lstrip("v")

if not RELEASE_TAG:
    print("::notice::No RELEASE_TAG set — skipping version sync")
    sys.exit(0)

if not MANIFEST_PATH.exists():
    print(f"::warning::Manifest not found at {MANIFEST_PATH}")
    sys.exit(0)

manifest = yaml.safe_load(MANIFEST_PATH.read_text())
if not isinstance(manifest, dict):
    print("::error::Manifest is not a valid YAML mapping")
    sys.exit(1)

current_version = str(manifest.get("version", ""))
if current_version == RELEASE_TAG:
    print(f"::notice::Version already matches tag ({RELEASE_TAG}) — nothing to sync")
    sys.exit(0)

print(f"Syncing version: {current_version} → {RELEASE_TAG}")

MANIFEST_PATH.write_text(
    MANIFEST_PATH.read_text().replace(
        f"version: {current_version}",
        f"version: {RELEASE_TAG}",
    )
)

manifest = yaml.safe_load(MANIFEST_PATH.read_text())
new_version = str(manifest.get("version", ""))
if new_version != RELEASE_TAG:
    print(f"::error::Version sync failed — manifest still reads '{new_version}'")
    sys.exit(1)

subprocess.run(["git", "config", "user.name", "capacium-bot[bot]"], check=True)
subprocess.run(["git", "config", "user.email", "capacium-bot[bot]@users.noreply.github.com"], check=True)
subprocess.run(["git", "add", str(MANIFEST_PATH)], check=True)
result = subprocess.run(["git", "commit", "-m", f"chore: sync version to {RELEASE_TAG} [skip ci]"])
if result.returncode == 0:
    subprocess.run(["git", "push"], check=True)
    print(f"::notice::Synced and pushed version {RELEASE_TAG}")
else:
    print("::notice::No changes to commit — version is in sync")
