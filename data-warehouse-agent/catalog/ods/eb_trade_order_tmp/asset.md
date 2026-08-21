---
asset_id: ods.eb_trade_order_tmp
layer: ODS
table_name: doris_ods_eb_trade_order_tmp
database: dp_ods
business_name: 跨境差异表（易仓历史订单汇总临时表）
status: 已确认
refresh:
  frequency: 待确认
  timezone: Asia/Shanghai
  load_window: 待确认
  load_strategy: 待确认
grain: 发货日期 + 店铺 + 商品 + 销售模式 + 国家
primary_key: [dt, shop_code, goods_code, sales_model, country_code]
partition:
  field: dt
  semantic: 易仓发货日期
  strategy: RANGE（月）+ 动态分区
  retention: 历史分区创建；动态规则从最早历史至未来 1 个月
distribution: HASH(dt)，BUCKETS AUTO
version:
  scene: 发货 V1 跨境差异历史来源
  valid_from: 2026-08-18
  valid_to:
  change_summary: 依据完整 Doris DDL 首次登记
source_evidence:
  - type: warehouse_ddl
    path: /Users/liuqingchen/.codex/attachments/1ae46b47-bdaa-4606-a2e0-4e1bcaf5bac7/pasted-text.txt
    locator: CREATE TABLE doris_ods_eb_trade_order_tmp
    observed_at: 2026-08-18
implementation_mapping:
  warehouse_references:
    - downstream_asset: dws.eb_trade_order_goods_index
      usage: 易仓历史订单商品 DWS 的 ODS 输入；发货 V1 不直接读取本表
---

# 跨境差异表（易仓历史订单汇总临时表）

该表就是发货 V1 文档所称的“跨境差异表”。尽管位于 `dp_ods`，其键是按发货日期、店铺、商品、销售模式、国家汇总，已不是原始订单子单粒度。它提供易仓 DWS 构建所需的历史跨境数量 `sales_num`、人民币收入 `sku_total_cny`、含税及不含税含运费采购成本总额；不能把它当作原始易仓订单明细表，也不是 V1 的直接输入。
