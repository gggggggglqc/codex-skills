---
name: jls-task-reminder
description: 查询和管理 jls-core 家里事任务系统。包括：查询产品组成员的家里事任务状态、设置定时提醒（每日验收截止日任务推送）、按工号/姓名/状态筛选任务、查询个人任务到期时间、查询谁的任务快到期了、@提醒相关成员到钉钉群。当用户提到"家里事"、"任务提醒"、"验收截止日"、"产品组任务"、"jls任务"、"进行中任务查询"、"什么时候到期"、"快到期了"、"任务到期"、"我的任务"时触发。
---

# 家里事定时提醒与任务查询

## 数据库连接

WMS 线上只读账号（jls_core 库）：

| 项目 | 值 |
|------|-----|
| 外网连接 | rr-2ze2z5m8919dglgt1po.mysql.rds.aliyuncs.com |
| 内网连接 | rr-2ze2z5m8919dglgt1.mysql.rds.aliyuncs.com |
| 端口 | 3306 |
| 账号 | wms_query |
| 密码 | ^6u5K2cc4bQW%Rg |
| 数据库 | jls_core（主业务）、hris_ads（组织架构） |

使用 `pymysql` 连接，charset 用 `utf8mb4`。

## 产品组定义

当前产品组为 **信息中心 > 信息一部 > 产品组**，`hris_department.dept_id = 393819645`。

通过以下 SQL 获取在职成员：

```sql
SELECT job_number, employee_name, dingding_user_id, phone
FROM hris_ads.hris_employee
WHERE dept_id = '393819645' AND deleted = 0 AND status = 1
```

## 任务状态码

| 值 | 状态 | 说明 |
|----|------|------|
| 1 | 待启动 | 任务已创建未开始 |
| 5 | 进行中 | 正在执行中 |
| 10 | 逾期进行中 | 已逾期仍在执行 |
| 15 | 已完成 | 执行完毕待验收 |
| 20 | 已验收 | 验收通过 |
| 25 | 已驳回 | 验收不通过 |
| 30 | 已归档 | 已归档 |

## 核心查询场景

### 场景一：今日验收截止日提醒

查询产品组在职成员当日验收截止且进行中的任务：

```sql
SELECT t.executor, he.employee_name, he.dingding_user_id,
       t.task_content, t.current_status, t.acceptance_deadline
FROM task t
JOIN hris_ads.hris_employee he ON he.job_number = t.executor
WHERE he.dept_id = '393819645'
  AND he.deleted = 0
  AND he.status = 1
  AND DATE(t.acceptance_deadline) = CURDATE()
  AND t.current_status IN (5, 10)
ORDER BY t.executor
```

### 场景二：按人查询所有进行中任务

```sql
SELECT t.task_code, t.task_content, t.current_status,
       t.acceptance_deadline, t.start_date, t.end_date
FROM task t
WHERE t.executor = '{job_number}'
  AND t.current_status IN (1, 5, 10)
ORDER BY t.acceptance_deadline
```

### 场景三：按状态统计产品组任务

```sql
SELECT he.employee_name, t.current_status, COUNT(*) as cnt
FROM task t
JOIN hris_ads.hris_employee he ON he.job_number = t.executor
WHERE he.dept_id = '393819645'
  AND he.deleted = 0
  AND he.status = 1
  AND t.current_status IN (5, 10)
GROUP BY he.employee_name, t.current_status
ORDER BY he.employee_name
```

### 场景四：我的任务什么时候到期

当有人问"我的家里事什么时候到期"时触发。需要知道提问者的工号（从钉钉发送者信息或用户告知获取）。

```sql
SELECT t.task_code, t.task_content, t.current_status,
       t.acceptance_deadline, t.start_date, t.end_date,
       DATEDIFF(t.acceptance_deadline, CURDATE()) as days_remaining
FROM task t
WHERE t.executor = '{job_number}'
  AND t.current_status IN (1, 5, 10)
ORDER BY t.acceptance_deadline
```

输出格式：
```
【刘庆晨 的进行中任务】
1. Fms-v6.4财务5月结账优化项需求评审
   截止日：2026-06-30（剩余18天）| 状态：进行中
```

**识别提问者身份**：
- 钉钉群聊中：从消息发送者的钉钉信息获取姓名，再通过 `hris_employee` 匹配工号
- 直接对话：询问用户工号或姓名

### 场景五：谁的任务快到期了

当有人问"谁的家里事快到期了"时触发。默认查未来3天内到期的任务。

```sql
SELECT t.executor, he.employee_name, he.dingding_user_id,
       t.task_content, t.current_status, t.acceptance_deadline,
       DATEDIFF(t.acceptance_deadline, CURDATE()) as days_remaining
FROM task t
JOIN hris_ads.hris_employee he ON he.job_number = t.executor
WHERE he.dept_id = '393819645'
  AND he.deleted = 0
  AND he.status = 1
  AND t.acceptance_deadline >= CURDATE()
  AND t.acceptance_deadline <= DATE_ADD(CURDATE(), INTERVAL 3 DAY)
  AND t.current_status IN (5, 10)
ORDER BY t.acceptance_deadline, t.executor
```

用户可指定天数，如"7天内到期的任务"则改为 `INTERVAL 7 DAY`。

输出格式：
```
【产品组近三日要到期任务提醒】
6月15日（3天后）：
  工号：11723  刘庆晨 @刘庆晨
    - Fms-v6.4财务5月结账优化项需求评审（进行中）
  工号：26695  文秋红 @文秋红
    - T+1进项税额取值和多维报表导入优化（进行中）
```

## 输出格式

按 **工号、姓名、任务名称** 组织输出：

```
【家里事提醒】今日验收截止日任务：

工号：11723  姓名：刘庆晨 @刘庆晨
  - Fms-v6.4财务5月结账优化项需求评审（进行中）

工号：26695  姓名：文秋红 @文秋红
  - T+1进项税额取值和多维报表导入优化（逾期进行中）
```

- 任务名称取 `task_content` 第一行前50个字符
- 发送时 @ 有任务的成员（使用 `dingding_user_id`）
- 无匹配任务时发送简短提示即可

## 定时提醒配置

定时任务已配置（任务名：产品组家里事每日提醒）：

| 项目 | 值 |
|------|-----|
| 频率 | 每天早上 9:00 |
| 时区 | Asia/Shanghai |
| 目标群 | 钉钉「产品组」群 |
| 漏执行策略 | skip（跳过） |

如需修改定时任务，使用 `qoder_cron` 工具，taskId 通过 `qoder_cron list` 查询。

## 查询脚本

执行 `scripts/query_tasks.py` 支持多种查询模式：

```bash
# 今日验收截止日提醒（默认）
python3 scripts/query_tasks.py

# 指定日期查询
python3 scripts/query_tasks.py --date 2026-06-15

# 查询某人的所有进行中任务及到期时间
python3 scripts/query_tasks.py --mode my-tasks --executor 11723

# 查询近三日快到期的任务（默认）
python3 scripts/query_tasks.py --mode expiring

# 自定义天数，如未来7天
python3 scripts/query_tasks.py --mode expiring --days 7

# 按状态筛选
python3 scripts/query_tasks.py --status 5,10
```

输出 JSON 格式，包含 `has_tasks`、`message`、`mentions` 等字段。

## 数据库表结构

详见 [reference.md](reference.md) 获取完整的表结构说明。
