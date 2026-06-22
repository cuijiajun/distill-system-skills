#!/usr/bin/env python3
"""
distill-finalize.py — 蒸馏收尾脚本
自动完成 step 8/9/10 的全部机械操作 + 自检。

用法:
  python scripts/distill-finalize.py --distilled-dir /path/to/distilled
  python3 scripts/distill-finalize.py --distilled-dir /path/to/distilled [--project-root /path/to/project]

跨平台：Windows / Mac / Linux 均可运行，仅依赖 Python 3 标准库。
"""
import argparse
import json
import os
import shutil
import sys
from pathlib import Path

# 修复 Windows 控制台编码（GBK 不支持 emoji）
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(description="蒸馏收尾脚本：完成 step 8/9/10 + 自检")
    parser.add_argument("--distilled-dir", required=True, help="distilled 目录路径")
    parser.add_argument("--project-root", default=None, help="项目根目录（不传则取 distilled 的父目录）")
    args = parser.parse_args()

    distilled_dir = Path(args.distilled_dir).resolve()
    project_root = Path(args.project_root).resolve() if args.project_root else distilled_dir.parent

    # 定位 skill 目录（脚本在 scripts/ 下，skill 根在父目录）
    script_dir = Path(__file__).parent.resolve()
    skill_root = script_dir.parent
    viewer_src = skill_root / "assets" / "viewer.html"

    print("=" * 50)
    print("  蒸馏收尾脚本 (distill-finalize)")
    print("=" * 50)
    print(f"  DistilledDir: {distilled_dir}")
    print(f"  ProjectRoot:  {project_root}")
    print(f"  SkillRoot:    {skill_root}")
    print()

    if not distilled_dir.exists():
        print(f"[FATAL] distilled 目录不存在: {distilled_dir}")
        sys.exit(1)

    checks = []

    # ============================================================
    # Step 8: 检查 capabilities.json
    # ============================================================
    cap_path = distilled_dir / "capabilities.json"
    tool_count = 0
    sys_name = "蒸馏项目"
    sys_desc = ""

    if cap_path.exists():
        try:
            with open(cap_path, "r", encoding="utf-8") as f:
                cap = json.load(f)
            tool_count = len(cap.get("tools", []))
            sys_name = cap.get("system", sys_name)
            sys_desc = cap.get("description", "")
            checks.append(("8", "capabilities.json", "OK", f"{tool_count} tools"))
            print(f"[Step 8] capabilities.json OK ({tool_count} tools)")
        except Exception as e:
            checks.append(("8", "capabilities.json", "FAIL", f"JSON 解析失败: {e}"))
            print(f"[Step 8] capabilities.json JSON 解析失败: {e}")
    else:
        checks.append(("8", "capabilities.json", "MISSING", "AI 未生成 capabilities.json"))
        print("[Step 8] capabilities.json 不存在！AI 跳过了 step 8。")

    # ============================================================
    # Step 9a: 拷贝 viewer.html -> index.html
    # ============================================================
    index_path = distilled_dir / "index.html"
    if viewer_src.exists():
        shutil.copy2(str(viewer_src), str(index_path))
        size_kb = round(index_path.stat().st_size / 1024, 1)
        checks.append(("9a", "index.html", "OK", f"{size_kb}KB"))
        print(f"[Step 9a] index.html OK ({size_kb}KB)")
    else:
        checks.append(("9a", "index.html", "FAIL", f"viewer.html 源不存在: {viewer_src}"))
        print(f"[Step 9a] viewer.html 源不存在: {viewer_src}")

    # ============================================================
    # Step 9b: 生成 data.js（内嵌全部文档 + 大模型配置）
    # ============================================================
    data_js_path = distilled_dir / "data.js"

    # 收集所有 .md/.json/.txt 文件
    file_list = []
    for ext in (".md", ".json", ".txt"):
        for f in sorted(distilled_dir.rglob(f"*{ext}")):
            if f.is_file():
                rel = f.relative_to(distilled_dir).as_posix()
                with open(f, "r", encoding="utf-8") as fh:
                    text = fh.read()
                file_list.append({"path": rel, "text": text})

    if not file_list:
        checks.append(("9b", "data.js", "FAIL", "distilled/ 下无 .md/.json 文件"))
        print("[Step 9b] distilled/ 下无文件可嵌入！")
    else:
        # 预计算 domainCount
        domain_count = 0
        domain_dir = distilled_dir / "domain"
        if domain_dir.exists():
            domain_count = len([
                f for f in domain_dir.glob("*.md")
                if f.name != "_index.md"
            ])

        # 读取大模型配置
        settings = None
        home = Path.home()
        oc_paths = [
            home / ".joyincode" / "opencode.json",
            home / ".config" / "opencode" / "opencode.json",
        ]
        for oc_path in oc_paths:
            if oc_path.exists():
                try:
                    with open(oc_path, "r", encoding="utf-8") as fh:
                        oc = json.load(fh)
                    model_full = oc.get("model", "")
                    model_name = model_full.split("/")[-1] if "/" in model_full else model_full
                    providers = oc.get("provider", {})
                    if providers:
                        first_prov = list(providers.values())[0]
                        opts = first_prov.get("options", {})
                        settings = {
                            "endpoint": opts.get("baseURL", ""),
                            "apiKey": opts.get("apiKey", ""),
                            "model": model_name,
                            "temperature": 0.3,
                        }
                        print(f"[Step 9b] 大模型配置来源: {oc_path} (model={model_name})")
                        break
                except Exception as e:
                    print(f"[Step 9b] 读取 {oc_path} 失败: {e}")

        # 构建 data 对象
        data_obj = {
            "name": sys_name,
            "description": sys_desc,
            "toolCount": tool_count,
            "domainCount": domain_count,
            "files": file_list,
        }

        # 用 Python json.dumps 生成 JSON（严格转义，解决 PowerShell ConvertTo-Json 的 bug）
        # ensure_ascii=False 保留中文原文，json.dumps 自动转义所有控制字符
        js = "window.__DISTILLED_DATA__ = " + json.dumps(data_obj, ensure_ascii=False, separators=(",", ":")) + ";\n"
        if settings:
            js += "\nwindow.__DISTILLED_SETTINGS__ = " + json.dumps(settings, ensure_ascii=False, separators=(",", ":")) + ";\n"

        with open(data_js_path, "w", encoding="utf-8") as f:
            f.write(js)

        size_kb = round(data_js_path.stat().st_size / 1024, 1)
        checks.append(("9b", "data.js", "OK", f"{size_kb}KB ({len(file_list)} 文件, toolCount={tool_count})"))
        print(f"[Step 9b] data.js OK ({size_kb}KB, {len(file_list)} 文件嵌入)")

    # ============================================================
    # Step 10: 创建/更新项目根 AGENTS.md
    # ============================================================
    agents_path = project_root / "AGENTS.md"
    agents_content = """## 蒸馏文档（AI 能力说明）
本系统已蒸馏为 AI 可用的领域能力文档，位于 `distilled/`。
- 系统能力入口：`distilled/AGENTS.md`（API 清单 + curl 示例 + 编排）
- 查看器/对话：双击 `distilled/index.html`（已内嵌全部文档+大模型配置，开箱即用）
- 涉及本系统业务时，先读 `distilled/00-overview.md` 了解系统能力。
"""

    need_write = True
    if agents_path.exists():
        try:
            existing = agents_path.read_text(encoding="utf-8")
            if "蒸馏文档" in existing:
                need_write = False
                checks.append(("10", "AGENTS.md", "OK", "已存在蒸馏引用"))
                print("[Step 10] AGENTS.md 已含蒸馏引用，跳过")
        except Exception:
            pass

    if need_write:
        if agents_path.exists():
            with open(agents_path, "a", encoding="utf-8") as f:
                f.write("\n" + agents_content)
            checks.append(("10", "AGENTS.md", "OK", "已追加蒸馏引用"))
            print("[Step 10] AGENTS.md 已追加蒸馏引用")
        else:
            with open(agents_path, "w", encoding="utf-8") as f:
                f.write(agents_content + "\n")
            checks.append(("10", "AGENTS.md", "OK", "已新建"))
            print("[Step 10] AGENTS.md 已新建")

    # ============================================================
    # 收尾验证门
    # ============================================================
    print()
    print("=" * 50)
    print("  收尾验证门")
    print("=" * 50)

    all_pass = True
    for step, fname, status, detail in checks:
        if status == "OK":
            icon = "✅"
            print(f"  {icon} Step {step}: {fname:<22} {detail}")
        else:
            icon = "❌"
            all_pass = False
            print(f"  {icon} Step {step}: {fname:<22} {detail}")

    print()
    if all_pass:
        preview_url = distilled_dir.as_uri() + "/index.html"
        print("✅ 蒸馏完成！全部文件就位。")
        print(f"   预览: {preview_url}")
    else:
        print("❌ 蒸馏未完成！有文件缺失或失败，请修复后重跑。")
        print("   缺 capabilities.json = AI 未完成 step 8，需重新蒸馏")
        print("   缺 index.html/data.js = 脚本拷贝/生成失败，检查 skill 目录")
    print()


if __name__ == "__main__":
    main()
