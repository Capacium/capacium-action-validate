"""Tests for Capacium manifest validation."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = os.path.join(os.path.dirname(__file__), "..", "src")


def run_validate(manifest_content: str, strict: bool = False, dot_file: bool = False) -> dict:
    tmpdir = tempfile.mkdtemp()
    manifest_path = os.path.join(tmpdir, "capability.yaml")
    with open(manifest_path, "w") as f:
        f.write(manifest_content)

    if dot_file:
        open(os.path.join(tmpdir, ".DS_Store"), "w").close()

    try:
        env = os.environ.copy()
        env["MANIFEST_PATH"] = manifest_path
        if strict:
            env["STRICT_MODE"] = "true"

        result = subprocess.run(
            [sys.executable, os.path.join(SCRIPT_DIR, "validate.py")],
            env=env,
            capture_output=True,
            text=True,
        )
        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    finally:
        import shutil
        shutil.rmtree(tmpdir)


def test_valid_manifest():
    manifest = """kind: skill
name: test-skill
version: 1.0.0
description: A valid test skill
author: Test
"""
    result = run_validate(manifest)
    assert result["returncode"] == 0, f"Expected 0, got {result['returncode']}: {result['stdout']}"


def test_invalid_kind():
    manifest = """kind: invalid-kind
name: test
version: 1.0.0
"""
    result = run_validate(manifest)
    assert result["returncode"] == 1, f"Expected 1, got {result['returncode']}"


def test_missing_version():
    manifest = """kind: skill
name: test
"""
    result = run_validate(manifest)
    assert result["returncode"] == 1


def test_invalid_version():
    manifest = """kind: skill
name: test
version: not-semver
"""
    result = run_validate(manifest)
    assert result["returncode"] == 1


def test_missing_name():
    manifest = """kind: skill
version: 1.0.0
"""
    result = run_validate(manifest)
    assert result["returncode"] == 1


def test_strict_mode_dot_file():
    """Dot-files are doc-level warnings — only promoted with strict-level=docs."""
    manifest = """kind: skill
name: dot-file-test
version: 1.0.0
description: A skill with dot file
author: Test
"""
    # strict-mode=true + strict-level=schema (default): dot-file stays as warning
    result = run_validate(manifest, strict=True, dot_file=True)
    assert result["returncode"] == 0, (
        f"Doc warnings (dot-files) should NOT block in default strict mode. "
        f"Got returncode {result['returncode']}: {result['stdout']}"
    )


def test_strict_level_docs_dot_file():
    """Dot-files are promoted with strict-level=docs."""
    manifest = """kind: skill
name: dot-file-test
version: 1.0.0
description: A skill with dot file
author: Test
"""
    tmpdir = tempfile.mkdtemp()
    manifest_path = os.path.join(tmpdir, "capability.yaml")
    with open(manifest_path, "w") as f:
        f.write(manifest)
    open(os.path.join(tmpdir, ".DS_Store"), "w").close()

    try:
        env = os.environ.copy()
        env["MANIFEST_PATH"] = manifest_path
        env["STRICT_MODE"] = "true"
        env["STRICT_LEVEL"] = "docs"

        result = subprocess.run(
            [sys.executable, os.path.join(SCRIPT_DIR, "validate.py")],
            env=env,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1, (
            f"strict-level=docs should fail on dot-file. "
            f"Got returncode {result.returncode}: {result.stdout}"
        )
    finally:
        import shutil
        shutil.rmtree(tmpdir)


def test_no_dot_file_passes():
    manifest = """kind: skill
name: my-skill
version: 1.0.0
description: A valid skill
author: Test
"""
    result = run_validate(manifest, strict=False, dot_file=False)
    assert result["returncode"] == 0, f"Expected 0, got {result['returncode']}: {result['stdout']}"


def test_exchange_metadata_output():
    manifest = """kind: skill
name: test-skill-meta
version: 2.0.0
description: Metadata test
author: Capacium
"""
    tmpdir = tempfile.mkdtemp()
    manifest_path = os.path.join(tmpdir, "capability.yaml")
    with open(manifest_path, "w") as f:
        f.write(manifest)

    try:
        env = os.environ.copy()
        env["MANIFEST_PATH"] = manifest_path
        env["EXCHANGE_METADATA_OUTPUT"] = "true"

        result = subprocess.run(
            [sys.executable, os.path.join(SCRIPT_DIR, "validate.py")],
            env=env,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Expected 0, got {result.returncode}: {result.stdout}"

        meta_path = os.path.join(os.path.dirname(SCRIPT_DIR), "exchange-metadata.json")
        if os.path.exists(meta_path):
            with open(meta_path) as f:
                meta = json.load(f)
            assert meta["kind"] == "skill"
            assert meta["name"] == "test-skill-meta"
            assert meta["version"] == "2.0.0"
            assert meta["validation_status"] == "pass"
    finally:
        import shutil
        shutil.rmtree(tmpdir)


def test_framework_command_conflict():
    """Warn when command frameworks declared but only SKILL.md exists."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manifest = tmpdir + "/capability.yaml"
        import yaml
        with open(manifest, "w") as f:
            yaml.dump({
                "name": "test-skill",
                "version": "1.0.0",
                "kind": "skill",
                "frameworks": ["opencode", "opencode-command"],
            }, f)
        Path(tmpdir + "/SKILL.md").write_text("# Test Skill\n\nSkill content.")
        env = {
            **os.environ,
            "MANIFEST_PATH": manifest,
            "STRICT_MODE": "false",
            "GITHUB_OUTPUT": os.devnull,
        }
        result = subprocess.run(
            [sys.executable, os.path.join(SCRIPT_DIR, "validate.py")],
            capture_output=True, text=True, env=env, cwd=tmpdir,
        )
        stdout = result.stdout.split("::set-output")[0].strip()
        output = json.loads(stdout)
        warnings = output["findings"]["warnings"]
        assert any("opencode-command" in w and "SKILL.md" in w for w in warnings), \
            f"Expected command/SKILL.md conflict warning, got: {warnings}"


def test_cursor_mdc_legacy_warning():
    """Warn when cursor framework declared with .mdc files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manifest = tmpdir + "/capability.yaml"
        import yaml
        with open(manifest, "w") as f:
            yaml.dump({
                "name": "test-skill",
                "version": "1.0.0",
                "kind": "skill",
                "frameworks": ["cursor"],
            }, f)
        Path(tmpdir + "/rules.mdc").write_text("# Old Cursor rules")
        env = {
            **os.environ,
            "MANIFEST_PATH": manifest,
            "STRICT_MODE": "false",
            "GITHUB_OUTPUT": os.devnull,
        }
        result = subprocess.run(
            [sys.executable, os.path.join(SCRIPT_DIR, "validate.py")],
            capture_output=True, text=True, env=env, cwd=tmpdir,
        )
        stdout = result.stdout.split("::set-output")[0].strip()
        output = json.loads(stdout)
        warnings = output["findings"]["warnings"]
        assert any(".mdc" in w and "cursor" in w.lower() for w in warnings), \
            f"Expected cursor/.mdc legacy warning, got: {warnings}"


if __name__ == "__main__":
    test_valid_manifest()
    test_invalid_kind()
    test_missing_version()
    test_invalid_version()
    test_missing_name()
    test_strict_mode_dot_file()
    test_no_dot_file_passes()
    test_exchange_metadata_output()
    test_framework_command_conflict()
    test_cursor_mdc_legacy_warning()
    print("All validate tests passed!")
