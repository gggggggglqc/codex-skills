---
name: jls-task-dingtalk-reminder
description: 查询 jls-core 家里事任务系统中今日验收截止的任务，并将提醒消息发送到钉钉「产品组」群聊，自动 @ 相关成员。当用户要求发送家里事提醒、任务截止提醒、钉钉群任务通知、今日任务提醒、家里事 @提醒 时触发。与 jls-task-reminder 的区别：本 skill 专注于「查询 + 钉钉群聊发送」的完整闭环操作。
---

# 家里事任务钉钉群聊提醒

## 触发场景

- 发送家里事提醒到钉钉群
- 今日验收截止日任务提醒
- 产品组任务 @提醒
- 家里事钉钉通知

## 数据库连接

本 skill 不保存任何真实数据库凭据。脚本统一从本地 profile 读取：

- 默认 profile：`DB_PROFILE=wms-mysql`
- profile 文件：`~/.config/db-profiles/wms-mysql.env`
- 默认数据库：`jls_core`
- charset：`utf8mb4`

执行前可先检查 profile：

```bash
python3 ~/.codex/skills/database-config/scripts/load_db_profile.py --profile wms-mysql
```

如需临时切换连接信息，只允许通过本地环境变量覆盖，不得把账号密码写回 skill。

产品组 dept_id 为 `393819645`（信息中心 > 信息一部 > 产品组）。

## 核心查询 SQL

查询今日验收截止且状态为「进行中」或「逾期进行中」的任务：

```sql
SELECT t.executor, he.employee_name, he.dingding_user_id,
       t.task_content, t.current_status
FROM task t
JOIN hris_ads.hris_employee he ON he.job_number = t.executor
WHERE he.dept_id = '393819645'
  AND he.deleted = 0
  AND he.status = 1
  AND DATE(t.acceptance_deadline) = CURDATE()
  AND t.current_status IN (5, 10)
ORDER BY t.executor
```

任务状态码：5=进行中，10=逾期进行中。

## 执行流程

### Step 1：执行查询

使用脚本查询并生成消息：

```bash
python3 scripts/remind.py
```

输出 JSON 字段：
- `has_tasks`: true/false
- `message`: 格式化后的提醒文本
- `mentions`: 需要 @ 的成员列表（含 `dingding_user_id`）

### Step 2：搜索钉钉群聊

获取「产品组」群的 openConversationId：

```bash
dws chat search --keyword "产品组" --format json
```

从返回中提取 `openConversationId`。

### Step 3：发送群消息

**无任务时**（`has_tasks=false`）：

```bash
dws chat message send \
  --group <openConversationId> \
  --title "家里事提醒" \
  --text "今日产品组无验收截止日在进行中/逾期进行中的家里事任务" \
  --format json
```

**有任务时**（`has_tasks=true`）：

```bash
dws chat message send \
  --group <openConversationId> \
  --title "家里事提醒" \
  --text $'消息内容，含 <@dingding_user_id> 占位符' \
  --at-users <dingding_user_id1>,<dingding_user_id2> \
  --format json
```

**关键要求**：
- `--text` 中必须包含 `<@dingding_user_id>` 占位符，否则 @ 不生效
- `--at-users` 传 `dingding_user_id` 列表，逗号分隔
- `--title` 必填
- 多行文本使用真实换行符（`$'...\n...'`），Markdown 段落间需空行

### 消息格式示例

```
【家里事提醒】今日验收截止日任务：

工号：15281  姓名：朱琳 <@154190878>
  - WMS V3.9.2 PDA新增返厂登记、已打印取消单登记等需求输出完成（进行中）
```

## 完整示例

假设脚本输出：
- `message`: 格式化提醒文本
- `mentions`: `[{"name":"朱琳","dingding_user_id":"154190878"}]`

执行：

```bash
# 1. 查群 ID
dws chat search --keyword "产品组" --format json
# -> openConversationId: cidt3+nZ0dN6aGfYPlVanJhSA==

# 2. 发送消息（有任务时）
dws chat message send \
  --group "cidt3+nZ0dN6aGfYPlVanJhSA==" \
  --title "家里事提醒" \
  --text $'【家里事提醒】今日验收截止日任务：\n\n工号：15281  姓名：朱琳 <@154190878>\n  - WMS V3.9.2 PDA新增返厂登记、已打印取消单登记等需求输出完成（进行中）' \
  --at-users 154190878 \
  --format json
```

## 定时任务

如需每日自动执行，通过 QoderWork 定时任务配置：
- 执行上述「Step 1 查询」+「Step 2-3 发送」流程
- 推荐时间：每天早上 9:00
- 时区：Asia/Shanghai
