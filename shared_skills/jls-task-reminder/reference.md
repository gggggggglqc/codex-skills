# 数据库表结构参考

## jls_core.task（家里事任务表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigint(20) | 主键 |
| task_code | varchar(32) | 任务编码（唯一） |
| dept_id | varchar(50) | 考核部门ID |
| task_content | varchar(5000) | 任务内容（可多行） |
| task_reward | tinyint(4) | 任务奖励 |
| salary_increase_amount | int(11) | 加薪金额 |
| bonus_type | tinyint(4) | 奖金类型 |
| reward_quantity | tinyint(4) | 奖励数量 |
| start_date | datetime | 开始日期 |
| end_date | datetime | 结束日期 |
| acceptance_deadline | datetime | **验收截止日** |
| current_node | tinyint(4) | 当前节点 |
| current_status | tinyint(4) | **当前状态**（1待启动/5进行中/10逾期进行中/15已完成/20已验收/25已驳回/30已归档） |
| current_sub_status | tinyint(4) | 当前子状态 |
| reminder_frequency | int(11) | 提醒频率 |
| type | tinyint(4) | 类型 |
| task_type | tinyint(4) | 任务类型 |
| task_attachments | json | 任务附件 |
| execution_result | varchar(5000) | 执行结果 |
| result_attachments | json | 结果附件 |
| completion_rate | decimal(5,2) | 完成率 |
| review_result | varchar(5000) | 评审结果 |
| publisher | varchar(32) | 发布人工号 |
| reviewer | varchar(32) | 评审人工号 |
| executor | varchar(32) | **执行人工号** |
| acceptance_hrbp | varchar(32) | 验收HRBP工号 |
| acceptor | varchar(32) | 验收人工号 |
| visible_scope | tinyint(4) | 可见范围 |
| project_id | varchar(32) | 项目ID |
| parent_task_code | varchar(32) | 父任务编码 |
| archived | tinyint(4) | 是否归档 |
| create_by | varchar(32) | 创建人 |
| update_by | varchar(32) | 更新人 |
| create_time | timestamp | 创建时间 |
| update_time | timestamp | 更新时间 |

## jls_core.employee（员工基础表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigint(20) | 主键 |
| job_number | varchar(32) | 工号（唯一） |
| employee_name | varchar(255) | 姓名 |
| default_assess_dept_id | varchar(32) | 默认考核部门ID |
| assess_dept_quantity | int(5) | 考核部门数量 |
| status | tinyint(4) | 状态 |

## hris_ads.hris_employee（HR系统员工表）

用于关联组织架构，关键字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| job_number | varchar(32) | 工号 |
| employee_name | varchar(255) | 姓名 |
| dept_id | varchar(32) | 所属部门ID |
| dingding_user_id | varchar(128) | 钉钉用户ID（用于@提醒） |
| phone | varchar(15) | 手机号 |
| status | int(4) | 状态（1=在职，0=离职） |
| deleted | tinyint(1) | 是否删除 |

## hris_ads.hris_department（部门表）

| 字段 | 类型 | 说明 |
|------|------|------|
| dept_id | varchar(32) | 部门ID |
| name | varchar(255) | 部门名称 |
| parent_id | varchar(32) | 上级部门ID |
| level | tinyint(3) | 层级 |
| assess_dept | tinyint(1) | 是否考核部门 |
| dept_path | varchar(2550) | 部门路径 |

## jls_core.employee_assess_dept（员工-考核部门映射）

仅包含 `assess_dept=1` 的考核部门，产品组（393819645）不在此表中，需通过 `hris_employee.dept_id` 关联。

| 字段 | 类型 | 说明 |
|------|------|------|
| job_number | varchar(32) | 工号 |
| dept_id | varchar(32) | 考核部门ID |
