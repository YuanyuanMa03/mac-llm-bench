#!/usr/bin/env python3
"""模型获取校验：对本地 models/<name> 与 HF Hub pinned revision 逐文件校验。

方法（与 models/MANIFEST.md 记录的既有做法一致）：
- 实查 Hub API 得到 revision 与全部文件的 git blob sha1（非 LFS）或
  LFS sha256（LFS 指针对象）；
- 非本地文件哈希对照 blob sha1；LFS 文件对照 lfs.sha256 元数据
  （本地 .cache 中 hf 下载已按内容寻址存储，此处校验字节存在性与 Hub 一致）。

输出：每文件 OK/MISMATCH + 总体结论，供 MANIFEST 更新引用。
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha256_file(path: Path) -> str:
    d = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            d.update(chunk)
    return d.hexdigest()


def main() -> int:
    if len(sys.argv) != 3:
        print("用法: verify_model.py <models/xxx> <hf_repo_id>", file=sys.stderr)
        return 2
    local_dir, repo_id = Path(sys.argv[1]), sys.argv[2]
    from huggingface_hub import HfApi

    api = HfApi()
    info = api.model_info(repo_id, files_metadata=True)
    revision = info.sha
    print(f"[verify] {repo_id} @ {revision}")
    ok = bad = 0
    for s in info.siblings:
        name = s.rfilename
        lpath = local_dir / name
        if not lpath.is_file():
            print(f"  MISSING {name}")
            bad += 1
            continue
        if s.lfs is not None:
            want = s.lfs.sha256
            got = sha256_file(lpath)
        else:
            # git blob hash: sha1("blob <size>\0" + content)，非纯内容 sha1
            data = lpath.read_bytes()
            got = hashlib.sha1(b"blob %d\x00" % len(data) + data).hexdigest()
            want = s.blob_id
        status = "OK" if got == want else "MISMATCH"
        if got == want:
            ok += 1
        else:
            bad += 1
        print(f"  {status:9s} {name} ({lpath.stat().st_size} B)")
    print(f"[verify] {ok} OK / {bad} bad; revision={revision}")
    print(json.dumps({"repo": repo_id, "revision": revision,
                      "ok": ok, "bad": bad}))
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
