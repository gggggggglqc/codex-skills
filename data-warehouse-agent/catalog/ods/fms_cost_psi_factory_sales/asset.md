---
asset_id: ods.fms_cost_psi_factory_sales
layer: ODS
table_name: doris_ods_fms_cost_psi_factory_sales
business_name: FMS 成本产销销售业务日志
status: 待数仓确认
owner: { product: 待确认, warehouse: 待确认 }
refresh: { frequency: 待确认, timezone: Asia/Shanghai }
grain: 待确认
fields_file: fields.yaml
version: { scene: V1.0.0, valid_from: 2026-08-13, valid_to: null, change_summary: 从 DAS 模型首次登记 }
source_evidence:
  - { type: das_code, path: "/Users/liuqingchen/工作/代码/das-core/jbs-das-core-model/src/main/java/com/jbs/das/core/model/DorisOdsFmsCostPsiFactorySalesBo.java", locator: "DorisOdsFmsCostPsiFactorySalesBo", observed_at: 2026-08-13 }
implementation_mapping: { das_references: [], warehouse_references: [] }
open_questions: ["请提供正式 DDL、表粒度、产销特殊口径字段和分区策略。"]
---

# FMS 成本产销销售业务日志

已由 DAS 模型识别；字段资产待数仓确认。
