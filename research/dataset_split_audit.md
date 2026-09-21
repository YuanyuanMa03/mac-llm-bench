# Dataset split audit

The frozen `formal_sft_v1` dataset was created from a pinned UltraChat source revision. The builder selected 2,080 source rows, restored their source-row order, then assigned the first 2,048 rows to training and the final 32 rows to validation. Checksums are recorded in `data/formal_sft_v1/SHA256SUMS`.

The historical trainer traversed the initial training order sequentially. No formal run consumed all 2,048 training examples, so seeds changed model and adapter initialization without changing the initial sample order. Validation examples form a source-order tail rather than a randomized representative holdout. Final validation losses are therefore descriptive results for this frozen split; they do not establish converged quality equivalence.

Future collector behavior may shuffle at epoch zero under a newer protocol. That change does not describe the 118-run frozen corpus.
