"""capability.yaml manifest validator for Capacium Validate Action.

Strict mode levels:
  strict-mode: "false"  → No warnings promoted (default)
  strict-mode: "true"   → Only schema-level warnings promoted (kind, deps, runtimes, frameworks)
  strict-level: "docs"  → Additionally promote doc-file warnings (prompt.md, README)
  
Doc-convention checks (prompt.md, README) are NEVER errors in default strict mode.
They are only promoted when STRICT_LEVEL=docs is explicitly set.
"""

import hashlib
import json
import os
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print(json.dumps({
        "valid": False,
        "findings": {
            "errors": ["PyYAML is required. Run: pip install pyyaml"],
            "warnings": [],
        },
    }, indent=2))
    print("::set-output name=valid::false")
    print("::set-output name=findings-count::1")
    print("::set-output name=error-count::1")
    print("::set-output name=warning-count::0")
    sys.exit(1)


VALID_KINDS = {
    "skill", "bundle", "tool", "prompt",
    "template", "workflow", "mcp-server", "connector-pack",
}

# Warnings in this set are schema-level: promoted to errors in strict-mode=true
_SCHEMA_WARNING_KEYS = {
    "dependencies", "runtimes", "frameworks",
}

# Warnings in this set are doc-level: only promoted in strict-level=docs
_DOCS_WARNING_KEYS = {
    "prompt.md", "readme", "dot-files",
}


def load_manifest(path: str) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def validate_manifest(manifest: dict) -> dict:
    findings = {"errors": [], "warnings": []}

    if not isinstance(manifest, dict):
        findings["errors"].append("Manifest must be a YAML mapping (dictionary)")
        return findings

    if "kind" not in manifest:
        findings["errors"].append("Missing required field: 'kind'")
    elif manifest["kind"] not in VALID_KINDS:
        findings["errors"].append(
            f"Invalid kind '{manifest['kind']}'. "
            f"Must be one of: {', '.join(sorted(VALID_KINDS))}"
        )

    if "version" not in manifest:
        findings["errors"].append("Missing required field: 'version'")
    else:
        version = str(manifest["version"])
        parts = version.split(".")
        if len(parts) != 3 or not all(p.isdigit() for p in parts):
            findings["errors"].append(
                f"Invalid version '{version}'. Must be valid semver (MAJOR.MINOR.PATCH)"
            )

    if "name" not in manifest:
        findings["errors"].append("Missing required field: 'name'")

    if "dependencies" in manifest:
        deps = manifest["dependencies"]
        if isinstance(deps, dict):
            for dep_name, dep_version in deps.items():
                if not isinstance(dep_version, str):
                    findings["warnings"].append(
                        f"Dependency '{dep_name}' has non-string version constraint"
                    )
        else:
            findings["warnings"].append("'dependencies' must be a mapping (name -> version)")

    if "runtimes" in manifest:
        runtimes = manifest["runtimes"]
        if isinstance(runtimes, dict):
            for runtime_name, runtime_version in runtimes.items():
                if not isinstance(runtime_version, str):
                    findings["warnings"].append(
                        f"Runtime '{runtime_name}' has non-string version constraint"
                    )
        else:
            findings["warnings"].append("'runtimes' must be a mapping (name -> version)")

    if "frameworks" in manifest:
        frameworks = manifest["frameworks"]
        if not isinstance(frameworks, list):
            findings["warnings"].append("'frameworks' should be a list")

    return findings


def lint_package(manifest_path: Path) -> dict:
    findings = {"errors": [], "warnings": []}
    pkg_dir = manifest_path.parent

    # prompt.md: NEVER a hard error — always a recommendation
    prompt_path = pkg_dir / "prompt.md"
    if not prompt_path.exists():
        findings["warnings"].append("Recommended file not found: prompt.md")

    readme_files = list(pkg_dir.glob("README*"))
    if not readme_files:
        findings["warnings"].append("No README file found in package")

    dot_files = [f.name for f in pkg_dir.iterdir() if f.name.startswith(".") and f.is_file()]
    for df in dot_files:
        if df not in (".gitignore", ".env.example"):
            findings["warnings"].append(f"Potentially unnecessary dot-file: {df}")

    yaml_files = list(pkg_dir.glob("*.yaml")) + list(pkg_dir.glob("*.yml"))
    manifests = [f for f in yaml_files if f.name.endswith(("capability.yaml", "capability.yml"))]
    if not manifests:
        findings["errors"].append("No capability manifest file found (*.yaml or *.yml)")

    # Framework compatibility hints
    manifest = load_manifest(str(manifest_path)) if manifest_path.exists() else {}
    frameworks = manifest.get("frameworks", [])
    if isinstance(frameworks, list):
        has_cmd = "opencode-command" in frameworks or "claude-code-command" in frameworks
        has_skill = any(f in frameworks for f in ("opencode", "claude-code", "gemini-cli", "cursor"))
        skill_md = (pkg_dir / "SKILL.md")
        if has_cmd and skill_md.exists() and any(f.endswith(".md") for f in os.listdir(pkg_dir) if f == "SKILL.md"):
            findings["warnings"].append(
                "Framework conflict: 'opencode-command' or 'claude-code-command' declared but only SKILL.md found. "
                "Command adapters create command symlinks that can't parse SKILL.md YAML frontmatter. "
                "Provide a separate .md file for commands or remove command frameworks."
            )
        # Cursor: .mdc is legacy, should use .cursor/skills/
        if "cursor" in frameworks:
            mdc_files = list(pkg_dir.glob("*.mdc"))
            if mdc_files:
                findings["warnings"].append(
                    "Cursor legacy format: .mdc files found. Cursor now expects SKILL.md in .cursor/skills/. "
                    "Convert .mdc files to SKILL.md format."
                )

    return findings


def _warning_is_schema(msg: str) -> bool:
    """Heuristic: classify a warning string as schema-level or doc-level."""
    schema_triggers = ("dependency", "dependencies", "runtime", "runtimes", "framework")
    return any(msg.lower().startswith(t) or "'" + t in msg.lower() for t in schema_triggers)


def _promote_warnings(
    manifest_warnings: list,
    lint_warnings: list,
    strict_mode: bool,
    strict_level: str,
) -> tuple:
    """Determine which warnings to promote to errors based on strict config."""
    errors_from_warnings = []

    if strict_mode:
        # Schema-level warnings → errors
        for w in manifest_warnings:
            errors_from_warnings.append(f"[strict] {w}")
        manifest_warnings_kept = []
    else:
        manifest_warnings_kept = manifest_warnings

    if strict_level == "docs":
        for w in lint_warnings:
            errors_from_warnings.append(f"[strict] {w}")
        lint_warnings_kept = []
    else:
        lint_warnings_kept = lint_warnings

    return manifest_warnings_kept, lint_warnings_kept, errors_from_warnings


def resolve_manifest_path(input_path: str, action_dir: Path) -> Path:
    p = Path(input_path)
    if p.is_absolute():
        return p
    return action_dir / p


def compute_fingerprint(path: Path) -> str:
    sha = hashlib.sha256()
    if path.is_file():
        sha.update(path.read_bytes())
    return sha.hexdigest()


def generate_exchange_metadata(manifest: dict, findings: dict) -> dict:
    metadata = {
        "kind": manifest.get("kind", "unknown"),
        "name": manifest.get("name", "unknown"),
        "version": manifest.get("version", "0.0.0"),
        "description": manifest.get("description", ""),
        "author": manifest.get("author", ""),
        "tags": manifest.get("tags", []),
        "fingerprint": None,
        "validation_status": "pass" if not findings.get("errors") else "fail",
        "error_count": len(findings.get("errors", [])),
        "warning_count": len(findings.get("warnings", [])),
    }
    return metadata


def set_output(name: str, value: str):
    output_path = os.environ.get("GITHUB_OUTPUT")
    if output_path:
        with open(output_path, "a") as f:
            print(f"{name}={value}", file=f)
    else:
        print(f"::set-output name={name}::{value}")


def main():
    manifest_path = os.environ.get("MANIFEST_PATH", "capability.yaml")
    strict_mode = os.environ.get("STRICT_MODE", "false").lower() == "true"
    strict_level = os.environ.get("STRICT_LEVEL", "schema").lower()
    exchange_output = os.environ.get("EXCHANGE_METADATA_OUTPUT", "false").lower() == "true"

    action_dir = Path(__file__).resolve().parent.parent
    full_path = resolve_manifest_path(manifest_path, action_dir)

    if not full_path.exists():
        result = {
            "valid": False,
            "findings": {"errors": [f"Manifest not found at {full_path}"], "warnings": []},
        }
        print(json.dumps(result, indent=2))
        set_output("valid", "false")
        set_output("findings-count", "1")
        set_output("error-count", "1")
        set_output("warning-count", "0")
        sys.exit(1)

    manifest = load_manifest(str(full_path))
    findings = validate_manifest(manifest)
    lint_findings = lint_package(full_path)
    findings_errors = findings.get("errors", [])
    findings_warnings = findings.get("warnings", [])
    lint_errors = lint_findings.get("errors", [])
    lint_warnings = lint_findings.get("warnings", [])

    # Promote warnings based on strict configuration:
    #   strict-mode=true + strict-level=schema (default):
    #     Only schema warnings (deps, runtimes, frameworks) → errors
    #     Doc warnings (prompt.md, README) stay as warnings
    #   strict-mode=true + strict-level=docs:
    #     Schema warnings + doc warnings → errors
    #   strict-mode=false:
    #     All warnings stay as warnings
    mw_kept, lw_kept, promoted = _promote_warnings(
        findings_warnings, lint_warnings, strict_mode, strict_level,
    )

    all_errors = findings_errors + lint_errors + promoted
    all_warnings = mw_kept + lw_kept
    is_valid = len(all_errors) == 0

    result = {
        "valid": is_valid,
        "manifest_path": str(full_path),
        "findings": {
            "errors": all_errors,
            "warnings": all_warnings,
        },
    }
    print(json.dumps(result, indent=2))

    set_output("valid", str(is_valid).lower())
    set_output("findings-count", str(len(all_errors) + len(all_warnings)))
    set_output("error-count", str(len(all_errors)))
    set_output("warning-count", str(len(all_warnings)))

    if exchange_output:
        fingerprint = compute_fingerprint(full_path)
        metadata = generate_exchange_metadata(manifest, findings)
        metadata["fingerprint"] = fingerprint
        metadata["lint_errors"] = len(lint_findings.get("errors", []))
        metadata["lint_warnings"] = len(lint_findings.get("warnings", []))
        metadata_path = Path("exchange-metadata.json")
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
        print(f"Exchange metadata written to {metadata_path.resolve()}")

    if not is_valid:
        sys.exit(1)


if __name__ == "__main__":
    main()
