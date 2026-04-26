"""Tests for Capacium manifest validation."""
import json
import os
import subprocess
import sys
import tempfile

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
    manifest = """kind: skill
name: dot-file-test
version: 1.0.0
description: A skill with dot file
author: Test
"""
    result = run_validate(manifest, strict=True, dot_file=True)
    assert result["returncode"] == 1, "Strict mode should fail on dot-file warning"


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


if __name__ == "__main__":
    test_valid_manifest()
    test_invalid_kind()
    test_missing_version()
    test_invalid_version()
    test_missing_name()
    test_strict_mode_dot_file()
    test_no_dot_file_passes()
    test_exchange_metadata_output()
    print("All validate tests passed!")
