---
asset_id: ods.erp_auth_ding_department
layer: ODS
table_name: doris_ods_erp_auth_ding_department
business_name: 钉钉部门组织
status: 待数仓确认
owner: { product: 待确认, warehouse: 待确认 }
refresh: { frequency: 待确认, timezone: Asia/Shanghai }
grain: 待确认
fields_file: fields.yaml
version: { scene: V1.0.0, valid_from: 2026-08-13, valid_to: null, change_summary: 从 DAS 代码首次登记 }
source_evidence:
  - { type: das_code, path: "/Users/liuqingchen/工作/代码/das-core", locator: "出现 doris_ods_erp_auth_ding_department", observed_at: 2026-08-13 }
implementation_mapping: { das_references: [], warehouse_references: [] }
open_questions: ["请提供部门 ID、层级、父子关系、有效状态与同步频率字段定义。"]
---

# 钉钉部门组织

已由 DAS 代码引用识别；字段资产待数仓确认。
