# Measurement methodology

## MLX synchronization

A measured training step includes forward computation, backward computation, optimizer update, and the `mx.eval` synchronization that materializes the step. Warmup steps are excluded from reported step-time summaries according to the frozen protocol. Historical timestamps have second-level resolution; future collector records use finer wall and monotonic clocks.

## Allocator peak

Peak memory is `mx.metal.get_peak_memory()` after the training-loop peak reset. It is the MLX allocator high-water mark for the measured training-loop workload, including scheduled validation. It is not process RSS and may exceed physical memory when macOS paging is active.

## Swap sampling

The supervisor samples system swap state at approximately 1 Hz. Initial residency is the system-wide swap-in-use value near run start. The D4 paging proxy is whole-run system swap-in delta divided by completed training steps. Tier-A is below 50 MB per completed step; Tier-B is the remaining set. Both metrics include activity from other processes and cannot attribute pages to the training process.

## Validation evidence

Measurement validation checked synchronized timing behavior, allocator reset behavior, monitor cadence, and supervisor artifact creation before the frozen benchmark. The published benchmark retains observed failures and records absent metrics as unavailable. Six finalized runs have declared manifest digest warnings; all 46 aggregation-included runs re-verify.

## Limits

Machine state can change during a run. Whole-run paging intensity is not a step-local counter. Historical step records lack monotonic timestamps, and killed runs may expose progress only through stdout. These constraints bound the temporal analyses and are retained in the reproducibility audit.
