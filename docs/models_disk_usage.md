# models/ 磁盘占用

采集时间：2026-08-31。数据来自真实运行的 `du -sk` / `df -k` 输出（见文末命令）；
revision 来自下载当日（2026-08-31）的 Hub API 实查，与 [models/MANIFEST.md](../models/MANIFEST.md) 一致。

| 目录 | Revision | du -sk（含 .cache） | 约合 |
| --- | --- | --- | --- |
| `models/Qwen3-0.6B` | `c1899de289a0` | 1,499,972 | ≈1.43 GiB |
| `models/Qwen3-1.7B` | `70d244cc86cc` | 3,983,928 | ≈3.80 GiB |
| `models/Qwen3-0.6B-4bit` | `73e3e38d9813` | 343,236 | ≈0.33 GiB |
| `models/Qwen3-1.7B-4bit` | `3b1b1768f8f8` | 961,036 | ≈0.92 GiB |
| `models/download_20260831.log` | — | 4 | — |
| **合计 `models/`** | — | **6,788,180** | **≈6.47 GiB** |

卷剩余空间（采集时）：`/dev/disk5s1` 可用 646,766,416 KB ≈ 617 GB。

说明：du 计的是分配块（含 hf 下载期间的内部 `.cache`），略小于
MANIFEST 中 safetensors 逻辑字节总和（≈1.503+4.064+0.335+0.968 GB）属预期。

## 采集命令

```bash
du -sk models/Qwen3-0.6B models/Qwen3-1.7B models/Qwen3-0.6B-4bit models/Qwen3-1.7B-4bit models/download_20260831.log
du -sk models/
df -k <repo-volume>
```
