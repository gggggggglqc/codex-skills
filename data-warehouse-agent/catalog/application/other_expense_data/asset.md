---
asset_id: app.other_expense_data
layer: APP
table_name: other_expense_data
database: tmp_data
business_name: 净利核算—其他费用数据表
status: 已确认
refresh: { frequency: 按需上传, timezone: Asia/Shanghai, load_window: 按 month 月度, load_strategy: 先删除对应月份数据后写入（覆盖式上传） }
grain: 月份 + 货主 + 店铺 + 仓库 + 费用类型
primary_key: [month, owner_code, shop_code, warehouse_code, cost_type]
partition: { field: month, semantic: 上传当月第一天, example: '2024-05-01', strategy: DDL 未声明 PARTITION BY }
distribution: HASH(month, owner_code)，BUCKETS 3
source_evidence:
  - { type: warehouse_ddl, path: 用户于会话中提供的 CREATE TABLE other_expense_data DDL, locator: other_expense_data, observed_at: 2026-08-18 }
  - { type: business_confirmation, path: 用户于会话中确认, locator: cost_type 按费用名称字典表映射 expense_code 后进入 V2, observed_at: 2026-08-19 }
  - { type: das_code, path: /Users/liuqingchen/工作/代码/das-core, locator: das-feature-v5.8.6@8448e45a5；OtherExpenseDataEntity、OtherExpenseDataDomain、OtherExpenseDataServiceImpl, observed_at: 2026-08-19 }
---

# 净利核算—其他费用数据表

该表按月上传非订单直接产生的净利费用数据，并作为 `doris_app_net_profit_check_report_v2` 的业务上传费用输入。

| 字段 | 含义 |
|---|---|
| `month` | 上传当月第一天，如 `2024-05-01` |
| `owner_code` / `shop_code` / `warehouse_code` | 费用归属维度 |
| `cost_type` | 快递代发费、耗材费、运杂费、供应链费用、人工费用、平台费用、直播间费用、分摊费用 |
| `rate` | 费比值，四位小数 |
| `amount` | 费用金额 |

上传时先删除对应 `month` 的历史数据后写入，避免重复。写入 V2 时，使用 `cost_type`（费用名称）关联《T+1净利核算表.xlsx》可见 Sheet「费用名称字典表V6.4.9.3」中的费用名称，取得对应 `expense_code` 后进入 `doris_app_net_profit_check_report_v2`。

## DAS 代码比对（基线 `das-feature-v5.8.6@8448e45a5`）

- 文档/DDL 是 `tmp_data.other_expense_data`，而 `OtherExpenseDataEntity` 当前 `@Table` 配置为 `tmp_data.other_expense_data_test`，需确认环境表名。
- `OtherExpenseDataDomain.batchSaveOrUpdate` 的 MD5 键由 `month + owner_code + shop_code + warehouse_code + cost_type` 组成；上传调用只做批量写入。代码另有按 MD5 键删除的 `batchDeleteOtherExpenseData` 接口，导入方法本身不会自动整月删除。
- 当前 DAS 仓库未发现该上传表转换并写入 V2 的离线 ETL；该链路应在调度/ETL 代码中继续核验。
