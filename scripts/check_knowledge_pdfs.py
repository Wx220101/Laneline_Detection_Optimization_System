#!/usr/bin/env python3
"""检查 knowledge/ 下所有 .pdf 是否可被 pdfplumber 打开（与 CrewAI 知识库一致）。"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    import pdfplumber
except ImportError as e:
    print("请先安装: uv sync   （需包含 pdfplumber）", file=sys.stderr)
    raise SystemExit(1) from e


def main() -> int:
    root = Path(__file__).resolve().parents[1] / "knowledge"
    pdfs = sorted(root.rglob("*.pdf"))
    if not pdfs:
        print(f"未在 {root} 下找到任何 PDF。")
        return 0

    print(f"扫描目录: {root}")
    print(f"共 {len(pdfs)} 个文件\n")
    bad = 0
    for p in pdfs:
        rel = p.relative_to(root.parent)
        size = p.stat().st_size
        head = p.read_bytes()[:8]
        magic_ok = head.startswith(b"%PDF")
        err: str | None = None
        pages: int | None = None
        try:
            with pdfplumber.open(p) as doc:
                pages = len(doc.pages)
        except Exception as e:
            err = f"{type(e).__name__}: {e}"
            bad += 1

        ok = err is None and magic_ok
        flag = "OK " if ok else "BAD"
        print(f"[{flag}] {rel}")
        print(f"      大小={size}  头=%PDF:{magic_ok}  {head!r}")
        if pages is not None:
            print(f"      页数={pages}")
        else:
            print(f"      错误: {err}")
        print()

    if bad:
        print(f"结论: {bad} 个文件无法作为合法 PDF 解析，请更换或重新导出。")
        return 1
    print("结论: 全部可解析。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
