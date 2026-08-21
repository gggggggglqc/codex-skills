---
asset_id: ods.upload_expense_detail
layer: ODS
table_name: doris_ods_upload_expense_detail
business_name: 上传费用明细
status: 待数仓确认
owner:
  product: 待确认
  warehouse: 待确认
refresh:
  frequency: 待确认
  timezone: Asia/Shanghai
grain: 待确认
fields_file: fields.yaml
version:
  scene: V1.0.0
  valid_from: 2026-08-13
  valid_to:
  change_summary: 从老板报表口径说明首次登记
source_evidence:
  - type: product_doc
    path: "老板报表与T+1净利字段逻辑整理.md"
    locator: "部门排行榜、店铺排行榜、平台链接中的推广费口径"
    observed_at: 2026-08-13
  - type: das_code
    path: "/Users/liuqingchen/工作/代码/das-core"
    locator: "代码文本中出现 doris_ods_upload_expense_detail"
    observed_at: 2026-08-13
implementation_mapping:
  das_references: []
  warehouse_references: []
open_questions:
  - 请数仓开发提供正式 DDL、分区策略、刷新频率与字段字典。
  - 请确认“支出、收入、一级费用类目、实际发生、平台链接”等字段物理名称与枚举。
---

# 上传费用明细

## 已知业务用途

老板报表中的推广费使用“支出减收入”，并限定一级费用类目为推广费用、实际发生；平台链接场景还限定平台链接不为空。

## 使用限制

上述为应用指标口径，不等同于 ODS 字段定义。字段与分区规则未确认前不得据此自动生成生产查询。
