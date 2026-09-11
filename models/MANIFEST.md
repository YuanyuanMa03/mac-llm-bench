# Model Manifest

Downloaded 2026-08-31 via the `hf` CLI (huggingface_hub 1.29.0), finished 10:34:39 local time.
Revisions were queried live from the HF Hub API on the same date — never inferred from model names.

| Local directory | HF repository | Revision | safetensors on disk | Files |
| --- | --- | --- | --- | --- |
| `models/Qwen3-0.6B` | `Qwen/Qwen3-0.6B` | `c1899de289a0` | 1.503 GB | 10 |
| `models/Qwen3-1.7B` | `Qwen/Qwen3-1.7B` | `70d244cc86cc` | 4.064 GB | 12 |
| `models/Qwen3-0.6B-4bit` | `mlx-community/Qwen3-0.6B-4bit` | `73e3e38d9813` | 0.335 GB | 11 |
| `models/Qwen3-1.7B-4bit` | `mlx-community/Qwen3-1.7B-4bit` | `3b1b1768f8f8` | 0.968 GB | 11 |
| `models/Qwen3-4B` | `Qwen/Qwen3-4B` | `1cfa9a720891` | 8.045 GB | 13 |
| `models/Qwen3-4B-4bit` | `mlx-community/Qwen3-4B-4bit` | `4dcb3d101c2a` | 2.263 GB | 11 |
| `models/Qwen3-8B-4bit` | `mlx-community/Qwen3-8B-4bit` | `545dc4251c05` | 4.608 GB | 11 |
| `models/Qwen3-14B-4bit` | `mlx-community/Qwen3-14B-4bit` | `a4d9b2df59d2` | 8.308 GB | 12 |
| `models/Qwen3-8B` | `Qwen/Qwen3-8B` | `b968826d9c46` | 16.096 GB | 15 |

Verification: local safetensors byte counts match the sizes reported by the Hub API for the pinned revisions.

Notes:

- `models/` is git-ignored; this manifest records provenance in its place.
- Download log: `models/download_20260831.log` (resumed once after an interruption).
- These four downloads ran unauthenticated; the HF account `myy555` was logged in only after they had started, and applies to future downloads.
- `models/Qwen3-4B` (2026-09-07)：HF CDN 链路 TLS 不稳多次中断，改经 **ModelScope** 下载权重、
  HF 主站取回元数据文件；全部 13 个文件已按 pinned revision 逐文件哈希校验
  （LFS 文件 = sha256 对照 `lfs.sha256`；非 LFS = git blob sha1 对照 `blob_id`），
  字节与 HF revision `1cfa9a720891…df60c` 完全一致——下载通道不改变内容 provenance。
- `models/Qwen3-8B` (2026-09-11)：`hf download` 直接从 HF 获取；
  全部 15 个文件按 pinned revision `b968826d9c46…1218` 逐文件校验
  （LFS = sha256；非 LFS = git blob sha1，含 `blob <size>\0` 前缀），15/15 OK
  （`scripts/verify_model.py`）。用于 8B BF16 边界探针（预注册 §7）。
