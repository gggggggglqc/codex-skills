---
asset_id: app.report_delivery_v1
layer: APP
table_name: doris_app_report_delivery_v1
database: dp_dws
business_name: 发货口径应用指标表（发货 V1）
status: 已确认
refresh: { frequency: 每日, timezone: Asia/Shanghai, load_window: 近90日, load_strategy: 覆盖更新 }
grain: 分区日期 + 应用维度组合的指标汇总行
primary_key: dt + plat_code + shop_type + shop_code + shop_plat_code + owner_code + business_group + spu_code + sku_code + plat_spu_id + plat_sku_id + goods_category + is_brand_fix_priced + is_self_research + category_level1~4 + sales_model + country_code + warehouse_code + plat_goods_code + distributor_id + is_stop_orders + is_defective + supplier_code + warehouse_use_type + structure_id + company_code + cbs_platform + author_id + is_self_live_stream + brand_id（UNIQUE KEY）
partition: { field: dt, semantic: 系统/分销发货取发货日期，出入库取入库日期，系统退款取退款日期，分销退款取收货日期, strategy: 无 PARTITION BY 声明（非物理分区表） }
fields_file: fields.md
version: { scene: 发货 V1 应用层, valid_from: 2026-08-17, valid_to: null, change_summary: 首次解析离线指标说明文档 }
source_evidence:
  - { type: product_doc, path: /Users/liuqingchen/Downloads/发货口径应用指标表（发货V1）说明-离线.md, locator: 全文, observed_at: 2026-08-17 }
  - { type: warehouse_ddl, path: /Users/liuqingchen/.codex/attachments/9cc7f261-75ba-4653-a457-bdacb43503c1/pasted-text.txt, locator: dp_dws.doris_app_report_delivery_v1（字段与公式）, observed_at: 2026-08-17 }
  - { type: warehouse_ddl, path: /Users/liuqingchen/.codex/attachments/40280be0-f397-4167-8da4-649a2bfe8468/pasted-text.txt, locator: doris_app_report_delivery_v1（完整物理 DDL）, observed_at: 2026-08-17 }
implementation_mapping:
  warehouse_references:
    - { upstream_asset: dws.trade_order_goods_index, usage: 系统订单发货数量、收入、成本、返利及税额 }
    - { upstream_asset: dws.dms_delivery_index, usage: 分销发货数量、收入、成本、返利及税额 }
    - { upstream_asset: dws.refund_order_index, usage: 系统退单退款、退款成本及税额 }
    - { upstream_asset: dws.dms_refund_return_index, usage: 分销退货退款、退款成本及税额 }
    - { upstream_asset: dws.inbound_and_outbound_index, usage: 退货应收、无单退货、退货实收及分销退货入库数量 }
    - { upstream_asset: dws.cbs_trade_order_index, usage: 跨境系统订单发货数据；每日覆盖更新最近90日 }
    - { upstream_asset: dws.cbs_refund_order_index, usage: 跨境系统退单退款、退货及退款成本；每日覆盖更新最近90日 }
    - { upstream_table: fms_cost.expense_detail_cb, usage: 跨境费用明细；DDL及与 V1 差异/费用字段映射待提供 }
    - { upstream_asset: dws.eb_trade_order_goods_index, usage: 跨境差异表的易仓历史发货数量、人民币收入及采购成本；其 ODS 来源为 doris_ods_eb_trade_order_tmp }
    - { upstream_asset: dws.finance_cost_sbjct, usage: 天猫超市含税收入、不含税收入及销项税额补充；TMCS + CI168/CI654 }
---

# 发货口径应用指标表（发货 V1）

该应用层表按发货及退款时间汇总销售数量、退货数量、收入、税额、供货成本、采购成本、净利成本、返利成本和体积等指标，供老板报表、全渠道商品统计和销售对比分析使用。字段级的最终汇总口径以本表 DDL 注释为准。表采用 UNIQUE KEY，按 `shop_code` Hash 分桶 2 个 Bucket。

**结构结论**：现有物理 DDL 已完整，可承载当前已确认指标。离线说明另标记“产销结算店铺、结算店铺名称”为后续开发字段，二者不属于当前 V1 的结构范围。

应用范围显式包含跨境数据；这与销售模块基础 Index 本期“跨境销售忽略”的建设范围不同，二者不可互相替代。

详见：[血缘图](lineage.md)、[指标口径](metrics.md)、[维度规则](dimensions.md)、[跨境接入分析](crossborder-gap-analysis.md)、[补充来源清单](supplemental-sources.md)。
