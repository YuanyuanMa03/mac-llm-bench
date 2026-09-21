# Privacy sanitization

Historical environment captures in the public artifact are sanitized with a deterministic, value-only transformation. Non-placeholder persistent device identifiers are replaced by `[REDACTED]`; personal home prefixes by `<home>`; and custom volume prefixes by `<volume>`. Identifier keys, safe system paths, experiment identifiers, timestamps, model revisions, configurations, terminal states, and benchmark measurements are preserved.

The maintainer retains an independently verified private bundle and checkout containing the original captures. Public sanitized files are therefore not represented as byte-identical originals. `release_sanitization_manifest.jsonl` records each changed path, the private-original SHA-256, the public-sanitized SHA-256, and the sanitization class without recording removed values.

Existing per-run manifests retain their original experiment-time digests. The reproducibility audit accepts a digest difference only when the original digest and current public digest match the explicit release mapping. The six historical D6 manifest warnings remain original integrity warnings and are reported separately from privacy sanitization.
