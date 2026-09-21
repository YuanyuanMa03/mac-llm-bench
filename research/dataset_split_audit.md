# Formal dataset split audit

## Historical implementation

`scripts/build_formal_dataset.py` used seed 42 to shuffle all source-row
indices, selected the first 2,080 indices, restored those selected examples to
ascending `global_row`, and only then wrote the first 2,048 as training and the
tail 32 as validation.

The resulting historical semantics are therefore:

```text
randomly select 2,080 source rows
→ sort selected rows by source global_row
→ training = sorted rows 1..2,048
→ validation = sorted tail rows 2,049..2,080
```

A direct check of the frozen files confirmed that both splits are sorted and
that `max(train.global_row) < min(validation.global_row)`. The validation set is
not the next 32 examples in shuffled order; it is the 32 highest source-row
indices among the selected 2,080 examples.

## Evidence-preserving disposition

- `data/formal_sft_v1/**` is not rebuilt.
- Its historical MANIFEST wording is not silently rewritten.
- Validation-loss results remain usable as descriptive within-run diagnostics,
  but not as evidence from a shuffled-order random validation split.
- Future dataset builders must split the selected shuffled sequence before any
  presentation-order sort and must test split membership independently of file
  order.

