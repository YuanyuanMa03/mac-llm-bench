"""Tests for scripts/sanitize_release_history.py.

All fixtures use obviously fake identifier values. No real device
identifier may ever appear in this file (repo rule).
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import sanitize_release_history as sr  # noqa: E402

FAKE_ENV = (
    b'SPHardwareDataType:\n'
    b'    "serial_number" : "[REDACTED]"\n'
    b'    "platform_UUID" : "[REDACTED]"\n'
    b'    "provisioning_UDID" : "[REDACTED]"\n'
    b'    "model_name" : "Mac mini"\n'
)

FAKE_ENV_AFTER = (
    b'SPHardwareDataType:\n'
    b'    "serial_number" : "[REDACTED]"\n'
    b'    "platform_UUID" : "[REDACTED]"\n'
    b'    "provisioning_UDID" : "[REDACTED]"\n'
    b'    "model_name" : "Mac mini"\n'
)


def test_sanitize_bytes_redacts_live_values():
    out = sr.sanitize_bytes(FAKE_ENV)
    assert out == FAKE_ENV_AFTER
    assert b"FAKE-UDID" not in out and b"FAKE-SERIAL" not in out


def test_sanitize_bytes_is_idempotent_for_already_redacted():
    once = sr.sanitize_bytes(FAKE_ENV)
    assert sr.sanitize_bytes(once) == once


def test_redacted_key_report_counts_only_live_values():
    report = sr.redacted_key_report(FAKE_ENV)
    assert report == {"serial_number": [REDACTED], "provisioning_UDID": [REDACTED]}


def test_remap_manifest_only_touches_mapped_digests():
    old_digest = hashlib.sha256(FAKE_ENV).hexdigest()
    new_digest = hashlib.sha256(FAKE_ENV_AFTER).hexdigest()
    manifest = (f"{old_digest}  environment/raw_environment.txt\n"
                "aaaa1111  command.txt\n").encode()
    out = sr._remap_manifest(manifest, {old_digest: new_digest})
    assert out == (f"{new_digest}  environment/raw_environment.txt\n"
                   "aaaa1111  command.txt\n").encode()


def _run(cmd: list[str], **kw):
    subprocess.run(cmd, check=True, capture_output=True, **kw)


@pytest.mark.skipif(shutil.which("git-filter-repo") is None,
                    reason="git-filter-repo not installed")
def test_end_to_end_synthetic_repo(tmp_path: Path):
    src = tmp_path / "src"
    src.mkdir()
    run_dir = src / "results" / "raw" / "fake-run"
    env_dir = run_dir / "environment"
    env_dir.mkdir(parents=True)
    env_file = env_dir / "raw_environment.txt"
    env_file.write_bytes(FAKE_ENV)
    cmd_file = run_dir / "command.txt"
    cmd_file.write_bytes(b"echo hi\n")
    manifest = run_dir / "manifest.sha256"
    manifest.write_text(
        f"{hashlib.sha256(cmd_file.read_bytes()).hexdigest()}"
        "  command.txt\n"
        f"{hashlib.sha256(env_file.read_bytes()).hexdigest()}"
        "  environment/raw_environment.txt\n")
    readme = src / "README.md"
    readme.write_text('mentions "provisioning_UDID" as a field name only\n')

    env_vars = {
        "GIT_AUTHOR_NAME": "T", "GIT_AUTHOR_EMAIL": "t@example.com",
        "GIT_COMMITTER_NAME": "T", "GIT_COMMITTER_EMAIL": "t@example.com",
    }
    _run(["git", "init", "-q", "-b", "master", str(src)])
    _run(["git", "-C", str(src), "add", "-A"], env=env_vars)
    _run(["git", "-C", str(src), "commit", "-qm", "fixture"], env=env_vars)

    mirror = tmp_path / "mirror.git"
    _run(["git", "clone", "-q", "--mirror", f"file://{src}", str(mirror)])

    script = Path(sr.__file__).resolve()
    map_path = tmp_path / "map.json"
    rc = subprocess.run(
        [sys.executable, str(script), "prepare",
         "--git-dir", str(mirror), "--map-out", str(map_path),
         "--source-env-file", str(env_file)],
        capture_output=True, text=True)
    assert rc.returncode == 0, rc.stdout + rc.stderr
    assert b"FAKE-UDID" not in map_path.read_bytes()  # map holds hashes only

    rc = subprocess.run(
        [sys.executable, str(script), "apply",
         "--git-dir", str(mirror), "--map", str(map_path)],
        capture_output=True, text=True)
    assert rc.returncode == 0, rc.stdout + rc.stderr

    rc = subprocess.run(
        [sys.executable, str(script), "verify",
         "--git-dir", str(mirror),
         "--source-git-dir", str(src / ".git"),
         "--source-env-file", str(env_file),
         "--map", str(map_path)],
        capture_output=True, text=True)
    assert rc.returncode == 0, rc.stdout + rc.stderr

    def mirror_blob(path: str) -> bytes:
        return subprocess.run(
            ["git", "--git-dir", str(mirror), "show", f"HEAD:{path}"],
            check=True, capture_output=True).stdout

    sanitized_env = mirror_blob("results/raw/fake-run/environment/raw_environment.txt")
    assert sanitized_env == FAKE_ENV_AFTER
    assert b"FAKE-UDID" not in sanitized_env

    new_manifest = mirror_blob("results/raw/fake-run/manifest.sha256").decode()
    assert f"{hashlib.sha256(sanitized_env).hexdigest()}" \
           "  environment/raw_environment.txt" in new_manifest
    assert f"{hashlib.sha256(cmd_file.read_bytes()).hexdigest()}" \
           "  command.txt" in new_manifest

    assert mirror_blob("README.md") == readme.read_bytes()
    assert mirror_blob("results/raw/fake-run/command.txt") == b"echo hi\n"
