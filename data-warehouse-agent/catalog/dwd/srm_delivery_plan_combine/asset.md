---
asset_id: dwd.srm_delivery_plan_combine
layer: DWD
table_name: doris_dwd_srm_delivery_plan_combine
database: dp_dwd
business_name: 采购交货计划宽表
status: 已确认
refresh: { frequency: 待确认, timezone: Asia/Shanghai }
grain: 采购交货计划行（delivery_plan_id）
primary_key: 待确认（DDL 未声明 Doris 键模型）
partition: { field: dt, semantic: 采购交货计划创建日期, strategy: 待确认 }
fields_file: fields.md
version: { scene: 库存模块 V6.5.1, valid_from: 2026-08-14, valid_to: null, change_summary: 登记未交收库存与发货在途库存来源 }
source_evidence:
  - { type: warehouse_ddl, path: /Users/liuqingchen/.codex/attachments/d056fdd0-86bb-4aa6-9f32-27967922930a/pasted-text.txt, locator: doris_dwd_srm_delivery_plan_combine, observed_at: 2026-08-14 }
  - { type: warehouse_ddl, path: /Users/liuqingchen/.codex/attachments/dec718bf-4724-4422-a23f-682c4128aeb0/pasted-text.txt, locator: doris_dwd_srm_delivery_plan_combine, observed_at: 2026-08-14 }
implementation_mapping:
  warehouse_references:
    - upstream_asset: ods.srm_delivery_plan
      join: delivery_plan_id；提供 demand_num、actual_receive_num、in_transit_num、is_delete 与商品/仓库/货主键
    - downstream_asset: dws.sku_stock_index
      join: 按自然日、plan_goods_code、plan_warehouse_code、plan_owner_code 汇总未交收和发货在途库存
---

# 采购交货计划宽表

库存日切片的未交收库存与发货在途库存来源。当前有效规则均限制未删除 `is_delete = 1` 且采购订单不是“已取消”；未交收数量为 `demand_num - actual_receive_num`，发货在途数量为 `in_transit_num`，后者限制 `settlement_status = 20`（发货在途）。业务源表 `srm_ops.delivery_plan` 不含该状态，Combine 由采购订单关联补充。
