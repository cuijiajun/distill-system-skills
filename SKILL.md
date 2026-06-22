---
name: distill-system-skills
description: Use when reverse-engineering / 蒸馏 / 逆向工程 / 解析 / 理解 an existing business system or legacy codebase (老系统/业务系统) to turn it into an AI-consumable capability package — a distilled/ Markdown knowledge base (semantic/capability/detail layers) plus an OpenAI function-calling compatible capabilities.json. Use when the user wants to 把系统蒸馏为Skills技能包/领域能力中心, prepare a system for AI coding assistants / RAG / function-calling, or produce AI-readable system docs (对象/规则/API/Schema/枚举/错误码). 关键词：蒸馏、逆向、解析老系统、理解业务系统、领域模型、能力中心。
---

# distill-system-skills

## 这是什么
把一个面向人使用的业务系统/老系统，逆向蒸馏为一套 AI 可理解、可调用的领域能力文档（`distilled/`），并额外生成一份 **OpenAI function-calling 兼容**的能力清单 `capabilities.json`。AI 据此能用自然语言操作业务（录单/查单/统计），**只通过 API、不直接访问数据库**。

源自《AI 大模型逆向工程-将 IT 业务系统蒸馏为独立的 Skills 技能包》。理念、流程、模板均忠实于该手册。

## AI Agent 使用模式（ReAct 循环）
蒸馏产物喂给 AI Agent（大模型 + 工具调用），按 **理解→规划→取明细→工具调用→观察** 循环工作：
1. **理解意图**：依据 L2 语义层（00-overview / domain/ / api/_index）理解用户自然语言意图
2. **规划**：还缺信息？要做什么动作？→ 决定取 L3 明细还是直接调用工具
3. **取 L3 明细**：按需检索 `api/<用例>.md` / `reference/schema/` / `enums.md` / `error-codes.md`
4. **工具调用**：按 `capabilities.json` 注册的工具调用真实 API（写操作受 guardrails 约束）
5. **观察结果**：成功 → 应答用户；失败 → 按 `error-codes.md` 解释/重试/请求用户确认

## 何时用
- 要把老系统/业务系统"解析、理解、蒸馏"成 AI 可用文档或技能包
- 为 AI 编码助手 / RAG / function-calling 准备系统的语义底座
- 用户说：蒸馏、逆向工程、解析老系统、理解业务系统、做 Skills 技能包、把系统下沉为能力中心

## 核心护栏（始终遵守，违反即蒸馏失败）
1. **以代码为准**：实际行为以源代码 + 数据库约束为准，不臆测；与需求/本体冲突时照实写代码行为，并登记到 `model-code-conflicts.md`
2. **AI 只通过 API 操作**，不直接读写数据库
3. **引用类字段是 ID 不是名称**——先调主数据接口解析
4. **服务端权威字段**（累计金额、状态等）由系统计算/维护，调用方不可设置
5. **写权限分级**：前期只开放读；写操作受控/需确认；不可逆操作强制二次确认
6. **每条规则标注执行方**：【服务端强制】/【服务端维护】/【调用方需预判】/【副作用】
7. **冲突不静默选择**——一律登记冲突表
8. **密钥脱敏**：配置中的密码、token、secret、私钥等敏感值**必须脱敏**再写入 distilled/（如 `<见 application-prod.yml>`），**绝不**把真实凭据写进文档。配置的**结构/字段名**要记录，但**值**要打码

## 工作流（自主一次性模式）
**输入**：仓库根路径（默认当前工作目录）+ 可选 `distill-input.yaml` 资料清单。

按设计图 **S0 → S6** 七阶段推进，**S2–S5 可迭代往返**（发现缺口则回到 S2–S5 修复）：

- **S0 盘点**（资料 + 优先级）：Glob 仓库树（**先过滤，见下方文件过滤规则**）；按清单/约定定位 源码服务层、路由层、**配置类/集成点**、DB schema、需求、本体；自动填写资料盘点表（见 `fact-priority.md`）；**填完后用交互式问题（question 工具）呈现盘点表给用户确认**，不要用纯文本消息。**产出**：资料盘点表（经用户确认）；一段话的系统定位。
- **S1 对象**（对象 + 关系）：从 路由层→服务层→DB→需求→本体 归纳领域对象、关系、生命周期、状态机；划清系统边界。**产出**：`00-overview.md` 初稿、`domain/_index.md`、各 `domain/<对象>.md` 初稿。**检查点**：每个对象能用一句话定义；关系图自洽。
- **S2 规则**（规则 + 冲突）：从服务层抽取强制规则（校验、状态流转、自动计算），标注执行方；与本体比对登记冲突。**产出**：各对象文档的"核心业务规则"段；`reference/model-code-conflicts.md`。**检查点**：每条规则都有执行方标注；冲突已登记。
- **S3 API**（用例级接口）：从需求业务动作出发，对照路由层确认真实接口（方法+路径+入参+出参）；用例级粒度（剥离 UI 态字段）。**产出**：`api/_index.md`、各 `api/<域>/<用例>.md`。**检查点**：每个用例能回答"场景/输入/输出/规则/错误"。
- **S4 明细**（Schema + 枚举）：字段级 schema、枚举、错误码、统一响应信封。**产出**：`reference/schema/*.md`、`reference/enums.md`、`reference/error-codes.md`。**检查点**：API 文档出现的每个枚举/错误码，明细层都能查到。
- **S5 编排**（引用 + 编排）：用 `[[slug]]` 把对象↔接口↔Schema 串起来；在 `api/_index.md` 写"自然语言意图 → 接口序列"的典型编排；标注每个写接口的"写权限分级"。**产出**：完善后的 `api/_index.md`、`README.md`、`requirements/_index.md`。**检查点**：能顺着链接从"用户想做的事"走到"该调哪些接口"。
- **S6 验证**（实跑 + 迭代）：见 `reference/verification.md` 静态清单 + 动态验证。**产出**：验证记录 / 结论。**检查点**：典型读、写、统计、规则反例场景全部通过。

> **迭代回路**：S6 或 S2–S5 任何阶段发现缺口 → 回到 S2–S5 修复 → 重新验证。
> 每阶段详细产出/检查点见 `reference/stages.md`。

8. **收尾脚本（step 8+9+10 合并执行，必须运行）**：
   生成完所有 distilled/*.md 文件后，**立即运行**收尾脚本（一步完成 capabilities.json 检查 + index.html 拷贝 + data.js 生成 + 根 AGENTS.md 创建 + 自检）：
   ```bash
   python scripts/distill-finalize.py --distilled-dir <项目>/distilled
   # Mac/Linux 可能需要 python3
   python3 scripts/distill-finalize.py --distilled-dir <项目>/distilled
   ```
   **不运行此脚本不算蒸馏完成。** 脚本会自检并打印 ✅/❌ 清单。

**读取优先级（可信度，裁决冲突时用）**：路由层 = 服务层 ＞ DB 约束 ＞ 本体 ＞ 需求文档

**文件过滤规则（S0 扫描前必读）**：
- **跳过（无语义/构建产物/二进制/日志）**：`target/`、`build/`、`dist/`、`node_modules/`、`.git/`、`logs/`、`*.class`、`*.jar`、`*.war`、`*.zip`、`*.log`、`*.lock`、`.idea/`、`.settings/`、`*.iml`
- **读但需转换（文档类，绝不跳过！）**：`*.docx`、`*.doc`、`*.xlsx`、`*.xls`、`*.pptx`、`*.pdf`——这些是**需求文档/业务文档的高价值来源**，绝不能写"无法读取"然后跳过。处理规则（按顺序尝试，直到成功读取）：
  1. **先找本机 skills**：检查 `~/.config/opencode/skills/` 和项目级 `.joyincode/skills/`（或 `.opencode/skills/`）下是否有文档处理相关 skill（如 `docx`/`office`/`pptx` 等），有则加载并使用
  2. **找远程 skill 市场**：若本机没有，访问 `http://192.168.90.238:8091/airesource/skillmarket/-/tree/main/skills` 查找并下载安装对应的文档处理 skill
  3. **自行安装依赖**：若远程也没有，自行安装（如 `py -m pip install python-docx openpyxl pdfplumber`），安装后提取文本
  4. **兜底**：`.docx`/`.xlsx` 本质是 ZIP，可解压后直接解析 `word/document.xml` 或 `xl/sharedStrings.xml`
- **读但脱敏（配置类，含密钥）**：`*.yml`、`*.yaml`、`*.properties`、`*.conf`——**读结构/字段名**，但密码/token/secret/密钥的**值必须打码**（如 `<见 application-prod.yml>`），**绝不**把真实凭据写进 distilled/
- **正常读（源码）**：`*.java`、`*.py`、`*.ts`、`*.js`、`*.go`、`*.sql`、`*.md`、`*.xml`（pom 等）
- **尊重 .gitignore 但不完全依赖**：`.gitignore` 排除的构建产物要跳过；但配置文件（`application-*.yml`）即使被 gitignore 也要读（脱敏后），因为它们是集成点的真相来源

**读取覆盖面（必读，防漏，与可信度无关——漏读=蒸馏必然有缺口）**：
- **配置类与集成点**（最易漏）：`@ConfigurationProperties`/`@Value`/`*Properties.java`/`*.yml`/`*.properties`——暴露外部依赖（OAuth、第三方回调、上游地址、密钥、第三方 SDK）。**网关/中间层/集成类项目此项最优先读**。扫描清单里看到却跳过=执行失误
- **第三方回调与外部链路**：OAuth 回调、webhook、上游免密登录等入口——**必须单独建 domain 文档**，不与普通 CRUD 混在一起；逐个标注其外部依赖与触发条件
- **读完 controller 清单后反向核对**：①每个外部集成点是否都有对应 domain/api 文档 ②每个配置项（corpid/secret/上游URL…）是否都追溯到用途 ③"代码读到一半的歧义"（如两种 token 来源）是否已对照分析，不要留半句

## 资料输入形式
- **仓库根路径**（默认当前工作目录）
- **可选 `distill-input.yaml`**（资料清单）：

```yaml
repo: .
source:
  services: backend/services   # 业务规则真相来源
  routes: backend/routes      # API 清单真相来源
database:
  schema: db/schema.sql       # 或目录
requirements: docs/需求.md
ontology: models/**/*.yaml    # 可选
notes: 仅代码可信，需求已过期
```

不提供清单也能跑——用 Glob 自动扫描识别常见源码/DB/文档目录。**但 S0 扫描后必须把自动填写的资料盘点表呈现给用户确认**，不能默默跳过。资料不全可降级（见 `reference/fact-priority.md`）。

## 目录结构（产出）——渐进式披露（L1/L2/L3）
`distilled/` 放在被解析系统的仓库根目录：

```
distilled/
├── README.md                       # 入口：阅读顺序/加载策略/写权限提醒
├── AGENTS.md                       # AI 工具直接读取的快捷入口（curl 命令 + 编排示例）
├── index.html                      # 蒸馏文档查看器+领域对话客户端（双击即用，无需配置）
├── capabilities.json               # function-calling 能力包
│
├── 【L1 元数据 — 常驻索引】
│   └── 00-overview.md              # 系统全景 + 给 AI 的关键约定（常驻）
│
├── 【L2 语义层 — 激活时载入上下文】← S0·S1
│   ├── 01-glossary.md              # 业务术语表
│   ├── domain/                     # 领域对象（建议常驻给 AI）
│   │   ├── _index.md               # 对象关系总览（文字版关系图）
│   │   └── <对象>.md                # 一个核心对象一个文件
│   └── api/_index.md               # 能力清单 + 典型编排
│
├── 【L3 明细层 — 按需检索(RAG)，不常驻上下文】← S4·S2
│   ├── api/<域>/<用例>.md          # 业务用例级接口（场景/输入/输出/规则/错误/示例/写权限分级）
│   ├── reference/
│   │   ├── schema/<表>.md          # 字段级 Schema
│   │   ├── enums.md                # 全部枚举/字典值
│   │   ├── error-codes.md          # 错误码与统一响应
│   │   └── model-code-conflicts.md # ⚠️ 本体/需求 ↔ 代码 差异清单
│   └── requirements/_index.md      # 原始需求（可追溯）
```

## capabilities.json（能力包，OpenAI function-calling 兼容）
每个用例级 API 编译为一个工具条目：

```json
{
  "name": "create_contract",
  "description": "录入一份生效销售合同及付款条款，触发收款预算重算。<场景/边界>",
  "method": "POST",
  "endpoint": "/api/behaviors/Contract_Create/execute",
  "guardrails": {
    "access": "controlled-write",
    "requires_confirmation": true,
    "irreversible": false,
    "dry_run_supported": true
  },
  "parameters": {
    "type": "object",
    "properties": { "contractNo": { "type": "string", "description": "合同编号，唯一" } },
    "required": ["contractNo", "totalAmount", "paymentTerms"]
  }
}
```

字段/参数必须与代码实际入参出参**逐字段核对**（不可臆测）。`guardrails.access` 取值：`read-only` / `controlled-write` / `disabled`。

## 关键约定（详见 reference/conventions.md）
- 文件名小写 kebab-case；API 字段沿用代码实际命名（通常 camelCase）；枚举用业务实际值（含中文）
- 一个领域对象一个文件；一个业务用例一个文件；接口粒度按业务动作不按 CRUD
- 交叉引用一律 `[[slug]]`（slug=文件名不含 .md）；对象↔接口↔Schema 三者互链
- 规则执行方标注是强制的

## 参考（按需读）
- `reference/principles.md` — 六条设计原则（核心，建议常驻）
- `reference/stages.md` — S0-S6 七阶段流程（每阶段产出/检查点 + 迭代回路）
- `reference/fact-priority.md` — 事实优先级、冲突登记、资料不全降级策略
- `reference/conventions.md` — 命名/粒度/交叉引用/规则执行方标注规范
- `reference/verification.md` — 质量验收：静态清单 + 实跑测试集
- `templates/` — 13 个文件模板（含 AGENTS.md），套用即填

## 常见错误
- 把需求/Schema/API 全塞一个上万行文件 → 塞不进上下文。**必须分层**
- 接口粒度太细（CRUD）或太粗（照搬前端复合接口，夹带 UI 态字段）→ **必须用例级**
- 规则不标注执行方 → AI 过度兜底或误以为服务端会拦
- 静默选择冲突版本（需求说 A、代码做 B 时悄悄选一个）→ **必须登记冲突表**
- `capabilities.json` 用臆测字段/编造错误消息 → **必须与代码实际行为逐项核对**
- **漏读配置类/集成点**（`*Properties.java`/`*.yml`/OAuth 回调/上游地址）→ 外部接入回答不全，这是蒸馏最常见的缺口根因。**扫描时看到的小配置文件不要因为"省上下文"跳过**——它们往往是外部接入的答案所在
- 外部集成点（OAuth/webhook/第三方）和普通 CRUD 混在一个 domain 文件里 → **必须单独成文**，标注外部依赖与触发条件
