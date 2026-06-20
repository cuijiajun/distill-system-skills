# <系统名> · 蒸馏文档（AI 能力说明书）

本目录把 <系统名> 蒸馏为一套 AI 可理解、可调用的领域能力说明。
AI 仅通过 API 操作业务，**不直接访问数据库**。

## 阅读顺序 / 加载策略
**语义层（建议常驻加载给 AI）：**
1. `00-overview.md` — 系统全景与给 AI 的约定
2. `01-glossary.md` — 业务术语
3. `domain/` — 领域对象
4. `api/_index.md` — API 能力清单与典型编排

**明细层（按需检索）：**
- `api/` — 各业务用例接口详情
- `reference/schema/` — 字段级 Schema
- `reference/enums.md` / `reference/error-codes.md`
- `reference/model-code-conflicts.md` — ⚠️ 重要：模型与代码差异

**能力包：** `capabilities.json`（function-calling 工具集）

**来源：** `requirements/_index.md`

## 目录结构
<!-- <贴出本系统的目录树> -->

## 关键提醒（写操作权限）
<!-- <前期只读/写需确认/不可逆操作说明> -->

> 本文件由 distill-legacy-system skill 生成，可按需修改。
