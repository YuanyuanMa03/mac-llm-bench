# Evidence directory

This directory pins forensic evidence backing claims in the paper and in
`research/deviations.md` (D7 erratum) and `research/release_audit.md`.

**`JetsamEvent-2026-09-16-004948.ips`** — the kernel Jetsam event proving the
b8 third SIGKILL was memory exhaustion (bug_type 298). The raw `.ips` file
is deliberately **not committed**: it embeds a device-scoped
`crashReporterKey` and the full per-process list of the host machine
(third-party app names included), which is not appropriate to publish.

The retained, publishable facts extracted from it (python3.13 resident
23.5 GiB / peak 29.7 GiB, compressor 12.5 GiB, free page floor 59 MiB,
24 processes in vm-compressor-space-shortage, bug_type 298, timestamp
2026-09-16 00:49:48 +0800) are recorded verbatim in:

- `research/deviations.md` — D7 erratum note (Chinese working log)
- `research/release_audit.md` — R6 forensic section
- paper §Boundary Behavior (Table 4 cites the Jetsam event)

The original file's SHA-256:

```
2ea68278e2763953d284bc11bdb965de30a0284d11bfa4f6111ae6a536564712  JetsamEvent-2026-09-16-004948.ips
```

The file itself stays on the operator's machine and can be re-shared
privately with reviewers on request.
