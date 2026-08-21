# 发货 V1 → 净利 V2 → 经营净利：结果核对映射

## 1. 使用范围

- `dp_dws.doris_app_report_delivery_v1`：按应用维度汇总的发货、退款、收入、成本与税额结果。
- `dp_dws.doris_app_net_profit_check_report_v2`：按商品、供应商和 `expense_code` 展开的净利事实；V1 行在此可能因供应商采购占比被拆成多行。
- `dp_dws.doris_app_finance_profit_business`：按财务科目和费用归属汇总的净利结果；计划月底上线后纳入实际勾稽。

核对前提：统一 `dt`、国内/跨境范围、店铺/货主/商品等共同维度；本轮 V1→V2 规则限定 V1 `cbs_platform=0 AND business_group<>6` 与 V2 `country_type=1` 的国内结果。V2 必须先按这些共同维度聚合，**不将供应商拆分行逐行与 V1 比较**。

## 2. V1 → V2 已确认映射

| 核对 ID | V1 字段 | V2 条件与字段 | 聚合公式 | 核对级别 |
|---|---|---|---|---|
| `REC-REV-001` | 代销（`sales_model='3'`）取 `estimate_brand_quotation`，其余取 `sales_amount` | `expense_code='EP001'`、`country_type=1`，发货 V1 来源行 | `SUM(V1.代销供货额/其他模式销售额) = SUM(V2.expense_amount)` | 含税销售收入（减退款） |
| `REC-REV-002` | `no_tax_payment`（`cbs_platform=0`） | `expense_code='EP028'`、`country_type=1` | `SUM(V1.no_tax_payment) = SUM(V2.expense_amount)` | 国内不含税收入 |
| `REC-COST-001` | `no_tax_product_cost`（`cbs_platform=0`） | `expense_code='EP003'`、`country_type=1` | `SUM(V1.no_tax_product_cost) = SUM(V2.expense_amount)` | 国内不含税净利成本 |
| `REC-TAX-001` | `output_tax_amount`（`cbs_platform=0`） | `expense_code='EP029'`、`country_type=1` | `SUM(V1.output_tax_amount) = SUM(V2.expense_amount)` | 国内销项税额 |
| `REC-TAX-003` | `input_tax_amount`（`cbs_platform=0`） | `expense_code='EP030'`、`country_type=1` | `SUM(V1.input_tax_amount) = SUM(V2.expense_amount)` | 成本进项税额 |
| `REC-TAX-002` | `input_tax_amount_rebate`（`cbs_platform=0`） | `expense_code='EP039'`、`country_type=1` | `-SUM(V1.input_tax_amount_rebate) = SUM(V2.expense_amount)` | 返利成本进项税额；跨境为 `0` |
| `REC-COST-002` | `rebate_amount`（`cbs_platform=0`） | `expense_code='EP038'`、`country_type=1` | `-SUM(V1.rebate_amount) = SUM(V2.expense_amount)` | 不含税返利成本 |

> “发货 V1 来源行”指 V2 中由 V1 进入的收入/成本事实。若物理字段 `flag=1` 可稳定代表该来源，核对 SQL 必须增加 `flag=1`；若上线实现未以该字段标识来源，则按已确认的国内订单范围、业务属性和 EP 编码过滤，并将该实现差异登记为核对证据。

> 六项共同的国内 V1 范围：`cbs_platform=0`，且 `business_group<>6`（排除产销事业群）。这与《收入成本V6.4.9.3》的“事业群不等于产销事业群”限制一致。

## 3. V2 → 经营净利已确认科目映射

经营净利表没有 `expense_code`，因此以费用名称字典表的 `EP → subject_code` 关系进行汇总核对。上线后统一按 V2 的 `dt`、店铺、货主、商品、销售模式、国别等经营净利共同维度聚合。

| 核对 ID | V2 `expense_code` | 经营净利 `subject_code` | 经营净利金额字段 | 核对公式 |
|---|---|---|---|---|
| `REC-FIN-001` | `EP028` | `6001.01` | `no_tax_amount` | `SUM(V2.expense_amount) = SUM(经营净利.no_tax_amount)` |
| `REC-FIN-002` | `EP040` | `6001.02` | `no_tax_amount` | `SUM(V2.expense_amount) = SUM(经营净利.no_tax_amount)` |
| `REC-FIN-003` | `EP003` | `6401.01` | `no_tax_amount` | `SUM(V2.expense_amount) = SUM(经营净利.no_tax_amount)` |
| `REC-FIN-004` | `EP041` | `6401.02` | `no_tax_amount` | `SUM(V2.expense_amount) = SUM(经营净利.no_tax_amount)` |
| `REC-FIN-005` | `EP038` | `6401.19` | `no_tax_amount` | `SUM(V2.expense_amount) = SUM(经营净利.no_tax_amount)` |
| `REC-FIN-006` | `EP029` | `2221.01.01` | `tax_amount` | `SUM(V2.expense_amount) = SUM(经营净利.tax_amount)` |
| `REC-FIN-007` | `EP030` | `2221.04.01.01` | `tax_amount` | `SUM(V2.expense_amount) = SUM(经营净利.tax_amount)` |
| `REC-FIN-008` | `EP039` | `2221.04.01.03` | `tax_amount` | `SUM(V2.expense_amount) = SUM(经营净利.tax_amount)` |

## 4. 当前不可做严格一一勾稽的项

| V1 字段/场景 | 原因 | 当前核对方式 |
|---|---|---|
| `input_tax_amount` | V1 为成本及相关费用进项税额的汇总字段；V2 按 `EP030`、`EP033`、`EP034`、`EP035`、`EP037` 等细分，不能将 V1 总额直接等同某一个 EP | 在明确 V1 内各进项税组成字段后，核对 `V1 总额 = 对应 EP 税额之和` |
| `purchase_price_total`、`no_tax_purchase_price_total` | V2 当前核心净利链路定义的是净利成本/返利成本，不等同采购成本字段 | 仅做趋势/异常波动核对，不纳入净利主链严格勾稽 |
| `estimate_brand_quotation` | 供货成本不属于当前 V2 已确认的 EP 主映射 | 仅做趋势/异常波动核对 |
| `paid_num`、`refund_num` | V2 不是数量事实表 | 对 V1/DWS 订单与发货 Index 进行数量勾稽，不穿透到 V2 |
| 跨境导入收入/成本 | V2 还承接跨境导入及关税、头程成本；V1 与 V2 的跨境来源和退款边界并非全部一一对应 | 国内与跨境分开核对；跨境以导入表和跨境 Index 为独立核对链 |

## 5. 执行顺序与容差

1. 先验证日期完整性与共同维度完整性。
2. 执行 V1 → V2 六条映射；按日、店铺、货主、商品逐层下钻。
3. 经营净利表上线并完成首次回刷后，执行 V2 → 经营净利八条映射。
4. 金额保留至源表精度比较；展示保留两位。绝对差额 `<= 0.01` 视为通过；超过 `0.01` 先按供应商、店铺、商品和来源标识拆分。

## 6. 来源与确认状态

- V1 字段含义与 V2 EP 映射：`catalog/application/report_delivery_v1/fields.md`、`catalog/application/net_profit_t1/rules.md`。
- EP—科目映射：T+1 文档可见 Sheet「费用名称字典表V6.4.9.3」，已摘录至 `catalog/application/net_profit_t1/rules.md`。
- 经营净利表尚未正式上线；第 3 节的实际结果核对状态为“待上线验证”。
