# distill-system-skills

> 将业务系统/老系统逆向蒸馏为 AI 可理解、可调用的领域能力文档 + function-calling 能力包。

## 这是什么

一套可被 AI 编码助手（opencode / Codex / Claude Code）直接加载的 **Skill**，用于把现有业务系统蒸馏为一套结构化的 `distilled/` 文档 + `capabilities.json` 能力包。AI 据此能用自然语言操作业务，**只通过 API、不直接访问数据库**。

源自《AI 大模型逆向工程-将 IT 业务系统蒸馏为独立的 Skills 技能包》方法论手册。

## 解决什么问题

```
老系统（代码即真相，文档过期/缺失）
        │ 蒸馏
        ▼
distilled/                    capabilities.json
├── 00-overview.md            ├── 35+ 工具定义
├── 01-glossary.md            ├── guardrails（读/写/不可逆）
├── domain/                   └── OpenAI function-calling 兼容
├── api/
├── reference/
├── AGENTS.md  ← AI 编码助手自动读取
├── index.html ← 双击即用的查看器+对话客户端
└── data.js    ← 内嵌全部文档+大模型配置
```

AI 工具打开项目即理解系统能力，无需翻代码。

## 快速开始

### 安装

将本 Skill 复制到 opencode 的 skills 目录：

```bash
# 全局（所有项目可用）
cp -r distill-system-skills ~/.config/opencode/skills/

# 项目级（仅当前项目）
cp -r distill-system-skills .joyincode/skills/
```

### 使用

在 opencode / Codex / Claude Code 中说：

> "把 `E:\xxx\my-project` 蒸馏一下"

AI 会自动触发本 Skill，按 S0→S6 七阶段流程产出 `distilled/` 目录。

### 蒸馏完成后

| 入口 | 方式 | 适合 |
|------|------|------|
| `distilled/index.html` | 双击打开 | 可视化查看 + 自然语言对话 |
| `distilled/AGENTS.md` | AI 编码助手自动读取 | 编码时理解系统能力 |
| `distilled/capabilities.json` | 注册为 function-calling 工具 | AI 直接调用 API |
| `项目根/AGENTS.md` | opencode 自动加载 | 让 AI 发现蒸馏产物 |

## 目录结构

```
distill-system-skills/
├── SKILL.md                    # 入口：触发条件 + 核心护栏 + S0-S6 工作流
├── reference/                  # 规范文档（按需加载）
│   ├── principles.md           #   六条设计原则
│   ├── stages.md               #   S0-S6 七阶段（产出/检查点 + 迭代回路）
│   ├── fact-priority.md        #   事实优先级 + 冲突登记 + 降级策略
│   ├── conventions.md          #   命名/粒度/交叉引用/规则执行方标注
│   └── verification.md         #   质量验收：静态清单 + 实跑测试集
├── templates/                   # 文件模板（套用即填）
│   ├── README.md               #   distilled/ 入口
│   ├── 00-overview.md          #   系统全景
│   ├── 01-glossary.md          #   术语表
│   ├── AGENTS.md               #   AI 快捷入口（curl 示例）
│   ├── data.js                 #   查看器自动加载文件
│   ├── domain-_index.md        #   领域对象总览
│   ├── domain-object.md        #   单个领域对象
│   ├── api-_index.md           #   API 能力清单
│   ├── api-usecase.md          #   单个用例接口
│   ├── schema-table.md         #   字段级 Schema
│   ├── enums.md                #   枚举/字典
│   ├── error-codes.md          #   错误码
│   ├── model-code-conflicts.md #   代码/需求差异
│   └── requirements-_index.md  #   原始需求
└── assets/
    └── viewer.html             # 蒸馏文档查看器+对话客户端
```

## 核心护栏

蒸馏过程中始终遵守：

1. **以代码为准** — 实际行为以源代码为准，不臆测
2. **AI 只通过 API** — 不直接读写数据库
3. **引用字段是 ID** — 先解析，不用名称
4. **服务端权威字段** — 不可由调用方设置
5. **写权限分级** — 前期只读，写需确认，不可逆强制二次确认
6. **规则标注执行方** — 服务端强制/服务端维护/调用方需预判/副作用
7. **冲突不静默** — 一律登记冲突表
8. **密钥脱敏** — 配置中的密码/token/secret 必须打码

## 七阶段流程

```
S0 盘点 → S1 对象 → S2 规则 → S3 API → S4 明细 → S5 编排 → S6 验证
                         ▲__________________________________|
                                （发现缺口则迭代）
```

| 阶段 | 产出 | 检查点 |
|------|------|--------|
| S0 盘点 | 资料盘点表（经用户确认） | 资料齐全度 + 事实优先级 |
| S1 对象 | 00-overview / domain/ | 每对象一句话定义 + 关系图自洽 |
| S2 规则 | 规则段 + 冲突表 | 每条规则有执行方标注 |
| S3 API | api/_index + api/<域>/ | 每用例回答"场景/输入/输出/规则/错误" |
| S4 明细 | schema/ enums error-codes | API 出现的枚举/错误码都能查到 |
| S5 编排 | api/_index 编排 + README + capabilities.json + index.html + data.js + 根 AGENTS.md | 链接可追溯 |
| S6 验证 | 验证结论 | 读/写/统计/规则反例四类场景通过 |

## 文件过滤规则

| 类别 | 处理 | 文件 |
|------|------|------|
| **跳过** | 不读 | `target/` `*.class` `*.jar` `logs/` `.git/` |
| **读但需转换** | 转换后读，**绝不跳过** | `.docx` `.xlsx` `.pdf`（先找 skill → 找远程市场 → 自行安装） |
| **读但脱敏** | 读结构，值打码 | `.yml` `.properties`（密码/token → `<见配置文件>`） |
| **正常读** | 直接读 | `.java` `.py` `.ts` `.sql` `.md` `.xml` |

## 收尾强制门

声称"蒸馏完成"之前，必须验证以下文件全部存在：

- `distilled/capabilities.json`
- `distilled/index.html`
- `distilled/data.js`
- 项目根 `AGENTS.md`

**缺任何一个都不算完成。**

## 产出三层架构（渐进式披露）

```
distilled/
├── 【L1 元数据 — 常驻索引】         ← opencode/codex 自动读取
│   └── 00-overview.md
├── 【L2 语义层 — 激活时载入】       ← AI 理解业务对象和 API 清单
│   ├── 01-glossary.md
│   ├── domain/
│   └── api/_index.md
├── 【L3 明细层 — 按需检索(RAG)】    ← AI 需要时才取，不占常驻上下文
│   ├── api/<域>/<用例>.md
│   └── reference/
└── capabilities.json               ← function-calling 工具集
```

## AI Agent 使用模式（ReAct 循环）

```
用户："买入 101010 1000万 T+0 利率2.5%"
  │
  ▼
① 理解意图（L2 语义层）
② 规划：还缺什么？要做什么？
③ 取 L3 明细（api/<用例>.md / enums / error-codes）
④ 工具调用（capabilities.json 注册的工具）
⑤ 观察结果 → 应答用户
```

## 技术栈

- 适用于任何语言/框架的业务系统（Java/Python/Go/Node.js...）
- 产出为标准 Markdown + JSON，不依赖特定运行时
- 查看器为单文件 HTML，无需后端，双击即用
- 兼容 OpenAI function-calling 格式

## License

MIT
