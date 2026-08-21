---
asset_id: dws.trade_order_goods_index
layer: DWS
table_name: doris_dws_trade_order_goods_index
database: dp_dws
business_name: 系统订单与商品指标
status: 已确认
owner:
  product: 待确认
  warehouse: 待确认
refresh:
  frequency: 每日
  timezone: Asia/Shanghai
  load_window: 最近 60 天
  load_strategy: 删除最近 60 天旧数据后，重算并写入新数据
grain: 系统订单子单商品行；原始订单子单与系统订单子单保留关联字段
primary_key: [dt, sub_order_id]
partition:
  field: dt
  semantic: 下单日期
  strategy: RANGE（月）+ 动态分区
  retention: 历史分区创建；动态规则为从最早历史至未来 1 个月
fields_file: fields.md
version:
  scene: V6.5.1
  valid_from: 2026-08-13
  valid_to:
  change_summary: 依据当前销售模块 V6.5.1 和 Doris 建表语句首次登记
source_evidence:
  - type: warehouse_ddl
    path: /Users/liuqingchen/.codex/attachments/db88d14f-094c-4ad8-8729-35e78595ac71/pasted-text.txt
    locator: CREATE TABLE doris_dws_trade_order_goods_index
    observed_at: 2026-08-13
  - type: product_doc
    path: /Users/liuqingchen/Downloads/销售模块.xlsx
    locator: 基础指标-商品v6.5.1；修饰词；修饰词-商品专属；维度概念
    observed_at: 2026-08-13
implementation_mapping:
  das_references: []
  warehouse_references:
    - ddl: /Users/liuqingchen/.codex/attachments/db88d14f-094c-4ad8-8729-35e78595ac71/pasted-text.txt
open_questions:
  - “返利后成本（不含税）”为派生返利成本金额的中间计算，不作为本 Index 独立输出字段。
---

# 系统订单与商品指标

该表承载原始订单商品、系统订单商品与组合装商品指标。组合装在“原始订单 → 系统订单”上游业务阶段已完成拆分、分摊和去重，本表仅承接系统订单结果，不重复处理。`dt` 为下单日期，物理唯一键为 `dt + sub_order_id`；系统订单子单通过 `source_sub_order_id` 关联原始订单子单，系统订单主单与子单通过 `order_id` 关联。不能把分销数据写入或解释为该表的系统订单子单数据。
