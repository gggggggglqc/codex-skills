---
asset_id: app.boss_report_multidim
layer: 多维数据应用层
business_name: 多维报表－老板报表
status: 部分确认
version:
  current_version: v5.8.6（开发中，计划月底上线）
  version_note_latest: Das-v3.9.2（2026-06-26，已上线；与当前开发版本并存）
  visible_rule_sheets: [DAS v5.8.4.2净利, DASv5.8.6净利优化, DAS v5.8.6老板报表指标, DAS v5.8.6人力成本占比, 额外说明]
refresh: { frequency: 待确认, timezone: Asia/Shanghai, load_window: 各底表按文档时间窗口, load_strategy: 待确认 }
grain: 页面查询维度组合 + 业务日期/统计周期
source_evidence:
  - { type: product_doc, path: /Users/liuqingchen/Downloads/老板报表应用产品.xlsx, locator: 可见 Sheet，隐藏 Sheet 不作为当前规则来源, observed_at: 2026-08-18 }
---

# 多维报表－老板报表

本资产解析可见 Sheet；隐藏历史版本、删除线内容均不纳入当前有效口径。当前开发版本为 **v5.8.6**，计划月底上线；已识别集团、部门、渠道、店铺、达人、品类、货品、SKU、清仓品、供应商等页面，以及人力成本占比和价税分离净利弹窗规则。

当前可确认的核心数据源包括：

- 发货口径：`dp_dws.doris_app_report_delivery_v1`；
- 实时支付口径：`doris_app_real_time_sales_report_rt`、`doris_app_real_time_sales_report_v1`；
- 净利：`doris_app_net_profit_check_report_v2`、`doris_dws_finance_cost_sbjct`、`doris_dws_finance_cost_sbjct_failure`；
- 产销导入：`tmp_data.sales_production_revenue_profit`；
- 库存/动销：`doris_dws_sku_stock_index`、`doris_dim_sku_dynamic_sales`、`doris_dws_stock_turnover_index`。

详见：[字段与规则](/Users/liuqingchen/Documents/Codex/windows-projects/Das/catalog/application/boss_report_multidim/fields.md)、[待确认事项](/Users/liuqingchen/Documents/Codex/windows-projects/Das/catalog/application/boss_report_multidim/open-items.md)。
