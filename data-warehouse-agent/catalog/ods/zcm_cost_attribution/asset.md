---
asset_id: ods.zcm_cost_attribution
layer: ODS
table_name: doris_ods_zcm_cost_attribution
business_name: 成本归属
status: 待数仓确认
owner: { product: 待确认, warehouse: 待确认 }
refresh: { frequency: 待确认, timezone: Asia/Shanghai }
grain: 待确认
fields_file: fields.yaml
version: { scene: V1.0.0, valid_from: 2026-08-13, valid_to: null, change_summary: 从 DAS 代码首次登记 }
source_evidence:
  - { type: das_code, path: "/Users/liuqingchen/工作/代码/das-core", locator: "出现 doris_ods_zcm_cost_attribution", observed_at: 2026-08-13 }
implementation_mapping: { das_references: [], warehouse_references: [] }
open_questions: ["请提供正式 DDL、源系统、成本归属对象与生效规则。"]
---

# 成本归属

已由 DAS 代码引用识别；字段资产待数仓确认。
