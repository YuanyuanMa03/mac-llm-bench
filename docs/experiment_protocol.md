# Experiment protocol

## 1. Purpose and normative language

This protocol defines the evidence that must accompany every fine-tuning attempt in this repository. It does not define a training implementation. `MUST`, `MUST NOT`, and `SHOULD` are normative.

Two rules take precedence throughout:

- A missing, unavailable, or failed measurement is `null`; it is never `0` and is never estimated.
- Every number reported in analysis or a paper MUST be traceable to an immutable raw result and, where applicable, its raw monitoring log.

Fields described as required must be present in the result object. A required field may still have value `null` when the source is unavailable; its companion source/notes field must explain why. Estimates, if introduced in a later protocol version, must use a separately named `estimated_*` field and must never replace a measured field.

All timestamps use RFC 3339 UTC with microseconds (`YYYY-MM-DDTHH:MM:SS.ffffffZ`). Durations use seconds, byte quantities use bytes, rates use explicit denominator units, and percentages use the closed interval 0--100 unless the field is explicitly a ratio.

## 2. Experiment lifecycle

1. Resolve the effective configuration without downloading or changing dependencies.
2. Generate and reserve the experiment ID (Section 9).
3. Create `results/raw/<experiment_id>/` and write the proposed configuration, exact argument-vector command, working directory, and initial environment snapshot.
4. Run preflight checks. A preflight failure still produces a terminal raw result.
5. Record pre-run hardware, power, disk, memory, swap, and thermal observations.
6. Start raw stdout, stderr, and monitoring logs before model loading.
7. Execute exactly one training process and retain failures, including OOM.
8. Record the end time, terminal state, exit code, final measurements, and artifact hashes.
9. Atomically finalize the result (for example, write `result.json.tmp`, `fsync`, then rename to `result.json`) and make the directory read-only where practical.
10. Never modify the finalized directory. A correction is a new experiment linked by `experiment.supersedes_experiment_id`.

An interrupted collector should leave a recoverable partial directory. Recovery may append a terminal `unknown_failure` result only if no finalized result exists; it may not rewrite measurements already emitted. The future runner must document its crash-recovery behavior.

## 3. Required record

Every attempt must contain the following categories. Exact field names and types are defined in [result_schema.md](result_schema.md).

### 3.1 Experiment identity and provenance

Record the experiment ID, schema version, protocol version, creation time, whether the run is warm-up or measured, repeat index, comparison-group ID, parent/superseded experiment IDs, exact command as an argument array plus a display string, working directory, effective configuration, configuration SHA-256, and hostname/machine identifier when available. The argument array is authoritative because shell quoting can make a display string ambiguous.

### 3.2 Hardware

Record:

- Mac model and model identifier;
- Apple chip model;
- total unified memory in bytes;
- physical and logical CPU core counts (do not collapse them into one ambiguous count);
- GPU core count;
- a pseudonymous machine identifier when available;
- storage medium/type when relevant to model or dataset I/O; and
- free bytes on the filesystem containing the raw output directory immediately before the experiment.

Preferred sources are `system_profiler SPHardwareDataType -json`, `sysctl`, `ioreg` only when a documented key is selected, and `df -kP <output-directory>`. Record the command and raw snapshot. `system_profiler` output varies by Mac/macOS release; absent keys are `null`. Do not infer GPU cores, memory, or model properties from a product name. Never store a hardware serial number. Derive any machine identifier by hashing a stable local identifier with a study-specific salt, or use a study-assigned label; record the derivation method, not the secret salt.

### 3.3 Software

Record:

- macOS product version and build;
- Python implementation and full version;
- MLX and `mlx-lm` versions;
- package manager, virtual-environment type/path, lockfile path and SHA-256 when present;
- an immutable installed-package snapshot (for example, `python -m pip freeze --all` plus its file hash; use the native equivalent for the selected manager);
- Git commit SHA and dirty status, plus a patch artifact when dirty;
- versions of model, dataset, tokenizer, acceleration, and numerical libraries that affect the run; and
- relevant environment variables after allow-listing and secret redaction.

Use `sw_vers`, `python --version` plus `sys.version`, package metadata (`importlib.metadata.version`), package-manager-native lock/snapshot commands, and `git rev-parse HEAD` / `git status --porcelain=v1`. Preserve raw outputs. A missing Git repository yields `git_commit_sha: null` and `git_dirty: null`; such a run may be retained for debugging but is not a valid measured benchmark. A dirty-tree run must store a binary-safe patch or archive of untracked source files; dirty status alone is not reproducible. Never capture tokens, passwords, cookies, or unrelated environment variables.

### 3.4 Model

Record model ID, provider/repository, exact resolved revision/commit, local model path when used, parameter count, architecture, pre-training quantization state and bits, tokenizer ID/revision, model file size in bytes when measurable, and a manifest of model-file hashes where practical.

The resolved revision must come from repository metadata, a locally cached snapshot identifier, or an artifact manifest. Parameter counts must come from verified configuration/weight inspection or a library-reported count whose method is recorded. Never infer either from the model name. For sharded or cached models, define file size as the sum of the exact files in the stored manifest; do not use the size of an unrelated cache directory. Unverified values are `null`.

### 3.5 Fine-tuning configuration

Record:

- method: `full`, `lora`, or `qlora`;
- quantization bits (`null` for unquantized training); for QLoRA also record quantization scheme, group size, and compute dtype when supported;
- LoRA rank, alpha, dropout, and target modules (`null`/empty only when not applicable);
- number of trainable layers, trainable parameters, total parameters, and trainable-parameter ratio;
- micro-batch size, gradient accumulation steps, effective batch size, and the exact formula used;
- sequence length;
- learning rate, optimizer and all non-default optimizer parameters;
- scheduler, scheduler parameters, warm-up steps or ratio;
- requested steps and epochs (`null` when not applicable), plus stop criteria;
- seed and every library-specific seed actually set;
- gradient checkpointing state; and
- parameter, compute, and optimizer-state precision/dtype.

The effective batch size must not be assumed to equal `micro_batch_size * gradient_accumulation_steps` if data parallelism or packing changes its meaning. Record `effective_batch_size_formula` and world size. Trainable/total parameter counts must be obtained after adapters, freezing, and quantization are applied. Store the ratio as a dimensionless fraction in `[0, 1]` and preserve the underlying counts.

Also record data packing, padding side, truncation behavior, loss-mask policy, evaluation/checkpoint/logging cadence, resume checkpoint and hash, and any early-stopping rule because these can alter work performed or timing.

### 3.6 Dataset

Record dataset name, source, resolved revision/version, local paths or split identifiers, train/validation/test example counts, preprocessing configuration, preprocessing code/recipe version, tokenizer ID and resolved revision, tokenizer settings, maximum sequence length, shuffle state, split seed, sampling/subset rules, and hashes where practical.

For local data, store a deterministic manifest containing relative path, byte size, and SHA-256 per source file. For remote datasets, record the immutable revision plus hashes of materialized split/cache artifacts when practical. Split sizes must be counted after filtering and splitting; if not measured, use `null`. Preprocessing configuration must include prompt/template formatting, field mapping, normalization, filtering, deduplication, packing, truncation, special tokens, and label masking. Do not copy sensitive dataset contents into metadata.

### 3.7 Runtime and training measurements

Record experiment start/end UTC timestamps, wall-clock seconds from a monotonic clock, model-load duration, training-loop duration, requested and successful optimizer steps, attempted micro-steps, warm-up steps excluded from performance summaries, per-step timing artifact, average and median measured step time, tokens processed, tokens/second, samples/second, peak process memory, peak system memory, initial and peak swap, page-fault counters, energy, and thermal observations.

Rate denominators must be explicit. `tokens_processed` must state whether it counts non-padding input tokens, loss-bearing tokens, padded tokens, or another exact definition. Throughput must be computed from raw counts and the documented measured interval; it must not include model download and should separately state whether model load, evaluation, checkpointing, and logging are included. Store raw per-step timing so summary values are generated rather than manually typed.

### 3.8 Outcome and artifacts

Exactly one terminal state is required:

- `success`
- `oom`
- `timeout`
- `user_interrupted`
- `configuration_error`
- `dependency_error`
- `model_load_error`
- `runtime_error`
- `unknown_failure`

Also record process exit code (`null` only if no child process was started or no code was recoverable), signal, error type, error message, error phase, stdout/stderr paths, and whether the result is complete. Classify OOM only from an explicit exception, OS termination evidence, or a documented detector; do not classify OOM solely because memory was high. Preserve complete stdout and stderr even on failure. OOM and every other failed experiment are valid observations and MUST NOT be deleted.

Every result directory contains, at minimum:

- `result.json`: finalized nested result;
- `config.yaml`: exact user configuration;
- `effective_config.json`: resolved defaults and configuration SHA-256 input;
- `command.json`: executable, argument vector, display form, working directory;
- `environment/`: raw environment, package, Git, OS, and hardware snapshots;
- `logs/stdout.log` and `logs/stderr.log`;
- raw timing/monitoring logs, even if incomplete; and
- `manifest.sha256`: hashes of all finalized files except the manifest itself, with the exclusion documented.

Paths stored in JSON are relative to the experiment directory when possible. Artifacts outside it require an absolute URI/path, hash, and retention policy.

## 4. macOS system-measurement plan

The table distinguishes observed command availability from publication readiness. “Conditionally usable” means the command/API is a proposed source, but parsing, overhead, scope, and repeatability must be validated before the metric appears in a paper. “Unresolved” means the measured field remains `null` in paper-bound results until a method is validated.

| Metric | Proposed macOS source and method | Stored unit | Known limitations | Publication status |
|---|---|---:|---|---|
| Wall-clock duration | Record UTC boundaries; compute duration with Python `time.monotonic_ns()` around the child process and phase boundaries. | s | Clock placement determines included work; suspend/sleep and phase definitions need tests. | Conditionally usable; validate runner implementation against a controlled sleep/process test. |
| Per-step time | Emit monotonic timestamps around synchronized optimizer steps; preserve raw events. | s/step | Asynchronous Metal work can make unsynchronized host timings too small; synchronization API and overhead must be validated for the installed MLX version. | Unresolved until MLX synchronization behavior is tested. |
| Process peak memory | Wrap the training child with `/usr/bin/time -l`; preserve `maximum resident set size` and `peak memory footprint` output. Optionally sample `ps` only as a diagnostic. | bytes | Scope and units must be confirmed on the target macOS; RSS may not represent all unified/Metal allocations; child/grandchild coverage and sampling differ. A local smoke command produced both labels, but that does not validate MLX accounting. | Unresolved for paper use until compared with a known allocation and MLX workload. |
| System memory baseline | Preserve `vm_stat` output and page size immediately before/after; optionally sample during the run. | pages in raw log; derived bytes only after a validated formula | `vm_stat` exposes categories, not a single canonical “used memory”; compression, purgeable/file-backed pages, and concurrent applications confound a derived total. | Raw counters usable as context; aggregate system-used memory unresolved. |
| Peak system memory | Periodically capture timestamped `vm_stat` and `memory_pressure -Q`. | bytes or %, depending on validated definition | Sampling can miss peaks; there is no validated canonical conversion in this repository; `memory_pressure` percentage is not application attribution. | Unresolved; `runtime.peak_system_memory_bytes` stays `null`. |
| Initial/peak swap | Capture `sysctl vm.swapusage` immediately before the run and sample it at a fixed interval; peak is the maximum observed `used` value. Preserve raw lines. | bytes | System-wide, affected by other processes; sampling misses transients; parsing/units can change; swap may not return to baseline after a run. | Conditionally usable after parser fixtures and sampling-overhead validation. |
| Page faults | Preserve `/usr/bin/time -l` `page faults` and `page reclaims`; also preserve before/after `vm_stat` counters for system context. | count | Process vs system scopes differ; labels do not by themselves establish major/minor semantics; descendants and OS-version behavior need validation. | Unresolved for comparative claims; raw counters may be reported descriptively with scope. |
| Power-source state | Capture `pmset -g batt` immediately before and after; parse AC/battery state and battery percentage when exposed. | enum and % | A snapshot can miss transitions; UPS/desktop output differs. It is not an energy measure. | Conditionally usable after parser tests; record raw output. |
| Energy consumption | `powermetrics` can sample supported power domains, but its output may only be retained as raw diagnostic evidence. A measured `energy_joules` value requires a separately validated calibrated external meter and synchronized interval. | J for calibrated measurement; raw W samples for diagnostics | `powermetrics` requires superuser for actual sampling on the inspected host; support varies. Its own help says values are estimated and may be inaccurate and should not compare devices. Monitoring overhead is unvalidated. Any later derived value must be named `estimated_energy_joules`, never `energy_joules`. | Unresolved for primary paper comparisons. |
| Thermal state | Preferred candidate: a small Foundation helper reading `ProcessInfo.thermalState` at pre-run and periodically; retain enum transitions. `pmset -g therm` may be stored only as diagnostic output. | enum (`nominal`, `fair`, `serious`, `critical`) | The helper has not been implemented or validated. `pmset -g therm` observed only historical warning messages and did not supply current thermal state. Coarse states do not provide temperature. | Unresolved until the Foundation API path, cadence, and overhead are validated. |
| Hardware inventory | `system_profiler SPHardwareDataType -json`, selected `sysctl` keys, and a raw snapshot. | model strings, bytes, count | Keys vary by hardware/OS; GPU core count may be absent. Serial numbers must be excluded. | Conditionally usable with schema-aware parsing and fixtures; absent values are `null`. |
| Free disk | `df -kP <raw-output-directory>` immediately before the run; convert 1024-byte blocks to bytes and retain raw output. | bytes | APFS snapshots, quotas, purgeable space, and concurrent writes affect availability. | Usable as contextual metadata after conversion test. |

The command probes performed while writing this protocol establish only that selected commands execute on one local host; they do not validate a future collector, its parsing, or metric semantics.

## 5. Experimental isolation and confounder control

- Run no other ML training, inference, model conversion, or benchmark job concurrently.
- Record whether the Mac is connected to AC power before and after; abort or flag the run if the source changes.
- Record the current thermal state before starting when a validated method becomes available; until then record `null` and the unresolved reason. Use a fixed idle/cool-down policy within each comparison and record its actual duration.
- Capture baseline system memory, memory-pressure output, and swap immediately before training.
- Close major background applications where possible. Otherwise record application name/version or an approved process-list snapshot, with privacy review.
- Disable or document scheduled jobs, OS updates, indexing, cloud sync, backups, displays/external peripherals, Low Power Mode, and other material background activity.
- Use the same hardware, power mode, macOS build, Python environment, MLX/`mlx-lm` versions, model/tokenizer/dataset revisions, monitoring configuration, and storage location across a controlled comparison unless the changed item is the independent variable.
- Fix random seeds for controlled comparisons and record every seed actually applied. A fixed seed does not imply deterministic Metal kernels; test and report determinism separately.
- Randomize or counterbalance run order where thermal drift, cache state, or swap accumulation could bias a sweep; record order.
- Repeat performance-sensitive measured configurations at least three times unless a written power/precision rationale sets another count. Repetitions use distinct experiment IDs and explicit `repeat_index`; do not discard inconvenient repeats.
- Mark warm-up runs with `experiment.run_kind: warmup`. Warm-ups are retained but excluded from measured summaries. Define whether caches are cold/warm and whether model loading is included before collection.
- Use a fixed monitoring cadence within a comparison. Measure monitoring overhead with the same workload before adopting a cadence.
- Never compare results collected under materially different conditions without naming the difference and treating it as a potential confounder.

## 6. Validity rules

A **protocol-valid result** (including failure/OOM) has a unique ID; finalized immutable directory; required keys; exact command and effective configuration; environment/Git evidence; raw logs; a justified terminal state; internally consistent timestamps; and a complete hash manifest. It contains no fabricated or silently estimated measurement.

A **performance-valid benchmark run** is a protocol-valid `success` result that additionally:

1. is marked `measured`, not `warmup`;
2. used the predeclared configuration and comparison environment;
3. ran alone on the machine with stable documented power state;
4. completed the predeclared measured interval and required successful steps;
5. has no collector gap or measurement error affecting the primary metric;
6. uses a validated timing/synchronization method;
7. has documented thermal/baseline status and no unplanned material interference; and
8. passes automated consistency checks (counts, formulas, timestamp order, hashes, and status/exit-code rules).

An OOM or failed run can be protocol-valid and is an important feasibility observation, but it is not a performance-valid throughput run. Analysis must not silently mix these populations. An invalid run remains immutable and receives explicit exclusion reasons; it is never deleted.

## 7. Raw-result immutability and data flow

- Raw results live only under `results/raw/<experiment_id>/` (or one equivalently named immutable file per experiment if a future storage backend requires it).
- Exactly one experiment attempt owns each raw directory. Never reuse or overwrite an ID.
- After finalization, raw files MUST NOT be edited, reformatted, recompressed, or “fixed.” Corrections create a new experiment and link to the old ID.
- Analysis and figure code may only read `results/raw/`; it must never write there.
- Derived tabular data belongs in `results/processed/`. Each derived dataset records the analysis commit, input experiment IDs and manifest hashes, command, and generation timestamp.
- Programmatically generated figures belong in `results/figures/`. Never manually type benchmark numbers into plots or paper tables.
- Failed, timed-out, interrupted, dependency-error, and OOM directories are retained under the same policy as successes.
- Backups and transfers must preserve file bytes and verify `manifest.sha256` after copying.

Repository policy should make finalized raw paths append-only (for example, permissions plus CI checks), but filesystem permissions are not a substitute for hashes and review.

## 8. Comparisons and reporting

Define a comparison group before running it: independent variable(s), controlled variables, primary metric, warm-up policy, repetition count, exclusion rules, and aggregation method. Report individual runs and distribution summaries; do not report only the best run. Any post-hoc exclusion must be recorded with an immutable exclusion-reason artifact and remain auditable.

Only generated processed data may feed pandas, CSV exports, plots, or LaTeX tables. Generated rows must include `experiment.id`, terminal state, validity flags, configuration hash, and raw manifest hash so a paper value can be traced back to raw evidence.

## 9. Experiment ID strategy

Generate the ID once, immediately before the raw directory is created:

```text
<UTC>__<model-slug>__<method>-q<bits-or-none>__ctx<context>__b<micro>-ga<accum>__r<rank-or-na>__s<seed>__<uuid7>
```

Example **format only** (not an experiment or measurement):

```text
YYYYMMDDTHHMMSSffffffZ__model-slug__lora-qnone__ctx512__b1-ga1__r8__s42__UUID7
```

Rules:

- `<UTC>` is the ID-generation time in UTC with microseconds. It aids sorting and debugging but is not the authoritative start timestamp.
- Slugs are lowercase ASCII `[a-z0-9-]`, repeated hyphens are collapsed, and model slug is capped at 32 characters. Numeric fields are validated decimal integers.
- `uuid7` is the full canonical lowercase UUIDv7 without braces. It supplies programmatic uniqueness even for simultaneous/repeated configurations; do not truncate it.
- Non-applicable fields use the literal `na`; unknown required configuration is a preflight configuration error, not an `unknown` slug.
- The ID is stored in `result.json` and never recomputed or renamed. Effective configuration canonicalization and SHA-256 are stored separately; identical configurations intentionally receive different run IDs.
- Before creation, use an atomic exclusive directory-create operation. Any collision is a hard error and must not overwrite existing data.

The factor segment is for diagnosis, not parsing or scientific truth. Analysis reads the JSON fields, never reverse-engineers variables from the filename.

## 10. Reproducibility review and unresolved issues

The following issues must be resolved or explicitly accepted before the first paper-bound run:

- **Repository identity:** the inspected skeleton is not currently a Git repository. Initialize version control and commit the runner/protocol before measured runs.
- **Environment lock:** no package-manager configuration or lock content is currently present. Select one manager, lock exact transitive dependencies, and validate environment export/recreation on a clean environment.
- **Model/data identity:** choose model and dataset IDs, immutable revisions, licenses, tokenizer revision, and artifact hashing. Names alone are insufficient.
- **Timing correctness:** validate MLX synchronization around step boundaries and specify inclusion of evaluation/checkpoint/logging.
- **Memory semantics:** validate `/usr/bin/time -l` units/scope and determine how MLX/Metal unified allocations appear. No validated definition for peak system memory exists yet.
- **Swap/page faults:** build parser fixtures, establish scopes, choose cadence, and quantify collector overhead. These system-wide metrics are confounded by background processes.
- **Thermal state:** implement and validate the Foundation `ProcessInfo.thermalState` collector. `pmset -g therm` is not accepted as current thermal state.
- **Energy:** `powermetrics` requires elevated permission on the inspected host, reports estimates, varies by hardware, and may add overhead. It is not currently approved for primary paper claims. A calibrated external power meter would require its own protocol and synchronization.
- **Monitoring privilege/privacy:** do not run the trainer as root. If a privileged sidecar is ever approved, constrain it, log the authorization and command, and audit outputs for process names or sensitive paths.
- **Monitoring overhead:** benchmark the collector off/on at candidate cadences before choosing one; do not assume overhead is negligible.
- **Redundancy:** model/tokenizer identifiers appear in model and dataset/training contexts; the canonical identities live under `model`, while dataset fields state the tokenizer actually used. Parameter counts are deliberately duplicated only as underlying counts plus a derived ratio; consistency checks must reject disagreement.
- **Confounders:** thermal history, run order, cache warmth, swap baseline, background services, power mode, OS build, filesystem volume/free space, model/data cache placement, dataset order/packing, logging/evaluation/checkpoint cadence, display/peripheral state, and nondeterministic kernels can alter results.
- **Paper validation:** timing synchronization, token accounting, effective-batch formula, parameter counts, quantization state, peak-memory interpretation, parser units, sampler cadence/overhead, failure classification, repeat count, and statistical aggregation must each have executable tests before publication.

Information that could still block independent reproduction includes unavailable model/data artifacts, mutable upstream revisions, missing dirty-tree content, undisclosed preprocessing code, secrets required for access, unavailable macOS/hardware versions, and unspecified library defaults. Record these as limitations; do not fill them with guesses.

## 11. Protocol change control

Store a protocol version in every result. Changes to field meaning, units, validity rules, measurement commands, or parsing require a new protocol/schema version and migration notes. Never reinterpret old raw fields in place; transform them into a versioned processed dataset.
