# Experiment governance: the boundary-control design

This artifact was produced by a single researcher working with AI coding
assistants. That combination is efficient but risky: assistants can
plausibly "complete" tasks that were never verified, quietly rewrite
records, or drift a benchmark into something easier to publish. The
repository is therefore built around one design idea: **every layer of
the work sits behind an explicit boundary with a tamper-evident record**.
This document describes those boundaries so that a reader can audit them,
and so that the practice can be reused.

The design is deliberately boring: numbered tasks, append-only records,
scripts instead of memory, and a strict separation between *what the
evidence supports* and *what the paper claims*. No layer trusts any
other layer's self-report.

## 1. Task boundary: the numbered-prompt ledger

Every formal task — benchmark code, analysis, paper sections, release
steps — enters the project as a **numbered prompt** and is recorded by a
ledger harness before work starts:

| Phase | What is recorded | Guarantee |
| --- | --- | --- |
| `begin` | The verbatim task text, date, and the current commit | The task scope is fixed before any work happens; the working tree must be clean |
| execute | Work proceeds against the recorded text only | Already-closed ledger rows are immutable |
| `finish` | Binary status (`completed` / `not completed`), the produced file paths, and the **evidence**: the verification commands that were actually run plus their output | A task may be marked `completed` only if its verification commands were genuinely executed; fabricated evidence and phantom paths are rejected |

The finish step commits in two phases: commit A carries the task's
outputs, commit B backfills A's hash into the ledger row. The result is
that every change in the repository's history can be traced to a task
that declared its scope before starting, and every declared completion
carries runnable proof.

The reference implementation of this boundary is published with the
artifact: the ledger harness `scripts/prompt_log.py`, its skill
`.agents/skills/prompt-log/SKILL.md`, and the assistant integrity charter
`AGENTS.md`. The recorded task texts themselves are maintainer-side
work-process records and are intentionally **not** part of the public
artifact (see `docs/PUBLIC_RELEASE_POLICY.md`); the protocol and its
tooling are published, so the discipline is auditable and reusable
without exposing internal working material.

## 2. Tool boundary: single-purpose agent skills

Assistants do not freelance. Recurring operations — task-ledger
bookkeeping, figure generation, manuscript review passes — are captured
as small, versioned, single-purpose **skills** with written acceptance
criteria. A skill specification states exactly when it applies, what it
may touch, and what it must never do (for example: never modify files
under `results/raw/`, never hand-edit ledger metadata, never invent
verification output). This makes assistant behavior consistent across
sessions and reviewable after the fact: the skill text is short enough
to be read by a human, and the repository rules it encodes are enforced
again by scripts and tests.

The task-ledger skill and the integrity charter it encodes are published
with the artifact (`AGENTS.md`,
`.agents/skills/prompt-log/SKILL.md`) so that readers can check the
exact rules assistants operated under; the rest of the maintainer's
local skill bundle is tooling, not research content, and stays outside
the artifact. The constraints that matter to the science are restated
where readers can check them — in this document, in
`docs/experiment_protocol.md`, and in the test suite.

## 3. Scientific boundary: preregistration and deviations

Configurations, hypotheses, operational definitions, verdict thresholds,
and the analysis plan were frozen before the first formal run
(`research/preregistration.md`, commit `8db9c13`, 2026-09-12). Everything
that later deviated from that plan is logged as one of twelve named
deviations D1–D12 (`research/deviations_public.md`) — including the
uncomfortable ones (a paging metric that silently mislabeled runs, an
invalid batch axis, post-hoc analyses). Deviations are summarized, never
silently absorbed: where a rule was re-evaluated post hoc, the frozen and
revised readings are reported side by side in the paper.

## 4. Execution boundary: the supervisor and evidence preservation

Formal runs are executed by a supervisor that records, for every run:
the exact command, the declared configuration, the git commit, model
identity and revision, MLX and `mlx-lm` versions, macOS and hardware
metadata, training method, quantization, batch size, sequence-length
cap, LoRA rank, seed, wall-clock time, memory and throughput metrics,
terminal state, full logs, and a SHA-256 file manifest
(`docs/experiment_protocol.md`). Raw run directories are immutable after
finalization. **Failures are results**: OOM kills, timeouts, and
zero-progress runs are retained in `results/raw/` with the same
provenance as successes — 27 of the 118 finalized runs are failures, and
several boundary findings rest on them.

## 5. Analysis boundary: numbers only from evidence

No benchmark number in the paper or README is hand-typed. Every number is
regenerated from the frozen raw records by committed scripts
(`scripts/run_analysis.py` and friends), and each public claim is tied to
its evidence in a 21-row claim ledger (`research/claim_ledger.csv`) that
names the processed sources and raw run identifiers behind it and grades
each claim (confirmatory, descriptive, boundary observation). A
reproducibility audit (`research/reproducibility_public.md`) declares its
scope and the six known manifest warnings rather than hiding them.

## 6. Review and release boundaries

The manuscript went through a staged review cycle — panel review,
revision, re-review, integrity check, finalize — before freezing, and the
release itself is gated by cross-artifact audits: paper against evidence,
README against paper, claim ledger against evidence, a privacy scan of
the entire reachable Git history, and an **allowlisted** public tree
(`docs/PUBLIC_RELEASE_POLICY.md`) so that internal material (review
transcripts, working notes, task ledger, prompts) cannot leak into the
release by accident. Privacy sanitization applied to historical
environment captures is fully mapped in
`release_sanitization_manifest.jsonl` and described in
`docs/privacy_sanitization.md`.

## Reusing the design

The ingredients are cheap and assistant-agnostic:

1. Put an append-only ledger in front of every formal task; require the
   task text and starting commit to be recorded before work begins.
2. Allow only two completion states, and require the evidence field to
   name commands that were actually executed.
3. Freeze the scientific plan before running, and log deviations instead
   of absorbing them.
4. Make raw records immutable and keep failures.
5. Generate every published number from those records with committed
   scripts, and bind claims to sources in a ledger.
6. Define the public tree by allowlist, and audit the paper, README,
   claims, and history against each other before release.

A solo researcher with AI assistants needs these boundaries more than a
large lab does: they are what make "the assistant said it passed"
convertible into "here is the run that proves it".
