# Raw result schema

## 1. Representation rules

Each experiment produces one UTF-8 JSON object in `results/raw/<experiment_id>/result.json`. JSON is nested for provenance and flattened only in generated processed data.

- Required keys must exist. `nullable` means the value may be JSON `null` when unavailable or not applicable.
- Missing, unknown, unavailable, or failed measurements are `null`, never `0`.
- Measured fields contain measurements only. Any future estimate must use an explicit `estimated_*` name, a method, and provenance.
- Integers are JSON integers; finite measurements are JSON numbers. `NaN`, `Infinity`, numeric strings, and unit-bearing strings are forbidden in numeric fields.
- All byte quantities are bytes; all durations are seconds unless named otherwise; timestamps are RFC 3339 UTC with microseconds.
- Enums are closed sets for a schema version. Maps with tool-specific keys must be JSON-compatible and documented in the effective configuration.
- Paths are POSIX paths relative to the experiment directory unless `path_kind` says `absolute` or `uri`.

“Source” below means the authoritative producer, not a suggestion to invent a value. The raw source output must be retained when practical.

## 2. Top-level object

| Field | Type | Required | Source | Meaning |
|---|---|---:|---|---|
| `schema_version` | string | yes | runner constant | Version of this JSON contract. |
| `protocol_version` | string | yes | effective configuration/repository | Version of the experimental protocol followed. |
| `experiment` | object | yes | ID generator and runner | Identity, command, grouping, and validity metadata. |
| `hardware` | object | yes | preflight collector | Physical host and pre-run capacity. |
| `software` | object | yes | environment collector | OS, Python, packages, and repository state. |
| `model` | object | yes | config plus verified model metadata | Exact model identity and representation. |
| `dataset` | object | yes | config plus preprocessing/data inspection | Exact data identity and transformation. |
| `training` | object | yes | effective config plus initialized model | Fine-tuning configuration and verified parameter counts. |
| `runtime` | object | yes | clocks and system collector | Run phases, work completed, throughput, and resource observations. |
| `metrics` | object | yes | training/evaluation logs | Model-quality metrics and raw metric artifacts. |
| `status` | object | yes | supervisor/exception classifier | Exactly one terminal outcome and failure details. |
| `artifacts` | object | yes | finalizer | Logs, manifests, checkpoints, and hashes. |

## 3. Reusable record types

### `measurement<T>`

System measurements use an explicit envelope so a value is not separated from its evidence.

| Field | Type | Required | Source | Meaning |
|---|---|---:|---|---|
| `value` | `T` or null | yes | named collector | Measured value; `null` if not obtained. |
| `unit` | string | yes | schema constant | Unit such as `bytes`, `count`, `percent`, `seconds`, or `enum`; still present when value is null. |
| `source` | string or null | yes, nullable | collector | Exact command/API and parser version. |
| `sample_time_utc` | string or null | yes, nullable | wall clock | RFC 3339 UTC timestamp for snapshots; null for aggregates with a separate interval. |
| `raw_artifact_path` | string or null | yes, nullable | collector | Retained raw evidence path. |
| `collection_status` | enum | yes | collector | `measured`, `unavailable`, `failed`, `not_applicable`, or `unresolved`. |
| `notes` | string or null | yes, nullable | collector/operator | Limitation or failure reason; not a substitute for a value. |

If `collection_status != "measured"`, `value` must be `null`. A measured numeric zero is valid only when the raw source actually reported zero.

### `artifact_ref`

| Field | Type | Required | Source | Meaning |
|---|---|---:|---|---|
| `path` | string | yes | finalizer | Relative path, absolute path, or URI. |
| `path_kind` | enum | yes | finalizer | `relative`, `absolute`, or `uri`. |
| `sha256` | string or null | yes, nullable | SHA-256 tool | Lowercase 64-hex content digest; null only if the artifact was never created. |
| `size_bytes` | integer or null | yes, nullable | filesystem | Artifact byte size. |
| `media_type` | string or null | yes, nullable | finalizer | MIME type when known. |
| `complete` | boolean | yes | writer | Whether the artifact closed normally. |

## 4. `experiment`

| Field | Type | Unit | Required | Source | Meaning |
|---|---|---:|---:|---|---|
| `id` | string | none | yes | ID generator | Stable experiment ID defined by the protocol. |
| `created_at_utc` | string | UTC timestamp | yes | wall clock | ID/directory creation time. |
| `run_kind` | enum | none | yes | config | `warmup` or `measured`. |
| `comparison_group_id` | string or null | none | yes, nullable | study design | Group whose controlled conditions and independent variables are predeclared together. |
| `repeat_index` | integer | count | yes | config | Zero-based repeat index within a configuration. |
| `supersedes_experiment_id` | string or null | none | yes, nullable | operator/config | Earlier immutable result corrected by this run. |
| `parent_experiment_id` | string or null | none | yes, nullable | sweep/orchestrator | Parent job/sweep ID. |
| `sweep_dimensions` | object | none | yes | generated config | Names and effective values varied by a sweep; `{}` for a single run. |
| `exact_command_argv` | array[string] | none | yes | launcher | Unambiguous executable and arguments. |
| `exact_command_display` | string | none | yes | launcher | Shell-escaped display form; not authoritative. |
| `working_directory` | string | path | yes | process | Absolute launch working directory. |
| `config_path` | string | path | yes | launcher | Raw copied configuration path. |
| `effective_config_path` | string | path | yes | resolver | Canonical resolved configuration path. |
| `config_sha256` | string | none | yes | SHA-256 over canonical effective JSON | Lowercase 64-hex digest. |
| `conditions` | object | none | yes | preflight/operator | Isolation and confounder observations defined below. |
| `validity` | object | none | yes | validator | Booleans `protocol_valid` and `performance_valid`, plus array `exclusion_reasons`; false until final validation. |

`experiment.conditions` contains the following required, nullable observations: `concurrent_ml_jobs_detected` (boolean, process-list/preflight), `major_background_applications` (array of privacy-reviewed names/versions), `cooldown_seconds` (number, seconds), `cache_state` (string: declared cold/warm policy), `run_order_index` (integer, count), `low_power_mode` (boolean, validated power-settings source), `external_display_count` (integer, count), and `notes` (string). Unknown observations are null; an observed empty application list is `[]`.

## 5. `hardware`

Each measurement source is the retained preflight snapshot. String/count fields are required and nullable; absence is never inferred.

| Field | Type | Unit | Required | Source | Meaning |
|---|---|---:|---:|---|---|
| `mac_model` | string or null | none | yes | `system_profiler SPHardwareDataType -json` | Human-readable Mac model. |
| `model_identifier` | string or null | none | yes | same snapshot | Apple model identifier. |
| `apple_chip_model` | string or null | none | yes | same snapshot | Reported Apple chip name. |
| `unified_memory_bytes` | integer or null | bytes | yes | same snapshot or validated `sysctl` key | Installed unified memory. |
| `cpu_physical_cores` | integer or null | count | yes | `sysctl`/hardware snapshot | Physical CPU cores. |
| `cpu_logical_cores` | integer or null | count | yes | `sysctl`/hardware snapshot | Logical CPU cores. |
| `gpu_cores` | integer or null | count | yes | hardware snapshot | GPU cores only when explicitly reported. |
| `machine_id` | string or null | none | yes | study-assigned or salted hash | Pseudonymous stable host identifier; never a serial number. |
| `machine_id_method` | string or null | none | yes | collector config | Derivation description. |
| `storage_type` | string or null | none | yes | `system_profiler SPStorageDataType -json` or explicit inventory | Medium/type relevant to run I/O. |
| `output_filesystem` | string or null | none | yes | `df -kP`/mount metadata | Filesystem holding raw results. |
| `free_disk_before_bytes` | `measurement<integer>` | bytes | yes | `df -kP <output-dir>` | Free space immediately before run. |

## 6. `software`

| Field | Type | Unit | Required | Source | Meaning |
|---|---|---:|---:|---|---|
| `macos_version` | string or null | none | yes | `sw_vers` | Product version. |
| `macos_build` | string or null | none | yes | `sw_vers` | OS build identifier. |
| `python_implementation` | string or null | none | yes | `platform.python_implementation()` | Python implementation. |
| `python_version` | string or null | none | yes | `sys.version` | Full interpreter version/build. |
| `python_executable` | string or null | path | yes | `sys.executable` | Interpreter used by the runner. |
| `mlx_version` | string or null | none | yes | installed distribution metadata | Exact installed MLX version. |
| `mlx_lm_version` | string or null | none | yes | installed distribution metadata | Exact installed `mlx-lm` version. |
| `package_manager` | string or null | none | yes | environment detection/config | Manager and version. |
| `environment_type` | string or null | none | yes | environment detection | For example, venv/conda/uv; only observed value. |
| `environment_path` | string or null | path | yes | process environment | Active environment root. |
| `lockfile` | `artifact_ref` or null | none | yes, nullable | repository | Exact dependency lock, if present. |
| `package_snapshot` | `artifact_ref` or null | none | yes, nullable | package manager | Immutable resolved package listing. |
| `git_commit_sha` | string or null | none | yes | `git rev-parse HEAD` | Source commit. Null outside Git. |
| `git_dirty` | boolean or null | none | yes | `git status --porcelain=v1` | Whether tracked/untracked changes existed. |
| `git_patch` | `artifact_ref` or null | none | yes, nullable | Git plus untracked-source capture | Reproduction evidence for dirty source. |
| `libraries` | object<string,string or null> | none | yes | distribution metadata | Relevant model/data/tokenizer/numerical library versions. |
| `environment_allowlist` | object<string,string or null> | none | yes | redacted environment collector | Only reproducibility-relevant, non-secret variables. |
| `raw_environment_artifact` | `artifact_ref` | none | yes | collector | Redacted raw software/environment evidence. |

## 7. `model`

| Field | Type | Unit | Required | Source | Meaning |
|---|---|---:|---:|---|---|
| `id` | string or null | none | yes | effective config | Model identifier. Null is a configuration error for a run. |
| `provider` | string or null | none | yes | config/resolved repository | Provider or repository host. |
| `repository` | string or null | none | yes | resolver | Exact repository locator. |
| `requested_revision` | string or null | none | yes | config | User-requested revision. |
| `resolved_revision` | string or null | none | yes | repository/cache metadata | Immutable revision/commit actually loaded. |
| `revision_source` | string or null | none | yes | resolver | Evidence used to resolve revision. |
| `local_path` | string or null | path | yes | loader | Local snapshot path, if used. |
| `architecture` | string or null | none | yes | verified model config/library | Architecture actually loaded. |
| `parameter_count` | integer or null | parameters | yes | verified weight/config inspection | Total model parameters before adapters. |
| `parameter_count_method` | string or null | none | yes | inspector | Exact counting method/library. |
| `quantization_state` | enum or null | none | yes | weight/config inspection | `unquantized`, `quantized`, or null if unverified. |
| `quantization_bits` | integer or null | bits | yes | weight/config inspection | Stored weight precision when quantized. |
| `quantization_scheme` | string or null | none | yes | weight/config inspection | Exact scheme/grouping metadata. |
| `model_files_size_bytes` | integer or null | bytes | yes | model manifest | Sum of exact loaded model files. |
| `model_files_manifest` | `artifact_ref` or null | none | yes, nullable | hasher | Per-file paths, sizes, and hashes. |
| `tokenizer_id` | string or null | none | yes | loader | Tokenizer actually loaded. |
| `tokenizer_resolved_revision` | string or null | none | yes | repository/cache metadata | Immutable tokenizer revision. |

## 8. `dataset`

| Field | Type | Unit | Required | Source | Meaning |
|---|---|---:|---:|---|---|
| `name` | string or null | none | yes | config | Dataset name. |
| `source` | string or null | none | yes | config/resolver | Repository, URI, or local source description. |
| `requested_revision` | string or null | none | yes | config | Requested version/revision. |
| `resolved_revision` | string or null | none | yes | dataset/cache metadata | Immutable revision actually used. |
| `train_split` | string or null | none | yes | config | Train split identifier. |
| `validation_split` | string or null | none | yes | config | Validation split identifier. |
| `test_split` | string or null | none | yes | config | Test split identifier. |
| `train_examples` | integer or null | examples | yes | post-preprocessing count | Examples actually available to training. |
| `validation_examples` | integer or null | examples | yes | post-preprocessing count | Validation examples. |
| `test_examples` | integer or null | examples | yes | post-preprocessing count | Test examples. |
| `preprocessing` | object | none | yes | effective config/code | Field mapping, template, normalization, filtering, deduplication, packing, truncation, special-token, padding, and label-mask settings. |
| `preprocessing_code_revision` | string or null | none | yes | Git/config | Immutable recipe/source revision. |
| `tokenizer_id` | string or null | none | yes | preprocessing runtime | Tokenizer actually applied. Must agree with model unless intentionally documented. |
| `tokenizer_revision` | string or null | none | yes | tokenizer metadata | Resolved tokenizer revision. |
| `max_sequence_length` | integer | tokens | yes | effective config | Dataset preprocessing ceiling. |
| `shuffle` | boolean | none | yes | config | Whether examples are shuffled. |
| `split_seed` | integer or null | none | yes | config | Seed for split/shuffle; null only if not applicable. |
| `subset_rule` | object or null | none | yes, nullable | config | Exact deterministic sampling/subset rule. |
| `data_manifest` | `artifact_ref` or null | none | yes, nullable | hasher/dataset cache | Source/materialized file paths, sizes, and hashes. |

## 9. `training`

| Field | Type | Unit | Required | Source | Meaning |
|---|---|---:|---:|---|---|
| `method` | enum | none | yes | config | `full`, `lora`, or `qlora`. |
| `quantization_bits` | integer or null | bits | yes | effective config | Training quantization; null when unquantized/not applicable. |
| `quantization_scheme` | string or null | none | yes | config/runtime | QLoRA quantization scheme. |
| `quantization_group_size` | integer or null | parameters/group | yes | config/runtime | QLoRA group size. |
| `lora_rank` | integer or null | rank | yes | config | LoRA rank; null for full tuning. |
| `lora_alpha` | number or null | none | yes | config | LoRA scaling alpha. |
| `lora_dropout` | number or null | fraction | yes | config | Dropout in `[0,1]`. |
| `target_modules` | array[string] | none | yes | effective initialized config | Exact adapted modules; empty for full tuning. |
| `trainable_layers` | integer or null | count | yes | initialized model inspection | Layers containing trainable parameters under a documented definition. |
| `trainable_parameters` | integer or null | parameters | yes | initialized model inspection | Parameters with gradients enabled. |
| `total_parameters` | integer or null | parameters | yes | initialized model inspection | Parameters under the same counting method. |
| `trainable_parameter_ratio` | number or null | fraction | yes | derived from stored counts | `trainable_parameters / total_parameters`; null if either count missing. |
| `micro_batch_size` | integer | samples/micro-step | yes | effective config | Samples per micro-step. |
| `gradient_accumulation_steps` | integer | micro-steps/optimizer-step | yes | effective config | Accumulation factor. |
| `world_size` | integer | processes | yes | runtime/config | Data-parallel process count. |
| `effective_batch_size` | integer or null | samples/optimizer-step | yes | validated derivation | Effective sample count per optimizer step. |
| `effective_batch_size_formula` | string or null | none | yes | resolver | Explicit derivation including packing/world size. |
| `sequence_length` | integer | tokens | yes | effective config | Training context ceiling. |
| `learning_rate` | number | none | yes | effective config | Base/peak learning rate as defined by scheduler. |
| `optimizer` | string | none | yes | effective config | Optimizer name and implementation. |
| `optimizer_parameters` | object | mixed, keys documented | yes | effective config | All optimizer parameters, including defaults. |
| `scheduler` | string | none | yes | effective config | Scheduler name/implementation. |
| `scheduler_parameters` | object | mixed, keys documented | yes | effective config | All scheduler parameters. |
| `warmup_steps` | integer or null | optimizer steps | yes | config | Warm-up steps. |
| `warmup_ratio` | number or null | fraction | yes | config | Warm-up fraction when ratio-driven. |
| `requested_steps` | integer or null | optimizer steps | yes | config | Planned steps; null when epoch-only. |
| `requested_epochs` | number or null | epochs | yes | config | Planned epochs; null when step-only. |
| `stop_criteria` | object | mixed | yes | effective config | Exact completion/early-stop rules. |
| `seed` | integer | none | yes | config | Primary comparison seed. |
| `library_seeds` | object<string,integer or null> | none | yes | seed initializer | Every library-specific seed actually set. |
| `gradient_checkpointing` | boolean | none | yes | effective runtime | Whether enabled. |
| `parameter_dtype` | string or null | none | yes | initialized model | Parameter dtype. |
| `compute_dtype` | string or null | none | yes | runtime/config | Compute dtype. |
| `optimizer_state_dtype` | string or null | none | yes | initialized optimizer | Optimizer-state dtype. |
| `packing` | boolean | none | yes | effective config | Whether examples are packed. |
| `evaluation_interval_steps` | integer or null | optimizer steps | yes | config | Evaluation cadence; null if disabled. |
| `checkpoint_interval_steps` | integer or null | optimizer steps | yes | config | Checkpoint cadence; null if disabled. |
| `logging_interval_steps` | integer | optimizer steps | yes | config | Metric logging cadence. |
| `resume_checkpoint` | `artifact_ref` or null | none | yes, nullable | config/hasher | Exact checkpoint resumed from. |

## 10. `runtime`

Measurement envelopes are required even when their values are null.

| Field | Type | Unit | Required | Source | Meaning |
|---|---|---:|---:|---|---|
| `start_time_utc` | string or null | UTC timestamp | yes, nullable | wall clock | Child-process start; null if never started. |
| `end_time_utc` | string | UTC timestamp | yes | wall clock | Terminal finalization boundary. |
| `wall_clock_seconds` | number or null | s | yes | monotonic clock | Start-to-end child duration. |
| `model_load_seconds` | number or null | s | yes | monotonic phase events | Model loading duration. |
| `training_loop_seconds` | number or null | s | yes | monotonic phase events | Training-loop duration. |
| `successful_steps` | integer or null | optimizer steps | yes | training log | Completed optimizer updates; zero only when observed, null if the collector cannot establish the count. |
| `attempted_micro_steps` | integer or null | micro-steps | yes | training log | Micro-steps begun; null if unknown. |
| `measured_steps` | integer or null | optimizer steps | yes | timing processor | Successful steps included in summaries after declared exclusions. |
| `excluded_warmup_steps` | integer or null | optimizer steps | yes | timing policy | Completed steps excluded as timing warm-up. |
| `average_step_time_seconds` | number or null | s/optimizer-step | yes | generated from raw timings | Arithmetic mean across measured steps. |
| `median_step_time_seconds` | number or null | s/optimizer-step | yes | generated from raw timings | Median across measured steps. |
| `tokens_processed` | integer or null | tokens | yes | tokenizer/training counters | Tokens in the documented definition. |
| `token_count_definition` | string or null | none | yes | config/counter | Exact numerator definition. |
| `tokens_per_second` | number or null | tokens/s | yes | derived from stored count/time | Throughput for documented interval. |
| `samples_processed` | integer or null | samples | yes | training counter | Samples in measured interval. |
| `samples_per_second` | number or null | samples/s | yes | derived from stored count/time | Sample throughput. |
| `throughput_interval_definition` | string or null | none | yes | timing policy | Inclusion/exclusion of load, warm-up, eval, logging, checkpoints, synchronization. |
| `peak_process_memory_bytes` | `measurement<integer>` | bytes | yes | `/usr/bin/time -l` candidate | Peak process memory under named counter; unresolved until validated. |
| `peak_system_memory_bytes` | `measurement<integer>` | bytes | yes | unresolved | Aggregate system peak; value stays null until defined/validated. |
| `initial_system_memory` | `measurement<object>` | raw counters | yes | `vm_stat`/`memory_pressure -Q` | Baseline counters, not a guessed single used-memory value. |
| `initial_swap_bytes` | `measurement<integer>` | bytes | yes | `sysctl vm.swapusage` | Pre-run system-wide used swap. |
| `peak_swap_bytes` | `measurement<integer>` | bytes | yes | sampled `sysctl vm.swapusage` | Maximum observed used swap. |
| `process_page_faults` | `measurement<integer>` | count | yes | `/usr/bin/time -l` candidate | Raw labeled process counter; semantics pending validation. |
| `process_page_reclaims` | `measurement<integer>` | count | yes | `/usr/bin/time -l` candidate | Raw labeled process reclaim counter. |
| `system_vm_counters_before` | `measurement<object>` | pages/count | yes | `vm_stat` | Raw parsed baseline plus page size. |
| `system_vm_counters_after` | `measurement<object>` | pages/count | yes | `vm_stat` | Raw parsed terminal snapshot. |
| `energy_joules` | `measurement<number>` | J | yes | unresolved/calibrated external meter candidate | Measured interval energy; null until an approved calibrated method exists. `powermetrics` estimates cannot populate this field. |
| `thermal_state_before` | `measurement<string>` | enum | yes | unresolved Foundation helper | Current pre-run thermal state. |
| `thermal_state_peak` | `measurement<string>` | enum | yes | unresolved Foundation helper | Worst observed state using ordered enum. |
| `power_source_before` | `measurement<string>` | enum | yes | `pmset -g batt` | AC/battery/other state. |
| `power_source_after` | `measurement<string>` | enum | yes | `pmset -g batt` | Terminal power source. |
| `monitoring_interval_seconds` | number or null | s | yes | monitoring config | Cadence; null when no periodic monitoring. |
| `monitoring_overhead_validated` | boolean | none | yes | validation evidence | Whether cadence/tool overhead passed the declared test. |
| `step_timing_artifact` | `artifact_ref` or null | none | yes, nullable | logger | Raw per-step events. |
| `system_monitor_artifact` | `artifact_ref` or null | none | yes, nullable | collector | Raw periodic system observations. |

For failure before any work, observed counters such as `successful_steps: 0` are valid. Measurement fields whose collectors never ran remain `null` with a non-measured status.

## 11. `metrics`

Quality metrics are task-dependent; the envelope prevents an arbitrary metric from being mistaken for a benchmark result.

| Field | Type | Unit | Required | Source | Meaning |
|---|---|---:|---:|---|---|
| `training_loss_final` | number or null | dimensionless | yes | training log | Last finite training loss, not best loss; exact reduction is in metric definitions. |
| `validation_loss_final` | number or null | dimensionless | yes | evaluation log | Final validation loss; exact reduction is in metric definitions. |
| `test_metrics` | object<string,number or null> | key-specific | yes | evaluation | Declared task metrics; `{}` when no test evaluation. |
| `metric_definitions` | object<string,object> | none | yes | config/evaluator | For each metric: unit, direction, dataset split, implementation/version, aggregation. |
| `raw_metrics_artifact` | `artifact_ref` or null | none | yes, nullable | logger | Complete step/evaluation metric stream. |

Loss/quality fields are `null` after failures unless genuinely emitted and retained. A partial-run loss may be kept, but terminal status prevents it from being treated as a completed result.

## 12. `status`

| Field | Type | Unit | Required | Source | Meaning |
|---|---|---:|---:|---|---|
| `terminal_state` | enum | none | yes | supervisor/classifier | One of `success`, `oom`, `timeout`, `user_interrupted`, `configuration_error`, `dependency_error`, `model_load_error`, `runtime_error`, `unknown_failure`. |
| `exit_code` | integer or null | none | yes | process supervisor | Child exit code; null if unavailable/not started. |
| `signal` | string or null | none | yes | process supervisor | Terminating signal when applicable. |
| `error_type` | string or null | none | yes | caught exception/OS evidence | Exception/classification evidence. Null on success. |
| `error_message` | string or null | none | yes | caught exception/stderr | Verbatim concise error, with secrets redacted. Null on success. |
| `error_phase` | enum or null | none | yes | supervisor | `preflight`, `model_load`, `training`, `evaluation`, `finalization`, or null. |
| `classification_evidence` | string or null | none | yes | classifier | Rule and evidence supporting non-success class. |
| `result_complete` | boolean | none | yes | finalizer | Whether required finalization completed. |

Consistency rules include: `success` requires exit code `0`, null error fields, and completed requested stop criteria; a non-success must not claim `performance_valid`; `oom` requires explicit OOM evidence; and no terminal state permits deletion of the raw directory.

## 13. `artifacts`

| Field | Type | Required | Source | Meaning |
|---|---|---:|---|---|
| `stdout_log` | `artifact_ref` | yes | process supervisor | Complete raw stdout, possibly empty but present. |
| `stderr_log` | `artifact_ref` | yes | process supervisor | Complete raw stderr, possibly empty but present. |
| `config` | `artifact_ref` | yes | launcher | Exact copied YAML. |
| `effective_config` | `artifact_ref` | yes | resolver | Canonical resolved JSON. |
| `command` | `artifact_ref` | yes | launcher | Exact argv/display/cwd record. |
| `environment_directory` | `artifact_ref` | yes | collector | Archived or manifest-addressed environment evidence. |
| `checkpoints` | array[`artifact_ref`] | yes | trainer/finalizer | Produced checkpoints; empty on none/failure. |
| `additional` | array[`artifact_ref`] | yes | collectors | Other raw artifacts. |
| `manifest_sha256_path` | string | path | yes | finalizer | Hash manifest path. |
| `manifest_sha256` | string or null | none | yes, nullable | hasher | Digest of the manifest file, stored externally or in an append-only index to avoid self-reference. |

## 14. Shape example (values are not benchmark data)

This is a structural example only. Symbolic strings are schema illustrations, and unavailable measurements are null.

```json
{
  "schema_version": "SCHEMA_VERSION",
  "protocol_version": "PROTOCOL_VERSION",
  "experiment": {},
  "hardware": {},
  "software": {},
  "model": {},
  "dataset": {},
  "training": {},
  "runtime": {},
  "metrics": {},
  "status": {},
  "artifacts": {}
}
```

This abbreviated shape is not a valid final result because required nested fields are omitted. It exists only to show top-level organization and to support JSON syntax tests without inventing measurements.

## 15. Flattening for pandas, CSV, plots, and LaTeX

The processed-data generator must:

1. select a schema-version-specific parser;
2. verify the raw manifest before reading;
3. flatten scalar paths with stable dotted names (for example, `training.lora_rank` and `runtime.tokens_per_second`);
4. expose measurement values and provenance separately (for example, `runtime.peak_swap_bytes.value` and `.collection_status`);
5. serialize lists/maps as canonical JSON strings in CSV rather than lossy delimiter joining;
6. retain `experiment.id`, configuration SHA-256, raw manifest hash, status, and validity/exclusion fields in every row; and
7. generate all summary statistics and LaTeX cells from processed rows, never from manually entered benchmark numbers.

One experiment maps to one primary DataFrame row. Repeated per-step samples form a separate long table keyed by `experiment_id`, `step`, and `event_time`, avoiding variable-length arrays in the primary table.

## 16. Validation invariants

A future JSON Schema/validator must reject at least:

- absent required keys; unknown terminal states; non-finite numbers; negative durations/counts; and ratios outside their range;
- a measurement with non-null value when collection status is not `measured`, or a measured status with null value;
- timestamp inversion, `measured_steps > successful_steps`, or negative/excess excluded steps;
- a non-null rate without its numerator, denominator/interval definition, and positive duration;
- a non-null trainable ratio without both counts or with arithmetic disagreement beyond a declared floating tolerance;
- `success` with nonzero/null exit code, non-null error, incomplete result, or unmet stop criteria;
- `performance_valid: true` for non-success or warm-up runs;
- LoRA/QLoRA without rank/alpha/targets, or full tuning with adapter-only fields populated without an explicit extension;
- QLoRA without verified quantization metadata;
- dirty Git state without a patch/untracked-source artifact; and
- absolute/URI artifacts lacking a retention statement in `artifacts.additional` metadata.

The same schema must accept terminal failures with zero completed steps and null unavailable measurements, provided logs, status evidence, command, configuration, and environment provenance are retained.
