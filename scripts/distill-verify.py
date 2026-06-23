#!/usr/bin/env python3
"""
distill-verify.py — 蒸馏综合验证脚本
蒸馏结束后必须运行，自动检查所有 S0-S6 检查点并出报告。

用法:
  python scripts/distill-verify.py --distilled-dir <distilled路径> --source-dir <项目源码路径>
  python3 scripts/distill-verify.py --distilled-dir <distilled路径> --source-dir <项目源码路径>

跨平台：Windows / Mac / Linux，仅依赖 Python 3 标准库。
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

# 修复 Windows 控制台编码
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# 颜色
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"


class CheckResult:
    def __init__(self, stage, name, passed, detail="", missing=None):
        self.stage = stage
        self.name = name
        self.passed = passed
        self.detail = detail
        self.missing = missing or []


def main():
    parser = argparse.ArgumentParser(description="蒸馏综合验证脚本")
    parser.add_argument("--distilled-dir", required=True, help="distilled 目录路径")
    parser.add_argument("--source-dir", default=None, help="项目源码根目录（用于 Controller 覆盖率检查）")
    args = parser.parse_args()

    distilled = Path(args.distilled_dir).resolve()
    source = Path(args.source_dir).resolve() if args.source_dir else None

    print(f"\n{CYAN}{'='*60}")
    print(f"  蒸馏综合验证 (distill-verify)")
    print(f"{'='*60}{RESET}")
    print(f"  DistilledDir: {distilled}")
    print(f"  SourceDir:    {source}")
    print()

    if not distilled.exists():
        print(f"{RED}[FATAL] distilled 目录不存在{RESET}")
        sys.exit(1)

    results = []

    # ============================================================
    # S1: 文件完整性
    # ============================================================
    expected_files = [
        "00-overview.md",
        "01-glossary.md",
        "README.md",
        "AGENTS.md",
        "capabilities.json",
        "domain/_index.md",
        "api/_index.md",
        "reference/enums.md",
        "reference/error-codes.md",
        "reference/model-code-conflicts.md",
        "requirements/_index.md",
    ]
    for f in expected_files:
        p = distilled / f
        if p.exists():
            results.append(CheckResult("S1", f"文件存在: {f}", True))
        else:
            results.append(CheckResult("S1", f"文件存在: {f}", False, "缺失"))

    # domain 对象文件（排除 _index）
    domain_dir = distilled / "domain"
    domain_files = [f for f in domain_dir.glob("*.md") if f.name != "_index.md"] if domain_dir.exists() else []
    if domain_files:
        results.append(CheckResult("S1", f"domain 对象文档 ({len(domain_files)} 个)", True))
    else:
        results.append(CheckResult("S1", "domain 对象文档", False, "domain/ 下无对象文件（仅 _index）"))

    # ============================================================
    # S2: 规则执行方标注 + 冲突表
    # ============================================================
    rule_labels = ["服务端强制", "服务端维护", "调用方需预判", "副作用"]
    domain_md_files = list(domain_dir.glob("*.md")) if domain_dir.exists() else []
    api_md_files = list((distilled / "api").rglob("*.md")) if (distilled / "api").exists() else []
    all_md_files = domain_md_files + api_md_files

    files_with_rules = 0
    files_missing_labels = []
    for md in all_md_files:
        if md.name == "_index.md":
            continue
        content = md.read_text(encoding="utf-8")
        if "规则" in content or "规则" in content:
            has_label = any(label in content for label in rule_labels)
            if has_label:
                files_with_rules += 1
            else:
                files_missing_labels.append(md.name)

    if files_missing_labels:
        results.append(CheckResult("S2", "规则执行方标注", False,
                                   f"{len(files_missing_labels)} 个文件有规则但无标注",
                                   files_missing_labels[:5]))
    else:
        results.append(CheckResult("S2", "规则执行方标注", True, f"{files_with_rules} 个文件已标注"))

    # 冲突表非空
    conflicts_path = distilled / "reference" / "model-code-conflicts.md"
    if conflicts_path.exists():
        content = conflicts_path.read_text(encoding="utf-8")
        # 检查是否有实际冲突条目（## 或 ## 1. 等）
        conflict_items = re.findall(r"^##\s+\d+\.", content, re.MULTILINE)
        if conflict_items:
            results.append(CheckResult("S2", f"冲突表已登记 ({len(conflict_items)} 条)", True))
        else:
            results.append(CheckResult("S2", "冲突表", True, "已建立（无显式编号条目）"))
    else:
        results.append(CheckResult("S2", "冲突表", False, "model-code-conflicts.md 缺失"))

    # ============================================================
    # S3: Controller 覆盖率
    # ============================================================
    if source and source.exists():
        # 扫描源码中的 @*Mapping 端点
        endpoint_pattern = re.compile(
            r'@(Get|Post|Put|Delete|Request)Mapping\s*\(\s*'
            r'(?:value\s*=\s*)?["\']([^"\']+)["\']',
            re.MULTILINE
        )
        # 也匹配 @RequestMapping("/path") 类级别
        class_pattern = re.compile(
            r'@(?:Rest)?Controller[^@]*?@RequestMapping\s*\(\s*["\']([^"\']+)["\']',
            re.DOTALL
        )

        source_endpoints = set()
        source_controllers = set()
        for ext in (".java", ".kt", ".py", ".ts", ".js", ".go"):
            for f in source.rglob(f"*{ext}"):
                # 跳过构建产物
                if any(part in f.parts for part in ["target", "build", "dist", "node_modules", ".git"]):
                    continue
                try:
                    content = f.read_text(encoding="utf-8")
                except Exception:
                    continue
                # Controller 类
                if "Controller" in f.stem or "@RestController" in content or "@Controller" in content:
                    source_controllers.add(f.stem)
                # 端点
                for m in endpoint_pattern.finditer(content):
                    path = m.group(2)
                    source_endpoints.add(path)

        # 扫描 distilled/api/ 下的端点
        distilled_endpoints = set()
        api_dir = distilled / "api"
        if api_dir.exists():
            for md in api_dir.rglob("*.md"):
                content = md.read_text(encoding="utf-8")
                # 提取文档里的路径（如 POST /api/xxx 或 `/api/xxx`）
                for m in re.finditer(r'["\']?/(?:api|app|redis|testcase|users|redis)[/\w-]*["\']?', content):
                    distilled_endpoints.add(m.group(0).strip("'\""))
                # 也提取 capabilities.json 里的 endpoint
        # capabilities.json endpoints
        cap_path = distilled / "capabilities.json"
        cap_endpoints = set()
        if cap_path.exists():
            try:
                with open(cap_path, "r", encoding="utf-8") as fh:
                    cap = json.load(fh)
                for tool in cap.get("tools", []):
                    ep = tool.get("endpoint", "")
                    if ep:
                        cap_endpoints.add(ep)
            except Exception:
                pass

        total = len(source_endpoints)
        covered = len(distilled_endpoints | cap_endpoints)
        rate = (covered / total * 100) if total > 0 else 0

        if total == 0:
            results.append(CheckResult("S3", "Controller 覆盖率", True, "源码未发现 @*Mapping 端点"))
        elif rate >= 80:
            results.append(CheckResult("S3", f"Controller 覆盖率 {rate:.0f}%", True,
                                       f"{covered}/{total} 端点已覆盖"))
        else:
            # 找缺失的端点
            missing = source_endpoints - (distilled_endpoints | cap_endpoints)
            results.append(CheckResult("S3", f"Controller 覆盖率 {rate:.0f}%", False,
                                       f"{covered}/{total} 端点已覆盖（目标≥80%）",
                                       sorted(missing)[:10]))
    else:
        results.append(CheckResult("S3", "Controller 覆盖率", True, "未传 --source-dir，跳过"))

    # ============================================================
    # S3: capabilities.json 合法性 + tools 数
    # ============================================================
    if cap_path.exists():
        try:
            with open(cap_path, "r", encoding="utf-8") as fh:
                cap = json.load(fh)
            tool_count = len(cap.get("tools", []))
            results.append(CheckResult("S3", f"capabilities.json ({tool_count} tools)", True))

            # 检查每个 tool 有 name + endpoint + guardrails
            incomplete = []
            for t in cap.get("tools", []):
                missing_fields = []
                if not t.get("name"):
                    missing_fields.append("name")
                if not t.get("endpoint"):
                    missing_fields.append("endpoint")
                if not t.get("guardrails", {}).get("access"):
                    missing_fields.append("guardrails.access")
                if missing_fields:
                    incomplete.append(f"{t.get('name','?')}: {','.join(missing_fields)}")
            if incomplete:
                results.append(CheckResult("S3", "tools 字段完整性", False,
                                           f"{len(incomplete)} 个 tool 字段不全", incomplete[:5]))
            else:
                results.append(CheckResult("S3", "tools 字段完整性", True, "全部 tool 字段齐全"))
        except Exception as e:
            results.append(CheckResult("S3", "capabilities.json", False, f"JSON 解析失败: {e}"))
    else:
        results.append(CheckResult("S3", "capabilities.json", False, "文件缺失"))

    # ============================================================
    # S4: 枚举/错误码覆盖
    # ============================================================
    enums_path = distilled / "reference" / "enums.md"
    error_path = distilled / "reference" / "error-codes.md"
    results.append(CheckResult("S4", "enums.md 存在", enums_path.exists(),
                               "OK" if enums_path.exists() else "缺失"))
    results.append(CheckResult("S4", "error-codes.md 存在", error_path.exists(),
                               "OK" if error_path.exists() else "缺失"))

    # Schema 文件
    schema_dir = distilled / "reference" / "schema"
    schema_files = list(schema_dir.glob("*.md")) if schema_dir.exists() else []
    if schema_files:
        results.append(CheckResult("S4", f"Schema 文档 ({len(schema_files)} 个)", True))
    else:
        results.append(CheckResult("S4", "Schema 文档", True, "无（可能无 DDL）"))

    # ============================================================
    # S5: 交叉引用完整性
    # ============================================================
    all_md = list(distilled.rglob("*.md"))
    all_slugs = set()
    broken_refs = []
    for md in all_md:
        content = md.read_text(encoding="utf-8")
        for m in re.finditer(r'\[\[([^\]]+)\]\]', content):
            all_slugs.add(m.group(1))

    # 检查 slug 是否有对应文件
    for slug in all_slugs:
        found = False
        for md in all_md:
            if md.stem == slug or md.name == f"{slug}.md":
                found = True
                break
            # 也检查 slug 是不是文件名的一部分
            if slug in md.name:
                found = True
                break
        if not found:
            broken_refs.append(slug)

    if broken_refs:
        results.append(CheckResult("S5", f"交叉引用 ({len(all_slugs)} 个)", False,
                                   f"{len(broken_refs)} 个断链", sorted(broken_refs)[:5]))
    else:
        results.append(CheckResult("S5", f"交叉引用 ({len(all_slugs)} 个)", True, "全部有效"))

    # 写权限标注
    api_index = distilled / "api" / "_index.md"
    if api_index.exists():
        content = api_index.read_text(encoding="utf-8")
        has_write_perm = "写权限" in content or "controlled-write" in content or "不可逆" in content
        results.append(CheckResult("S5", "写权限标注", has_write_perm,
                                   "已标注" if has_write_perm else "api/_index.md 未标注写权限"))
    else:
        results.append(CheckResult("S5", "写权限标注", False, "api/_index.md 缺失"))

    # ============================================================
    # 护栏: 密钥脱敏
    # ============================================================
    secret_patterns = [
        (r'sk-[a-zA-Z0-9]{20,}', 'API Key (sk-...)'),
        (r'password\s*[:=]\s*["\'][^"\']{4,}["\']', '明文密码'),
        (r'secret\s*[:=]\s*["\'][^"\']{10,}["\']', '明文 secret'),
    ]
    leaked = []
    for f in distilled.rglob("*"):
        if not f.is_file() or f.name == "data.js":
            continue
        try:
            content = f.read_text(encoding="utf-8")
        except Exception:
            continue
        for pattern, label in secret_patterns:
            for m in re.finditer(pattern, content, re.IGNORECASE):
                # 排除脱敏占位
                if "<见" in content[max(0,m.start()-10):m.end()+10]:
                    continue
                leaked.append(f"{f.name}: {label}")

    if leaked:
        results.append(CheckResult("护栏", "密钥脱敏", False,
                                   f"发现 {len(leaked)} 处疑似泄露", leaked[:5]))
    else:
        results.append(CheckResult("护栏", "密钥脱敏", True))

    # ============================================================
    # Step 9/10: 机械文件
    # ============================================================
    for f in ["index.html", "data.js"]:
        p = distilled / f
        if p.exists():
            size = round(p.stat().st_size / 1024, 1)
            results.append(CheckResult("Step9", f"{f} ({size}KB)", True))
        else:
            results.append(CheckResult("Step9", f, False, "缺失"))

    # 根 AGENTS.md
    root_agents = distilled.parent / "AGENTS.md"
    if root_agents.exists():
        content = root_agents.read_text(encoding="utf-8")
        if "蒸馏" in content:
            results.append(CheckResult("Step10", "根 AGENTS.md", True, "已含蒸馏引用"))
        else:
            results.append(CheckResult("Step10", "根 AGENTS.md", False, "存在但无蒸馏引用"))
    else:
        results.append(CheckResult("Step10", "根 AGENTS.md", False, "项目根缺失"))

    # ============================================================
    # 输出报告
    # ============================================================
    print(f"{CYAN}{'='*60}{RESET}")
    print(f"{BOLD}  验证报告{RESET}")
    print(f"{CYAN}{'='*60}{RESET}\n")

    current_stage = ""
    passed = 0
    failed = 0
    warnings = 0

    for r in results:
        if r.stage != current_stage:
            current_stage = r.stage
            print(f"\n{BOLD}  [{r.stage}]{RESET}")

        if r.passed:
            icon = f"{GREEN}✅{RESET}"
            passed += 1
        else:
            icon = f"{RED}❌{RESET}"
            failed += 1

        line = f"    {icon} {r.name}"
        if r.detail:
            line += f" — {r.detail}"
        print(line)

        if r.missing:
            for item in r.missing:
                print(f"       {RED}→ {item}{RESET}")

    # 汇总
    print(f"\n{CYAN}{'='*60}{RESET}")
    total = len(results)
    rate = (passed / total * 100) if total > 0 else 0
    print(f"  {BOLD}汇总: {passed} 通过 / {failed} 失败 / {total} 总计 ({rate:.0f}%){RESET}")

    if failed == 0:
        print(f"  {GREEN}✅ 蒸馏验证全部通过！{RESET}")
    elif rate >= 80:
        print(f"  {YELLOW}⚠️ 蒸馏基本通过，但有 {failed} 项需修复{RESET}")
    else:
        print(f"  {RED}❌ 蒸馏验证未通过！{failed} 项失败，需修复后重跑{RESET}")

    print(f"{CYAN}{'='*60}{RESET}\n")

    # 退出码：全部通过=0，有失败=1
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
