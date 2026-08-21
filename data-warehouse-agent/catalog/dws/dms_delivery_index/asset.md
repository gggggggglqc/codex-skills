---
asset_id: dws.dms_delivery_index
layer: DWS
table_name: doris_dws_dms_delivery_index
database: dp_dws
business_name: 分销发货与退货指标
status: 已确认
owner:
  product: 待确认
  warehouse: 待确认
refresh:
  frequency: 每日
  timezone: Asia/Shanghai
  load_window: 最近 60 天
  load_strategy: 删除最近 60 天旧数据后，重算并写入新数据
grain: 分销发货单子订单商品行
primary_key: dt + sub_delivery_order_id
partition:
  field: dt
  semantic: 主单创建时间
  strategy: 每日删除并重算最近 60 天
fields_file: fields.md
version:
  scene: V6.5.1
  valid_from: 2026-08-13
  valid_to:
  change_summary: 依据当前销售模块 V6.5.1 和 Doris 建表语句首次登记
source_evidence:
  - type: warehouse_ddl
    path: /Users/liuqingchen/.codex/attachments/9a20546a-155c-466b-b214-bfd3617862f4/pasted-text.txt
    locator: CREATE TABLE dp_dws.doris_dws_dms_delivery_index
    observed_at: 2026-08-13
  - type: product_doc
    path: /Users/liuqingchen/Downloads/销售模块.xlsx
    locator: 基础指标-商品v6.5.1（分销发货单、分销退货单商品指标）
    observed_at: 2026-08-13
implementation_mapping: { das_references: [], warehouse_references: [] }
open_questions:
  - “返利后成本（不含税）”为派生计算中间金额，不作为本 Index 独立输出字段。
---

# 分销发货与退货指标

本表以分销发货单子订单为行粒度，承载发货、实到、实收与退货数量/金额及相关成本。它通过分销订单号、分销子订单号关联分销订单，不与系统订单子单关联。
