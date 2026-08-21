# 老板报表待确认事项

以下均来自可见 Sheet 中的矛盾、待开发标记、未来版本或缺少物理映射；未确认前不应作为 Agent 的确定性规则。

| 优先级 | 待确认事项 | 文档位置与原因 |
|---|---|---|
| 高 | 实时销售应用表 DDL 与字段映射 | `doris_app_real_time_sales_report_rt`、`doris_app_real_time_sales_report_v1`、`doris_app_real_time_sales_report`：需提供 DDL、日切片/回刷窗口、`sales_amount`、`refund_amount`、`paid_num`、`refund_num` 及代销 `estimate_cost` 字段映射。 |
| 高 | 产销、人力及业务上传表 DDL 与字段映射 | `tmp_data.sales_production_revenue_profit`、`tmp_data.month_department_employee_cost`、业务上传临时表（物理表名待确认）：需提供导入粒度、月份/日期字段、唯一键、重导覆盖方式，以及 `EP001/EP003/EP004/EP005/EP028`、`tax_income_inclusive`、`revenue_expense_amount`、`self_rev` 的字段对照。跨境导入表 `tmp_data.abroad_production_revenue_profit` 已确认。 |
| 高 | 净利科目关系及凭证中间表 DDL 与关联 | `doris_dws_voucher_subject_mid`、`doris_dim_fms_support_subject`、`doris_dim_expense_subject_relation`：需提供 DDL、最新 `dt` 取法、与 `subject_code` / `cost_code` / `expense_code` 的关联键。 |
| 高 | 历史收入/净利跨境切换 | `DAS v5.8.4.2净利`：2026-04-01 前走旧逻辑/V1，之后跨境走 V2/`source=4`；需确认各页面、昨日/上月/财年/365 日跨期时是否统一按查询开始日切换。 |
| 高 | 采购成本字段税别互换 | 同 Sheet 的清仓品行：字段“含税含运采购成本”写 `sum(不含税采购成本)`，“不含税含运采购成本”写 `sum(含税采购成本)`；需确认是列名还是公式互换。 |
| 中 | 委外仓库存/去库存金额取价 | `DAS v5.8.6老板报表指标` 行 131、140 标记委外仓 `warehouse_use_type=4` 的“不含税月度成本价为空/0时兜底采购价”为待开发。需确认是否纳入当前页面。 |
| 中 | 跨境订单数与供应商跨境筛选 | 行 144 标记 2025-07-15 后跨境自研系统订单去重为待开发；行 185 写跨境表暂无限制。需确认订单数、供应商页面跨境过滤规则。 |
| 中 | 有效 SKU 是否含禁用货主/SKU | Sheet「额外说明」第 16 行直接提出此问题，未给结论。 |
| 中 | 产销导入数据及货主配置 | 人力成本占比、集团/部门收入净利使用大量固定货主清单、`EP001/EP003/EP004/EP005/EP028`；需提供产销导入表 DDL、`field_code` 字段解释、历史补数和清单维护机制。 |
| 中 | 其他当前页面来源的结构/映射 | `dp_dws.doris_app_delivery_return_report`、`dp_dws.doris_dws_drop_shipping_delivery_return_report`、`doris_dws_bn_work_order_index`、`doris_dws_refund_order_index_rt`、`doris_dws_trade_order_goods_index_rt`、`dp_ods.doris_ods_upload_expense_detail`、`dp_ods.doris_ods_upload_expense_detail_cb`：文档使用但尚未提供 DDL/字段映射。 |
| 低 | 实时与结账后回刷差异 | 文档写实时发货收入会回刷近 60 天，净利含税收入按天回刷、结账后不再回刷。需确认报表选择实时/历史口径时的最终优先级和结账标志来源。 |

## 已识别的后续开发项（不作为当前缺失）

- v5.8.6 本月底与 `DWP-V6.4.9.3`、`DWP-V6.4.9.4`、`DWP-V6.4.9.5` 联动上线；`DWP-V6.4.9.6` 尚未评审，不纳入本期。
