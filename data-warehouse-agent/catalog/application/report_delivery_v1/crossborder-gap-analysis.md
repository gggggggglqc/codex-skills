# 发货 V1 跨境接入分析与补充清单

> 依据《跨境系统表建设-文秋红.xlsx》的全部可见 Sheet 解析；隐藏 Sheet「跨境系统单index表」按既定规则忽略。字段需求以可见 Sheet「V6.5.1跨境系统订单」「跨境系统退单index」为准。

## 已可确认的跨境数据链路

```text
cbs_trade_order + cbs_sub_trade_order
  → doris_dwd_cbs_systrade_order_combine
  → doris_dws_cbs_trade_order_index

cbs_refund_order + cbs_sub_refund_order
  → doris_dwd_cbs_sysrefund_combine
  → doris_dws_cbs_refund_order_index
  → doris_app_report_delivery_v1
```

- 跨境订单 V1 使用：`delivery_status=1`、`delivery_time`、`order_function in (1,10)`、`sales_model in (1,2,6)`，以及数量、人民币发货收入、供货/采购/净利成本。
- 跨境退单 V1 使用：`delivery_status=1`、`status=4`（退款成功）、`apply_time`、`finish_time`、`quantity`，以及人民币退款支出、供货/采购/净利成本。
- 跨境费用来源规划为 `fms_cost.expense_detail_cb`；跨境订单收入与退款需以财务汇率折算人民币，CNY 汇率为 1、无生效汇率取最新值。

## 已有资料无需重复提供

- 跨境订单、系统退单的字段级业务说明和 ODS/DWD 链路。
- 订单/退单的数量、发货状态、退款成功状态、成本字段的业务规则。
- 跨境费用业务表的字段说明。

## V1 已明确的历史切换描述

来源为《发货口径应用指标表（发货 V1）说明-离线》：

- “销售数量 → 跨境订单发货数量”及“销售收入 → 跨境订单发货收入”写明：**7 月 15 日之前用易仓，8 月和 9 月用跨境差异表，10 月 1 日开始接入自研跨境**；差异由财务从跨境差异表导入调整。
- “退货数量 → 跨境订单退货数量”写明：**2025 年 7 月 15 日之前用易仓，2025 年 7 月 15 日及以后用自研跨境**。
- 易仓链路已确认：`doris_ods_eb_trade_order_tmp`（即“跨境差异表”，键为 `dt + shop_code + goods_code + sales_model + country_code`）→ `doris_dws_eb_trade_order_goods_index`（唯一键 `dt + sub_order_id`）→ 发货 V1。V1 不直接读取 ODS；差异表已提供发货数量、人民币收入、含税/不含税采购成本字段。“8 月和 9 月使用差异表”与退货数量的切换描述并不完全一致，不能自行推断为统一规则。

## 仍需补充

当前无跨境来源调度待确认项。易仓 DWS 已停止更新，按历史冻结数据源使用。

## 已知边界

- `doris_dws_cbs_trade_order_index` 已确认 `UNIQUE KEY(dt, sub_order_id)`、按 `dt` 月分区、`HASH(dt, sub_order_id)` 自动分桶；每日覆盖更新最近 90 日。
- `doris_dws_cbs_refund_order_index` 已确认 `UNIQUE KEY(dt, sub_refund_id)`、按 `dt` 月分区、`HASH(sub_refund_id)` 3 分桶；每日覆盖更新最近 90 日。
- `doris_dws_eb_trade_order_goods_index` 已确认 `UNIQUE KEY(dt, sub_order_id)`、按 `dt` 月分区、`HASH(dt, sub_order_id)` 自动分桶；已停止更新，仅作为历史冻结数据源供 V1 使用。
- `doris_ods_eb_trade_order_tmp` 已确认就是“跨境差异表”，提供 `sales_num`、`sku_total_cny`、`tax_freight_price_total`、`no_tax_freight_price_total`；不含退款字段。
- 国别已确认按 `dt + shop_plat_code → dp_dim.doris_dim_platform.plat_code` 关联，使用 `cbs_platform`（`0` 否、`1` 是）判定；跨境平台国别为空，非跨境平台为 `CN`。不采用已删除线的 `receiver_country_code` 规则。
- 汇率表已确认是 `fms_support.exchange_rate_system`，以 `source_currency_code`、`target_currency_code` 和 `effective_date`/`expiring_date` 生效区间匹配；跨境文档明确使用 `direct_exchange_rate`，CNY 固定为 1、无生效汇率取最新日期汇率。订单按支付/发货/完成时间，退款按申请/完成时间取对应字段规定的汇率。
- 跨境站点维表已确认是 `dp_dim.doris_dim_oms_product_cbs_area_site`，使用 `dt + site_code` 关联并提供 `site_name`、`plat_code`、`third_site_id`、`area_code`、`country_code`；当前 V1 DDL 未输出站点字段，故不阻塞 V1 现有字段建设，且不改用站点国家简码作为 V1 国别规则。
- 天猫超市补充事实已确认是 `dp_dws.doris_dws_finance_cost_sbjct`：`shop_plat_code='TMCS'`、`cost_code IN ('CI168','CI654')`，分别使用 `share`、`no_tax_amount`、`tax_amount` 进入含税收入、不含税收入和销项税额。`doris_dws_finance_cost_sbjct_failure` 仅用于费用分摊失败核查。
- 费用采集策略维表已确认是 `dp_dim.doris_dim_fms_support_cost_gather_strategy`，以 `dt + subject_code + cost_code` 管理采集策略；`is_gather`、`is_accrual_subject` 均为 `1` 是、`2` 否，`cost_share_method` 为 `0` 销售收入、`1` 销售成本、`2` 发货方量；`cost_belong` 已确认十类损益归属及加减方向。该表是财务费用治理资产，不作为销售模块直接字段进入 V1 的前置条件。

- V1 中 `no_tax_payment`、`output_tax_amount`、`input_tax_amount`、`rebate_amount` 的 DDL 注释仅列国内系统单、分销单及退单，当前应视为不含跨境，除非后续产品另行确认。
