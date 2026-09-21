# Privacy remediation execution — 2026-09-21 (prompt19)

Executes the staged plan in
[privacy_remediation_plan_20260921.md](privacy_remediation_plan_20260921.md)
up to — deliberately not including — any remote mutation. Nothing was
pushed, force-pushed, tagged, or released by this run.

## Steps executed

| Plan step | Outcome |
|---|---|
| 1. Restrict access | Repository `YuanyuanMa03/mac-llm-bench` verified **already PRIVATE** via `gh repo view` (2026-09-21); `forkCount=0`, so there are no GitHub forks to notify. No visibility change was needed. |
| 2. Private archive | `~/mac-llm-bench-private/archive/` (mode 700, outside any git repo): `mac-llm-bench-pre-sanitization.bundle` (16 MiB, `git bundle verify`: complete history) and `mac-llm-bench-gitdir-pre-sanitization.tar.gz` (19 MiB, full `.git` incl. local-only refs). SHA-256 of both recorded in `archive/SHA256SUMS.txt` (outside git). |
| 3. Sanitizer | `scripts/sanitize_release_history.py` (this repository): field-aware and path-aware. Blobs are rewritten **only** if they appear at `**/environment/raw_environment.txt` (identifier field values → `[REDACTED]`) or `**/manifest.sha256` (digest lines referencing sanitized captures remapped). The real identifier value is read in memory for scans only and never written to disk; the sanitize map contains hashes only. |
| 4. Rewrite | Mirror clone `~/mac-llm-bench-private/work/mac-llm-bench-sanitize.git` (local-only refs `refs/codex/*`, `refs/remotes/*` pruned; master/paperwriting/`v1.0.0-rc1` retained) rewritten with `git filter-repo --blob-callback`. |
| 5. Verification | Battery below, all passed. |
| 6. Stop | No push / force-push / release / tag. Owner decision required for the remote replacement (see below). |

## Rewrite statistics

- 137 environment blobs (118 `results/raw` + 19 `results/validation`), each
  with exactly one live `provisioning_UDID` value redacted
  (`serial_number`/`platform_UUID` were already `[REDACTED]` historically).
- 137 `manifest.sha256` digest lines remapped to sanitized content digests.
- 117 commit pairs rewritten across 3 refs; all other blobs byte-identical.
- Pre-rewrite guard confirmed the identifier value appears in **no** other
  blob and in no commit or tag message, so no message rewriting was needed.

## Verification battery (verbatim outcomes)

```
$ uv run python -m pytest tests/test_sanitize_release_history.py -q
  5 passed          # synthetic fixtures only; fake identifiers only

$ scripts/sanitize_release_history.py prepare   (real mirror)
  [prepare] env blobs=137 manifest blobs=138
  [prepare] manifest digest lines to remap=137
  [prepare] map -> ~/mac-llm-bench-private/work/sanitize_map.json

$ scripts/sanitize_release_history.py apply
  [apply] git filter-repo completed

$ scripts/sanitize_release_history.py verify
  [verify] fsck --full ok
  [verify] value scan over 2124 sanitized blobs done (failures so far: 0)
  [verify] commit counts compared across 3 refs
  [verify] 117 commit pairs checked for tree equivalence
  [verify] all checks passed

$ per-run manifest consistency in the sanitized tip
  [manifest-consistency] verified=131 stale=6
  # 131 = 112 results/raw + 19 results/validation; the 6 stale runs are
  # exactly the pre-existing declared D6 digest/finalization warnings,
  # preserved as history (not silently "fixed").
```

Tree-equivalence check (every commit pair): path sets identical; every blob
outside environment captures and per-run manifests byte-identical — this is
the scientific-integrity gate confirming that non-environment research
values and classifications are unchanged.

## Deliverables for review

| Artifact | Location |
|---|---|
| Sanitized mirror (all history rewritten) | `~/mac-llm-bench-private/work/mac-llm-bench-sanitize.git` |
| Sanitized checkout, branch `paperwriting` | `~/mac-llm-bench-private/work/mac-llm-bench-sanitized-checkout` |
| Machine-readable sanitization manifest (137 entries; hashes + field names; no identifier values) | `release_sanitization_manifest.jsonl` at the sanitized repo root (commit `66cc563`, with post-sanitization README privacy notes, en+zh) |
| Sanitize map (blob/digest hashes only) | `~/mac-llm-bench-private/work/sanitize_map.json` |
| Pre-sanitization private archive | `~/mac-llm-bench-private/archive/` (bundle + full .git tarball + SHA256SUMS) |
| Sanitizer + regression tests | `scripts/sanitize_release_history.py`, `tests/test_sanitize_release_history.py` |

The research checkout is untouched: `results/raw/**` still carries the
original values by design (it is the private source of truth, archived
above); the sanitized public copy is a separate lineage.

## Remaining owner decisions (blocking re-publication)

1. Choose the replacement strategy: force-push the sanitized history to the
   existing private repository, or create a new public repository from the
   sanitized mirror (operationally safer; existing clones of the old history
   remain unremediated either way).
2. If any platform provides a rotation path for the provisioning identity,
   rotate it; keep the value out of issues and commit messages.
3. After re-publication: fix the paper revision (S42 — `arxiv-v1` tag/branch)
   and publish the arXiv link; update the README hold note status.
4. Notify known clone owners if any are identified.

## Invariants held

- No file under `results/raw/**` in the research checkout was modified.
- `research/preregistration.md` untouched; deviation history untouched.
- No benchmark was launched; no identifier value was printed, logged, or
  committed in this run (scans report counts and hashes only).
- No remote mutation of any kind.

## Addendum — repository recreation (2026-09-21, prompt20)

The owner selected the "new repository" strategy ("删除，重建仓库") and this
was executed as prompt20:

1. Pre-recreation archive refreshed at the current HEAD:
   `mac-llm-bench-pre-recreation.bundle` (verified complete history) and
   `mac-llm-bench-gitdir-pre-recreation.tar.gz`, SHA-256 appended to
   `archive/SHA256SUMS.txt` (pre-sanitization entries retained).
2. prompt19 outputs (sanitizer, tests, this report, ledger rows) were ported
   onto the sanitized lineage — the three new files are byte-identical to the
   research-repo versions; commit `1347203` in the public lineage.
3. Old repository `YuanyuanMa03/mac-llm-bench` deleted (`gh repo delete`,
   after confirming the remote held nothing absent from local history:
   only `master` @ `aef0276` and tag `v1.0.0-rc1`).
4. New repository created **public** at the same name and URL, no
   description/topics (none previously). Pushed from the sanitized checkout:
   branch `master` (= sanitized `paperwriting` tip `1347203`; local `master`
   is an ancestor, so full history is retained) and tag `v1.0.0-rc1`
   (sanitized rewrite).
5. End-to-end verification via a fresh clone of the public URL:
   - working-tree files containing the real identifier value: **0**;
   - every blob in the public history (2133 blobs): **0**;
   - all 118 `results/raw` captures show `"provisioning_UDID": "[REDACTED]"`;
   - `release_sanitization_manifest.jsonl` present with 137 entries;
     sanitizer script and tests present.

### New push workflow (important)

- The public repository must only ever be pushed from
  `~/mac-llm-bench-private/work/mac-llm-bench-sanitized-checkout`
  (sanitized lineage; its `origin` is the public URL).
- The research checkout's remote was renamed to
  `unsanitized-private-do-not-push` to prevent accidental publication of the
  unsanitized lineage. Publishing future changes requires porting diffs onto
  the sanitized lineage, as done for the prompt19 outputs.

