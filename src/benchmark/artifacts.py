"""原子 finalize 与 SHA-256 manifest。

流程：staging 目录写齐所有文件 → 生成 manifest.sha256（覆盖除自身外全部文件）
→ 自底向上只读化（文件 0o400、目录 0o500）→ rename 到最终目录。
最终目录已存在时为硬错误：绝不覆盖已 finalize 的 raw result（协议 §10）。
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_manifest(result_dir: Path) -> Path:
    """生成 manifest.sha256，行格式 `digest␠␠relative/path`（sha256sum 兼容）。"""
    entries: list[tuple[str, str]] = []
    for path in sorted(result_dir.rglob("*")):
        if path.is_file() and path.name != "manifest.sha256":
            entries.append((sha256_file(path),
                            path.relative_to(result_dir).as_posix()))
    manifest = result_dir / "manifest.sha256"
    manifest.write_text("".join(f"{digest}  {rel}\n" for digest, rel in entries),
                        encoding="utf-8")
    return manifest


def make_read_only(root: Path) -> None:
    """自底向上只读化：先文件后目录，保证可遍历。"""
    paths = sorted(root.rglob("*"), key=lambda p: len(p.parts), reverse=True)
    for path in paths:
        if path.is_file():
            os.chmod(path, 0o400)
        elif path.is_dir():
            os.chmod(path, 0o500)
    os.chmod(root, 0o500)


def finalize(staging: Path, final: Path) -> Path:
    if final.exists():
        raise RuntimeError(
            f"raw result 目录已存在，拒绝覆盖（不可变策略）：{final}"
        )
    write_manifest(staging)
    make_read_only(staging)
    os.rename(staging, final)
    return final


def verify_manifest(result_dir: Path) -> bool:
    """逐文件校验 manifest；目录必须只读且无残留 staging。"""
    manifest = result_dir / "manifest.sha256"
    if not manifest.is_file():
        return False
    listed: dict[str, str] = {}
    for line in manifest.read_text(encoding="utf-8").splitlines():
        digest, rel = line.split("  ", 1)
        listed[rel] = digest
    actual = {
        path.relative_to(result_dir).as_posix()
        for path in result_dir.rglob("*")
        if path.is_file() and path.name != "manifest.sha256"
    }
    if set(listed) != actual:
        return False
    return all(sha256_file(result_dir / rel) == digest
               for rel, digest in listed.items())
