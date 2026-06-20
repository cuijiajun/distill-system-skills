# 命名、粒度、交叉引用、规则执行方标注规范

## 7.1 规则执行方标注（强制）
每条规则必须带以下标签之一/多个：

| 标签 | 含义 | AI 用法 |
|---|---|---|
| **【服务端强制】** | 违反被接口拒绝 | 预判并向用户解释 |
| **【服务端维护】** | 系统自动计算/更新，调用方不可设置 | 不要传入这些字段 |
| **【调用方需预判】** | 服务端不拦，但业务要求 | AI 调用前自行判断或与用户确认 |
| **【副作用】** | 该动作触发的连锁（事件、重算等） | 提醒用户后续影响 |

## 7.2 交叉引用
- 一律用 `[[slug]]`，slug = 目标文件名（不含 `.md`）。
- 链接到尚不存在的文件**允许**——它标记"待补"，不是错误。
- 对象 ↔ 接口 ↔ Schema 三者之间**互相链接**，形成可追溯网。

例：`domain/contract.md` 里 `[[create-contract]]` 指向 `api/contract/create-contract.md`；`[[schema-contracts]]` 指向 `reference/schema/contracts.md`。

## 7.3 命名
- **文件名**：小写 kebab-case（如 `create-contract.md`）。
- **领域对象文件名** = 对象英文别名（如 `contract.md`）。
- **API 文件名** = 用例动作（如 `create-contract.md`、`query-contracts.md`）。
- **API 字段**：沿用代码实际返回的命名（通常 camelCase），**不要自创**。
- **枚举值**：用业务实际值（含中文），**不要翻译**。

## 7.4 粒度
- 一个**领域对象**一个文件；一个**业务用例**一个文件。
- 接口粒度按**业务动作**，不按表的 CRUD。
- 太细（CRUD 级 `insertOrderItem`）❌；太粗（照搬前端复合接口）❌；用例级 ✅。

## 7.5 "实际为准"
- 入参 / 出参 / 错误消息以**代码实际行为**为准，逐一核对，**不臆测**。
- 与需求/本体不一致的，照实写代码行为，并登记到冲突表。
- `capabilities.json` 的参数 schema 同样必须与代码实际入参逐字段对齐。

## slug 命名建议（保持目录与引用一致）
| 文件 | slug |
|---|---|
| `domain/contract.md` | `contract` |
| `api/contract/create-contract.md` | `create-contract` |
| `reference/schema/contracts.md` | `schema-contracts`（避免与对象 slug 冲突，加前缀） |
| `reference/enums.md` | `enums` |
| `reference/error-codes.md` | `error-codes` |
| `reference/model-code-conflicts.md` | `model-code-conflicts` |

> slug 冲突时（如对象名与 schema 表名相同），schema 文件 slug 加 `schema-` 前缀区分。
