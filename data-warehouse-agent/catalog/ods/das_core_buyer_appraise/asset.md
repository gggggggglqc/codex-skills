---
asset_id: ods.das_core_buyer_appraise
layer: ODS
table_name: doris_ods_das_core_buyer_appraise
business_name: 买家评价
status: 待数仓确认
owner: { product: 待确认, warehouse: 待确认 }
refresh: { frequency: 待确认, timezone: Asia/Shanghai }
grain: 待确认
fields_file: fields.yaml
version: { scene: V1.0.0, valid_from: 2026-08-13, valid_to: null, change_summary: 从 DAS 代码首次登记 }
source_evidence:
  - { type: das_code, path: "/Users/liuqingchen/工作/代码/das-core", locator: "出现 doris_ods_das_core_buyer_appraise", observed_at: 2026-08-13 }
implementation_mapping: { das_references: [], warehouse_references: [] }
open_questions: ["请提供评价主键、订单关联、评价时间、评分和内容脱敏规则。"]
---

# 买家评价

已由 DAS 代码引用识别；字段资产待数仓确认。
