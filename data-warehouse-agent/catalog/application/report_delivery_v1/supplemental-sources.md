# 发货 V1 补充来源：具体待接入清单

本清单只列影响 V1 现有字段的补充来源。不是所有跨境 Excel 中的表都必须进入 V1。

## 1. 跨境站点维表：当前不阻塞 V1

已提供维表：`dp_dim.doris_dim_oms_product_cbs_area_site`，以 `dt + site_code` 唯一。至少包含：

| 业务字段 | 已知字段 | 用途 |
|---|---|---|
| 站点编码 | `site_code` | 跨境订单 Index 的站点关联键 |
| 站点名称 | `site_name` | 跨境订单及宽表展示 |
| 站点 ID/商城 ID | `third_site_id` | 站点辅助识别 |
| 所属平台 | `plat_code` | 站点所属平台 |
| 国家简码 | `country_code` | 站点国家属性；不替代 V1 当前国别规则 |

当前 `doris_app_report_delivery_v1` DDL 没有 `site_code`、`site_name` 字段，因此该维表不是 V1 现有字段落表的前置条件；后续要在 V1 按站点分析时，可按 `dt + site_code` 接入。

## 2. 销售模块直接字段：不经费用采集策略表

销售模块 V6.5.1 已定义商品级含/不含税订单收入、销项税额、成本进项税额、卖家运费、代发费及其进项税额口径。它们应作为 V1 的直接销售 Index 上游，不以 `subject_code`/`cost_code` 再次识别：

| 销售模块字段 | 已知支撑字段/公式 | 对 V1 的作用 |
|---|---|---|
| 销项税额 | `sales_model=线上分销（代销）`：`brand_quotation/(1+税率)×税率`；其他模式：`payment/(1+税率)×税率`；保留 2 位 | `output_tax_amount` 的直接组成 |
| 进项税额（成本） | 非小规模公司：`product_cost/(1+税率)×税率`；小规模公司：`0` | `input_tax_amount` 的直接组成 |
| 不含税订单收入 | 线上分销（代销）：`brand_quotation - 销项税额`；其他模式：`payment - 销项税额` | `no_tax_payment` 的直接组成 |
| 卖家运费进项税额 | 销售模块字段公式 | `input_tax_amount` 的直接组成 |
| 代发费进项税额 | 销售模块字段公式 | `input_tax_amount` 的直接组成 |
| 不含税卖家运费 | 系统单范围内，按系统单获取订单后使用子单粒度预估物流费用字段 `no_tax_logistics_cost_fee` | V1 直接字段；净利 V2 写入 `EP031` |
| 不含税代发费（仓储服务费） | 系统单范围内，按系统单获取订单后使用子单粒度预估代发费用字段 `no_tax_agent_delivery_fee` | V1 直接字段；净利 V2 写入 `EP032` |
| 包装耗材进项税额 | `含税包材费用 / (1 + 13%) × 13%` | 销售模块包材税额口径 |

因此，当前 V1 不需要再为上述销售模块字段补充费用采集策略编码或有效策略行。费用采集策略表 `dp_dim.doris_dim_fms_support_cost_gather_strategy` 保留为财务费用治理资产，可按 `dt + subject_code + cost_code` 与费用事实关联，但不是这些 V1 直接字段的前置来源。

策略枚举已确认：`is_gather`、`is_accrual_subject` 均为 `1` 是、`2` 否；`cost_belong` 为收入/成本/费用等十类损益归属；`cost_share_method` 为销售收入/销售成本/发货方量。

## 3. 天猫超市收入：影响收入和销项税额

物理来源已确认：`dp_dws.doris_dws_finance_cost_sbjct`。文档给出业务筛选：`shop_plat_code = 'TMCS'` 且费用项目 `cost_code IN ('CI168', 'CI654')`。

| 项目 | 已确认口径 |
|---|---|
| 物理来源 | `dp_dws.doris_dws_finance_cost_sbjct` |
| 过滤 | `shop_plat_code = 'TMCS'`，`cost_code IN ('CI168', 'CI654')` |
| 时间 | `dt`（业务发生日期） |
| 含税收入 | `share` |
| 不含税收入 | `no_tax_amount` |
| 销项税额 | `tax_amount` |

该表已具备 V1 所需字段。`doris_dws_finance_cost_sbjct_failure` 是未分摊异常事实，只用于核查，不能直接计入 V1。

## 4. 跨境费用明细：不等同于 V1 必填费用补充

跨境 Excel 已说明 `fms_cost.expense_detail_cb` 用于跨境账单收入、支出、物流与费用明细；其典型关联为原始订单/子单或 SKU，金额按账单日期 `trans_dt` 汇率折算人民币。该表目前是跨境 Index/费用分析的上游候选，只有 V1 明确要将某项跨境费用计入现有字段时，才需要把它直接接入 V1；不能因“费用表存在”自动计入销售收入或税额。
