#!/usr/bin/env python3
"""Field-aware history sanitizer for the sanitized public release.

Executed against a disposable *mirror clone* of this repository, never against
the research checkout. It rewrites exactly two families of blobs:

1. ``**/environment/raw_environment.txt`` — the values of persistent-device
   identifier fields are replaced with ``[REDACTED]``.
2. ``**/manifest.sha256`` — the per-run integrity manifests: digest lines
   that reference a sanitized environment capture are remapped to the
   sanitized content digest, so the public copy's manifests stay truthful.

Design constraints (see research/privacy_remediation_plan_20260921.md):

* matches field names and digests, never a copied real identifier value;
* the real value (needed only for verification scans) is read in memory from
  a source environment capture supplied by the caller and never written to
  disk by this script;
* path selection uses the object database (a blob is sanitized only if it
  appears at a matching path), so source files and test fixtures that merely
  mention the field names are never touched;
* the research checkout, results/raw, and git history of this repository are
  not modified by this script.

Subcommands
-----------
prepare   walk the mirror, build the sanitize map (blob sets + digest map)
apply     run git-filter-repo with a thin blob callback driven by the map
verify    post-rewrite verification battery against the original repository
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

SENSITIVE_KEYS = (
    "provisioning_UDID",
    "serial_number",
    "serial_number_system",
    "platform_UUID",
    "crashReporterKey",
)

# Matches the "key" : "value" pairs exactly as the environment collector
# emits them; the quoted value is replaced with "[REDACTED]".
VALUE_RE_SRC = r'("(?:' + "|".join(SENSITIVE_KEYS) + r')"\s*:\s*)"[^"]*"'
VALUE_RE = re.compile(VALUE_RE_SRC.encode())
REDACTED = b'"[REDACTED]"'
REDACTED_VALUE = b"[REDACTED]"

ENV_PATH_SUFFIX = "environment/raw_environment.txt"
MANIFEST_PATH_SUFFIX = "manifest.sha256"

# Thin callback executed by git-filter-repo inside the mirror. All state
# comes from the JSON map referenced by $SANITIZE_MAP_JSON (hashes only).
CALLBACK = r'''
import json as _json, os as _os, re as _re
_m = _json.load(open(_os.environ["SANITIZE_MAP_JSON"]))
_env = set(x.encode() for x in _m["env_blob_shas"])
_man = set(x.encode() for x in _m["manifest_blob_shas"])
_dmap = {k.encode(): v.encode() for k, v in _m["digest_map"].items()}
_vre = _re.compile(_m["value_re"].encode())
_d = blob.data
_oi = blob.original_id
if _oi is not None and _oi in _env:
    blob.data = _vre.sub(rb'\1"[REDACTED]"', _d)
elif _oi is not None and _oi in _man:
    _out = []
    for _line in _d.split(b"\n"):
        _parts = _line.split(None, 1)
        if _parts and _parts[0] in _dmap:
            _line = _line.replace(_parts[0], _dmap[_parts[0]], 1)
        _out.append(_line)
    blob.data = b"\n".join(_out)
'''


def _git(git_dir: str, *args: str, binary: bool = False):
    run = subprocess.run(
        ["git", "--git-dir", git_dir, *args],
        capture_output=True,
        check=True,
    )
    return run.stdout if binary else run.stdout.decode()


def sanitize_bytes(data: bytes) -> bytes:
    return VALUE_RE.sub(rb'\1"[REDACTED]"', data)


def _match_value(match: re.Match) -> bytes:
    return match.group(0).rsplit(b'"', 2)[-2]


def redacted_key_report(data: bytes) -> dict[str, int]:
    """Count live (not already redacted) values per key, for manifests."""
    report: dict[str, int] = {}
    for m in VALUE_RE.finditer(data):
        key = m.group(1).decode().split('"')[1]
        if _match_value(m) != REDACTED_VALUE:
            report[key] = report.get(key, 0) + 1
    return report


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_live_value(source_env_file: Path) -> bytes:
    """Extract the live provisioning_UDID value in memory (never printed)."""
    m = re.search(
        rb'"provisioning_UDID"\s*:\s*"([^"]+)"', source_env_file.read_bytes()
    )
    if not m or m.group(1) == REDACTED_VALUE:
        raise SystemExit("could not extract a live provisioning_UDID value")
    return m.group(1)


def _object_pairs(git_dir: str) -> list[tuple[str, str]]:
    pairs = []
    for line in _git(git_dir, "rev-list", "--objects", "--all").splitlines():
        parts = line.split(" ", 1)
        pairs.append((parts[0], parts[1] if len(parts) > 1 else ""))
    return pairs


def _blob_shas(git_dir: str) -> set[str]:
    """Reachable objects of type blob (rev-list output includes trees)."""
    shas = sorted({sha for sha, _ in _object_pairs(git_dir)})
    run = subprocess.run(
        ["git", "--git-dir", git_dir, "cat-file", "--batch-check"],
        input="\n".join(shas) + "\n", capture_output=True, check=True, text=True,
    )
    out = set()
    for line in run.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "blob":
            out.add(parts[0])
    return out


def _tree_entries(git_dir: str, rev: str) -> dict[str, str]:
    """path -> blob sha for every blob in the commit tree."""
    entries = {}
    for line in _git(git_dir, "ls-tree", "-r", rev).splitlines():
        meta, path = line.split("\t", 1)
        _mode, otype, sha = meta.split()
        if otype == "blob":
            entries[path] = sha
    return entries


def _remap_manifest(data: bytes, digest_map: dict[str, str]) -> bytes:
    out = []
    for line in data.split(b"\n"):
        parts = line.split(None, 1)
        if parts and parts[0].decode() in digest_map:
            line = line.replace(parts[0], digest_map[parts[0].decode()].encode(), 1)
        out.append(line)
    return b"\n".join(out)


def cmd_prepare(args: argparse.Namespace) -> int:
    git_dir = args.git_dir
    value = load_live_value(Path(args.source_env_file))
    pairs = _object_pairs(git_dir)
    blobs = _blob_shas(git_dir)

    env_shas = {sha for sha, path in pairs
                if path.endswith(ENV_PATH_SUFFIX) and sha in blobs}
    man_shas = {sha for sha, path in pairs
                if path.endswith(MANIFEST_PATH_SUFFIX) and sha in blobs}
    print(f"[prepare] env blobs={len(env_shas)} manifest blobs={len(man_shas)}")

    # Abort if the real value appears outside environment captures
    # (blobs or commit/tag messages) — that would need manual handling.
    stray = []
    for sha in sorted(blobs):
        if sha not in env_shas and value in _git(
                git_dir, "cat-file", "blob", sha, binary=True):
            stray.append(("blob", sha))
    if value.decode(errors="ignore") in _git(
            git_dir, "log", "--all", "--format=%B"):
        stray.append(("commit-message", "<some commit>"))
    for line in _git(git_dir, "for-each-ref", "refs/tags",
                     "--format=%(contents)").splitlines():
        if value.decode(errors="ignore") in line:
            stray.append(("tag", "<some tag>"))
    if stray:
        for kind, ref in stray:
            print(f"[prepare] ABORT: real value found in {kind} {ref}")
        return 1

    digest_map: dict[str, str] = {}
    env_info: dict[str, dict] = {}
    for sha in sorted(env_shas):
        data = _git(git_dir, "cat-file", "blob", sha, binary=True)
        new = sanitize_bytes(data)
        digest_map[sha256_bytes(data)] = sha256_bytes(new)
        env_info[sha] = {
            "redacted_fields": redacted_key_report(data),
            "bytes_before": len(data),
            "bytes_after": len(new),
            "lines_preserved": data.count(b"\n") == new.count(b"\n"),
        }
        if any(_match_value(m) != REDACTED_VALUE for m in VALUE_RE.finditer(new)):
            print(f"[prepare] ABORT: pattern left unredacted in blob {sha}")
            return 1

    man_rewrites = sum(
        1 for sha in man_shas
        for line in _git(git_dir, "cat-file", "blob", sha, binary=True).split(b"\n")
        if line.split(None, 1) and line.split(None, 1)[0].decode() in digest_map
    )
    print(f"[prepare] manifest digest lines to remap={man_rewrites}")

    Path(args.map_out).write_text(json.dumps({
        "env_blob_shas": sorted(env_shas),
        "manifest_blob_shas": sorted(man_shas),
        "digest_map": digest_map,
        "env_info": env_info,
        "value_re": VALUE_RE_SRC,
    }, indent=1), encoding="utf-8")
    print(f"[prepare] map -> {args.map_out}")
    return 0


def cmd_apply(args: argparse.Namespace) -> int:
    map_path = str(Path(args.map).resolve())
    env = dict(os.environ, SANITIZE_MAP_JSON=map_path)
    run = subprocess.run(
        ["git", "--git-dir", args.git_dir, "filter-repo",
         "--force", "--blob-callback", CALLBACK],
        env=env, capture_output=True, text=True,
    )
    if run.returncode != 0:
        print(run.stdout)
        print(run.stderr, file=sys.stderr)
        return run.returncode
    print("[apply] git filter-repo completed")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    src, dst = args.source_git_dir, args.git_dir
    value = load_live_value(Path(args.source_env_file))
    failures: list[str] = []

    # 1. fsck on the sanitized mirror.
    _git(dst, "fsck", "--full")
    print("[verify] fsck --full ok")

    # 2. Real value must be absent from every object of the sanitized repo.
    dst_blobs = _blob_shas(dst)
    for sha in sorted(dst_blobs):
        if value in _git(dst, "cat-file", "blob", sha, binary=True):
            failures.append(f"value still present in blob {sha}")
    print(f"[verify] value scan over {len(dst_blobs)} sanitized blobs done "
          f"(failures so far: {len(failures)})")

    # 3. Every head/tag of the source survives with an equal commit count.
    refnames = sorted(line.split()[1] for line in _git(
        src, "for-each-ref", "refs/heads", "refs/tags",
        "--format=%(objectname) %(refname)").splitlines())
    for ref in refnames:
        n_src = int(_git(src, "rev-list", "--count", ref))
        n_dst = int(_git(dst, "rev-list", "--count", ref))
        if n_src != n_dst:
            failures.append(f"{ref}: commit count {n_src} -> {n_dst}")
    print(f"[verify] commit counts compared across {len(refnames)} refs")

    # 4. Pairwise tree equivalence via ls-tree (works across two repos):
    #    identical paths everywhere; identical blobs everywhere except env
    #    captures and per-run manifests, which must equal the deterministic
    #    transform of the originals.
    mapping = {}
    cm = Path(dst, "filter-repo", "commit-map")
    if not cm.exists():
        print("[verify] FAIL: filter-repo commit-map missing")
        return 1
    for line in cm.read_text().splitlines():
        old, new = line.split()
        mapping[old] = new

    digest_map = json.loads(Path(args.map).read_text())["digest_map"]
    n_pairs = 0
    for old in _git(src, "rev-list", "--all").splitlines():
        new = mapping.get(old)
        if new is None:
            failures.append(f"no sanitized counterpart for commit {old}")
            continue
        n_pairs += 1
        old_tree = _tree_entries(src, old)
        new_tree = _tree_entries(dst, new)
        if set(old_tree) != set(new_tree):
            failures.append(f"commit {old}: path set changed")
            continue
        for path, old_sha in old_tree.items():
            new_sha = new_tree[path]
            if old_sha == new_sha:
                continue
            if path.endswith(ENV_PATH_SUFFIX):
                expected = sanitize_bytes(_git(src, "cat-file", "blob",
                                               old_sha, binary=True))
                actual = _git(dst, "cat-file", "blob", new_sha, binary=True)
                if actual != expected:
                    failures.append(f"commit {old}: env blob differs from "
                                    f"deterministic transform at {path}")
            elif path.endswith(MANIFEST_PATH_SUFFIX):
                expected = _remap_manifest(
                    _git(src, "cat-file", "blob", old_sha, binary=True),
                    digest_map)
                actual = _git(dst, "cat-file", "blob", new_sha, binary=True)
                if actual != expected:
                    failures.append(f"commit {old}: manifest differs from "
                                    f"digest remap at {path}")
            else:
                failures.append(f"commit {old}: unexpected change at {path}")
    print(f"[verify] {n_pairs} commit pairs checked for tree equivalence")

    if failures:
        for f in failures[:20]:
            print(f"[verify] FAIL: {f}")
        return 1
    print("[verify] all checks passed")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("prepare")
    p.add_argument("--git-dir", required=True,
                   help="mirror .git dir to analyze")
    p.add_argument("--source-env-file", required=True,
                   help="one raw_environment.txt in the research checkout "
                        "carrying the live value (read in memory only)")
    p.add_argument("--map-out", required=True)
    p.set_defaults(func=cmd_prepare)

    p = sub.add_parser("apply")
    p.add_argument("--git-dir", required=True)
    p.add_argument("--map", required=True)
    p.set_defaults(func=cmd_apply)

    p = sub.add_parser("verify")
    p.add_argument("--git-dir", required=True)
    p.add_argument("--source-git-dir", required=True,
                   help="original repository .git for pairwise comparison")
    p.add_argument("--source-env-file", required=True)
    p.add_argument("--map", required=True,
                   help="sanitize map produced by prepare (digest map)")
    p.set_defaults(func=cmd_verify)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
