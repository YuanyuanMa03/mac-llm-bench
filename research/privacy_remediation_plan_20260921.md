# Privacy remediation plan — 2026-09-21

## Confirmed exposure, without reproducing values

A key-only scan found the persistent-device field `provisioning_UDID` in all
118 historical `results/raw/**/environment/raw_environment.txt` captures, and
a value-aware scan (2026-09-21) extended the scope to 19 further captures
under `results/validation/**` (16 validation runs plus 3 supervisor-v0 runs)
— 137 files in total. No non-environment file in the working tree contains
the value. The current source collector did not redact that key. Git-history
search found the key in 100 commits. No identifier value was copied into this
report, tests, commit messages, or terminal output.

This is a privacy incident, not a scientific-result correction. The research
numbers and logs must not be silently edited in place.

## Immediate owner actions

1. Temporarily make the public repository private or otherwise restrict access.
2. Preserve an encrypted, access-controlled archive of the original repository
   and record its repository-bundle SHA-256 outside Git.
3. Revoke/rotate any platform or provisioning identity for which Apple provides
   an applicable rotation path. The maintainer should determine this with the
   account owner; the value must not be pasted into an issue.
4. Decide between a sanitized-history replacement and a new sanitized public
   repository. A new public repository is operationally safer because it does
   not imply that existing clones have been remediated.
5. Notify downstream clone/fork owners that old objects contain a persistent
   device identifier and must be deleted or re-sanitized.

## Required sanitization contract

For every affected file in a public sanitized release:

- replace only sensitive field values with `[REDACTED]`;
- retain the original only in the private archive;
- produce a machine-readable `release_sanitization_manifest.jsonl` outside the
  raw experiment directories with `path`, `original_sha256`,
  `sanitized_sha256`, and `redacted_field_names`;
- never include original sensitive values in the manifest;
- state explicitly that sanitized files are not byte-identical immutable raw;
- regenerate repository integrity manifests for the public sanitized copy, but
  retain the private original manifests for audit.

## Staged commands for the maintainer

The following commands are a plan, not commands executed by this correction.
They deliberately stop before any remote mutation.

```bash
# 1. Restrict access in the hosting UI/API first.

# 2. Create and verify a private archive outside the public checkout.
git bundle create /PRIVATE/ARCHIVE/mac-llm-bench-pre-sanitization.bundle --all
git bundle verify /PRIVATE/ARCHIVE/mac-llm-bench-pre-sanitization.bundle
shasum -a 256 /PRIVATE/ARCHIVE/mac-llm-bench-pre-sanitization.bundle

# 3. Work in a disposable mirror; do not touch the research checkout.
git clone --mirror <PRIVATE-REPOSITORY-URL> /PRIVATE/WORK/mac-llm-bench-sanitize.git

# 4. Run a reviewed JSON-aware sanitizer over every historical
#    raw_environment.txt blob and write the sanitization manifest. The sanitizer
#    must match field names, never a copied real value.

# 5. Scan the rewritten object database before any publication.
git -C /PRIVATE/WORK/mac-llm-bench-sanitize.git fsck --full
git -C /PRIVATE/WORK/mac-llm-bench-sanitize.git log --all -S'provisioning_UDID' --oneline
git -C /PRIVATE/WORK/mac-llm-bench-sanitize.git log --all -S'crashReporterKey' --oneline

# 6. Review the replacement refs and manifest. Stop for explicit approval.
git -C /PRIVATE/WORK/mac-llm-bench-sanitize.git show-ref

# Intentionally omitted: git push --force / force-with-lease.
```

## Verification gates before re-publication

- Key/value-aware privacy scan returns no unredacted persistent identifiers in
  the working tree, every reachable commit, tag, release asset, or repository
  bundle intended for publication.
- The sanitization manifest contains hashes and field names only.
- A separate scientific integrity check confirms that non-environment research
  values and experiment classifications are unchanged.
- Public documentation explains that raw environment captures were sanitized
  for privacy while numeric benchmark evidence was preserved.
- The maintainer explicitly approves the final remote replacement. This task
  does not authorize a push, force-push, release, or tag.

