---
asset_id: ods.sku_estimate_sales
layer: ODS
table_name: doris_ods_sku_estimate_sales
business_name: SKU 预估销量
status: 待数仓确认
owner: { product: 待确认, warehouse: 待确认 }
refresh: { frequency: 待确认, timezone: Asia/Shanghai }
grain: 待确认
fields_file: fields.yaml
version: { scene: V1.0.0, valid_from: 2026-08-13, valid_to: null, change_summary: 从老板报表口径说明首次登记 }
source_evidence:
  - { type: product_doc, path: "老板报表与T+1净利字段逻辑整理.md", locator: "SKU / 货品排行榜：目标日销、目标月销、达成率", observed_at: 2026-08-13 }
  - { type: das_code, path: "/Users/liuqingchen/工作/代码/das-core", locator: "出现 doris_ods_sku_estimate_sales", observed_at: 2026-08-13 }
implementation_mapping: { das_references: [], warehouse_references: [] }
open_questions: ["请确认正式表名大小写：文档为 doris_ods_SKU_estimate_sales，DAS 为 doris_ods_sku_estimate_sales。", "请提供 SKU、目标日销、生效日期等字段定义。"]
---

# SKU 预估销量

## 已知业务用途

目标日销取汇总；目标月销为目标日销乘当月天数；达成率为本月销量除以目标月销。以上为 APP 口径，ODS 物理字段待确认。
