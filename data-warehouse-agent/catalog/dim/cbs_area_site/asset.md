---
asset_id: dim.cbs_area_site
layer: DIM
table_name: doris_dim_oms_product_cbs_area_site
database: dp_dim
business_name: 跨境区域站点维表
status: 已确认
refresh:
  frequency: 待确认
  timezone: Asia/Shanghai
  load_window: 按 dt 月分区
  load_strategy: 待确认
grain: 日期 + 站点编码
primary_key: [dt, site_code]
partition:
  field: dt
  semantic: 日期
  strategy: RANGE（月）+ 动态分区
  retention: 历史分区创建；动态规则保留最早历史至未来 2 个月
distribution: HASH(dt, site_code)，BUCKETS AUTO
version:
  scene: 跨境订单站点维度
  valid_from: 2026-08-18
  valid_to:
  change_summary: 依据完整 Doris DDL 首次登记
source_evidence:
  - type: warehouse_ddl
    path: 用户于会话中提供的 CREATE TABLE doris_dim_oms_product_cbs_area_site DDL
    locator: dp_dim.doris_dim_oms_product_cbs_area_site
    observed_at: 2026-08-18
---

# 跨境区域站点维表

以 `dt + site_code` 关联跨境订单，提供站点名称 `site_name`、所属平台 `plat_code`、第三方站点 ID `third_site_id`、区域、关联站点与国家简码 `country_code`。当前发货 V1 没有站点字段，站点维度不直接落入 V1；V1 国别仍按平台维表 `cbs_platform` 判定，不改用本站点国家简码。
