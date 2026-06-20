# <系统名> · AI 能力说明（AGENTS.md）

> 本文件由蒸馏流程自动生成。AI 工具（opencode/codex/claude code）打开本项目时自动读取，即可理解系统能力并生成准确调用命令。

## 系统定位
<!-- <2~3 句：系统是什么、服务谁、核心价值，来自 00-overview.md> -->

## 关键约定
1. **永远通过 API 操作**，不直接读写数据库。
2. **鉴权**：业务接口参数须带 `userId`（缺失返回 `code=222`，需重新登录）。
3. **响应信封**：`{code, message, data}`，`code="000"` 成功。
4. **引用类字段是 ID 不是名称**——先调主数据接口解析。
5. **写权限**：读操作可直接调用；写操作需用户确认后执行。

## 读操作（AI 可直接生成命令）

### 关联方名单
- **分页查询机构**：`POST /app/affiliateList/queryOrgPage`
  ```bash
  curl -X POST http://<host>/app/affiliateList/queryOrgPage \
    -H "Content-Type: application/json" \
    -d '{"userId":"<用户ID>","levelType":"公司层级"}'
  ```
- **分页查询自然人**：`POST /app/affiliateList/queryPersonPage`
- **查看详情**：`POST /app/affiliateList/viewDetail`

### 同业报价撮合
- **撮合匹配**：`POST /app/inter/pageInterMatch`
- **我的报价列表**：`POST /app/inter/findInterMatch`
- **报价公示**：`POST /app/inter/findBringListTable`

### 已生效指令
- **改标校验**：`POST /app/etrbid/checkUpdateBid`
- **改标记录查询**：`POST /app/etrbid/queryUpdateBidDetail`
- **债券详情**：`POST /app/etrbid/selectFinprodInfo`

### 投标汇总
- **重新计算**：`POST /app/quotebid/reCalc`
- **QT 发布对象查询**：`POST /app/qtrade/pullLabelAndUser`

### 报表统计
- **Shibor 曲线**：`POST /app/report/getShiborChart`
- **同业资产占比**：`POST /app/report/getSameChart`
- **资产负债比**：`POST /app/report/chartEquityDebtRatio`

### 用户/会话
- **首页菜单**：`POST /app/user/getMainPageMenu`
- **系统公告**：`POST /app/user/getNoticeList`
- **用户提醒**：`POST /app/user/getRemindList`

### 消息中心
- **消息分页**：`POST /app/message/selectMessage`
- **未读数量**：`POST /app/message/selectMessageNum`

### 任务
- **办理任务**：`POST /app/task/handleTask`（写，需确认）

---

## 写操作（AI 生成命令后需用户确认）

️ **以下操作会修改数据，AI 生成命令后必须请用户确认再执行。**

### 关联方名单
- **新建名单**：`POST /app/affiliateList/save`
  ```bash
  curl -X POST http://<host>/app/affiliateList/save \
    -H "Content-Type: application/json" \
    -d '{"userId":"<用户ID>","levelType":"公司层级","partyType":"机构","partyName":"XX公司","relationship":"公司法人控股股东/实际控制人"}'
  ```
- **修改名单**：`POST /app/affiliateList/update`
- **删除名单**（⚠️不可逆，仅允许日增数据）：`POST /app/affiliateList/delete`
- **退出名单**（⚠️不可逆，置失效）：`POST /app/affiliateList/exit`
- **导入提交**（生成审批任务）：`POST /app/affiliateList/importSubmit`

### 同业报价撮合
- **保存报价**：`POST /app/inter/saveInterMatch`
- **删除报价**（⚠️不可逆）：`POST /app/inter/delInterMatch`

### 已生效指令
- **改标**：`POST /app/etrbid/updateBid`（须先校验通过）
- **撤销指令**（⚠️不可逆）：`POST /app/etrbid/changeStatus`

### 投标汇总
- **汇总确认&发送**：`POST /app/quotebid/sumConfirm`
- **发送报价**：`POST /app/quotebid/send`

### 用户/会话
- **用户登录**：`POST /app/user/login`
- **修改密码**：`POST /app/user/updatePassword`
- **更新公告已读**：`POST /app/user/updateNoticeIsread`

### 消息中心
- **标记已读**（️不可逆）：`POST /app/message/markReaded`

---

## 典型编排（自然语言 → 命令序列）

### "查公司层级的关联机构名单"
```bash
curl -X POST http://<host>/app/affiliateList/queryOrgPage \
  -H "Content-Type: application/json" \
  -d '{"userId":"<用户ID>","levelType":"公司层级"}'
```

### "给关联方 A 录一条名单"
1. 先校验参数（levelType/partyType/relationship 取值见 `reference/enums.md`）
2. 生成保存命令（见上方"新建名单"）
3. **请用户确认后再执行**
4. 执行后检查响应 `code`，非 `000` 则按 `reference/error-codes.md` 解释错误

### "给已生效指令改标"
1. 查产品 SPV：`POST /app/etrbid/selectPrdSpv`
2. 查债券标位明细：`POST /app/etrbid/addBond`
3. 改标校验：`POST /app/etrbid/checkUpdateBid`
4. 若校验通过，生成改标命令：`POST /app/etrbid/updateBid`
5. **请用户确认后再执行**

### "发送投标报价"
1. 查 QT 发布对象：`POST /app/qtrade/pullLabelAndUser`
2. 重新计算：`POST /app/quotebid/reCalc`（回显给用户）
3. 用户确认后，发送：`POST /app/quotebid/send`

---

## 错误处理

| code | 含义 | AI 应如何处理 |
|------|------|---------------|
| 000 | 成功 | 解析 `data`，向用户展示结果 |
| 222 | 用户登录错误 | 提示用户重新登录，不要重试业务接口 |
| 110/010/100 | 网络/服务异常 | 提示"网络异常请稍后重试"；写操作不要自动重试 |
| 001 | 企业微信登录失败 | 提示重新发起企业微信授权 |
| 其它非 000 | 后端业务错误 | 按 `message` 解释；若 `message` 为空，显示"错误码：<code>"，不要臆造原因 |

---

## 详细文档索引

- 系统全景：`00-overview.md`
- 业务术语：`01-glossary.md`
- 领域对象：`domain/_index.md`、`domain/<对象>.md`
- API 详情：`api/_index.md`、`api/<域>/<用例>.md`
- 字段级 Schema：`reference/schema/<表>.md`
- 枚举字典：`reference/enums.md`
- 错误码：`reference/error-codes.md`
- 模型与代码差异：`reference/model-code-conflicts.md`

> 本文件是蒸馏产物的**快速入口**。AI 需要深入理解时，按上方索引读取对应文档。
