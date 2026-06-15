---
name: 老板报表公式说明
description: 老板报表/大屏（2025-04 发货口径）所有页面指标的计算逻辑、库表来源、限定逻辑与业务释义。当用户询问大屏/老板报表中任意指标（收入、毛利率、退款、库存、销量、净利、所得税、清仓金额、人均日产、SKU 日产、推广费比、平台链接、渠道占比、供应商成本、售后补发等）的口径/公式/取值表/分子分母/筛选范围时使用。
---

# 老板报表公式说明 Skill

## 用途

本 skill 沉淀了「老板报表 / 大屏应用产品」2025-04 发货口径的全部指标规则，覆盖以下 9 张大屏 + 4 个公共模块：

- 清仓品大屏
- 货品 / 自研 / 外采 / 品类 / SKU 汇总 五张排行榜
- 店铺 / 达人 / 天猫京东 / 抖音快手 / 拼多多 店铺排行榜
- 部门排行榜（发货口径）
- 公司大屏
- 供应商大屏
- 渠道排行榜（发货口径）
- 平台链接
- 售后补发商品
- 原子 SKU
- 净利核算指标（含税口径，旧）
- 税后净利核算指标（价税分离，新版）

## 何时使用本 skill

当用户提到下列关键字时，**必须**先按需读取本 skill 的参考文档再回答：

- 老板报表 / 大屏 / 看板 / 报表口径 / 报表公式 / 计算逻辑
- 发货口径、支付口径、不减退款、已减退款
- 清仓品 / 清仓库存金额 / 清仓处理金额
- SKU 日产 / 人均日产 / 1 元人力产出 / 人力成本占比
- 毛利率（含税 / 不含税 / 含税含运）/ 月同比 / 同期增长率
- 净利 / 税后净利 / 利润总额 / 销项税 / 进项税 / 应交增值税 / 印花税 / 水利建设基金
- 平台链接 / 渠道排行 / 店铺排行 / 部门排行 / 供应商大屏
- 货主合并 / 店铺过滤 / 平台映射

## 全局页面逻辑（必须先读）

回答任何指标问题前，**先把 [references/global-rules.md](./references/global-rules.md) 中的 17 条全局逻辑带入上下文**，否则容易答错口径、周期与排序默认。

关键摘录：

- **近 30 日** = 包含昨天的前 30 天；**本月** = 当月 1 号至昨天，不含当天；**财年** = 最近的 4 月 1 号至昨天。
- 数据源主要是订单表（系统订单 / 退单 / 分销订单 / 跨境订单），业务日期一般取**发货日期**，费用取**账单日期或凭证日期**。
- 业态默认只展示 TOB / TOC，sales_model = (1, -1) 与新增销售模式都归入「其他」；TOC: business_type=2，国内: country_type=1。
- 2024-01 起，**供应商大屏的毛利率和成本全部改为含税含运口径**展示。
- 实时 vs 历史**同周期数据不可对比**：实时表每天跑最近 30 天；历史表每天只跑昨日。
- 趋势图汇总规则：全仓 / 清仓库存金额、件均价、SKU 日产、人均日产、1 元人力产出 用平均值汇总；毛利率 / 退款 趋势图按收入成本求和后再算。
- 抽屉数据池：展示最近 365 日收入 ≠ 0 或今日金额 ≠ 0 的数据。
- 大屏部门筛选项已剔除「佳优、佳赏、佳三、佳四」四个货主。
- SKU、货品类目相关属性（淘汰品 / 瑕疵品 / 停止下单品 / 商品类型 / 类别 / 是否单品 / 是否删除 / 是否自研 / 是否自产 / 品牌 / 品类类目）**统一从动销表取值**。
- 库存 index 表统一限制销售仓 + 代发仓。

## 模块速查路由

按用户问的对象/页面读取对应文档：

| 用户问到 | 读取的文档 |
|---|---|
| 整体页面规则 / 时间口径 / 业态规则 | [references/global-rules.md](./references/global-rules.md) |
| 清仓品大屏（库存数量 / 财务销售收入 / 毛利率 / 退款率 / 去库存 / 件均价 / 上架日期 / 可发天数 / 含税含运成本价） | [references/clearance.md](./references/clearance.md) |
| 货品 / 自研 / 品类 / 外采 / SKU 汇总 排行榜（今日金额 / 昨日金额 / 7日环比 / 收入 / 毛利率 / 自研占比 / 件均价 / 库存 / 可发天数 / 平均日销 / 在途库存 / 上架天数 / 目标日销 / 目标月销 / 目标达成率 / 含税含运成本单价 / 快递费） | [references/sku-rank.md](./references/sku-rank.md) |
| 店铺 / 达人 / 天猫京东 / 抖音快手 / 拼多多 店铺排行（今日金额 / 7日环比 / 收入 / 毛利率 / 推广费 / 推广费比 / 单均价 / 已付金额） | [references/shop-rank.md](./references/shop-rank.md) |
| 部门排行榜（货主合并 / 店铺数 / 在岗人数 / 人均日产 / 1 元人力产出 / 人力成本占比 / 月完成率 / 年完成率 / 库存金额 / 周转天数 / 有效 SKU / 清仓品库存 / 清仓处理） | [references/department-rank.md](./references/department-rank.md) |
| 公司大屏（自营仓库存 / 代发仓库存 / 全仓库存 / 清仓品库存 / 本月清仓处理 / 有效 SKU / 发单量 / 本月收入 / 财年收入 / 同期收入 / 去年收入 / 月同比 / 同期增长率 / 自研品占比 / 上月毛利率 / 财年毛利率 / 本年预测收入 / 预测增长） | [references/company-dashboard.md](./references/company-dashboard.md) |
| 供应商大屏（销售成本 含税含运 / 年销售成本占比 / 总收入 / 毛利率 含税含运 / 自研占比 / 退款金额 / 退款占比 / 财年已交付/未交付采购额 / 税率 / 产值 / 有效 SKU / 有效货品 / SKU 日产 / 件均价） | [references/supplier-dashboard.md](./references/supplier-dashboard.md) |
| 渠道排行榜 / 渠道与店铺平台映射 | [references/channel-rank.md](./references/channel-rank.md) |
| 平台链接（今日支付/退款 / 昨日支付 / 退款率 / 单量 / 已发货收入 / 毛利率 / 推广费 / 单均价） | [references/platform-link.md](./references/platform-link.md) |
| 售后补发商品 / 原子 SKU | [references/after-sales-and-atomic.md](./references/after-sales-and-atomic.md) |
| 净利核算（含税口径 旧版） / 一级~六级科目 | [references/net-profit-old.md](./references/net-profit-old.md) |
| 税后净利核算（价税分离 新版 2026-04 起）/ 所得税 / 利润总额 / 含税收入 / 不含税收入 / 销项税 / 进项税 / 应交增值税 / 水利建设基金 / 印花税 / 销售费用无票 / 税金及附加 / 研发费用日期切换逻辑 | [references/net-profit-new.md](./references/net-profit-new.md) |

## 表名速查（核心库表）

| 用途 | 表名 |
|---|---|
| 实时支付（当日） | `doris_app_real_time_sales_report_rt` |
| 支付 V1（昨日及历史） | `doris_app_real_time_sales_report_v1` |
| 发货 V1（昨日 / 近 30 日 / 月 / 财年 / 365） | `doris_app_report_delivery_v1` |
| SKU 库存 index | `doris_dws_SKU_stock_index` |
| 动销维表 | `doris_dim_sku_dynamic_sales` |
| 动销-是否新品 | `doris_dim_SKU_is_new` |
| SKU 维表 | `doris_dim_SKU` |
| 采购价格维表 | `doris_dim_srm_purchase_price` |
| 月度采购阶梯价格维表 | `dp_dim.doris_dim_srm_billing_purchase_ladder_price` |
| 仓库维表 | `doris_dim_warehouse` |
| 系统订单 index | `doris_dws_trade_order_goods_index`，实时 `_rt` |
| 跨境订单 index | `doris_dws_eb_trade_order_goods_index` |
| 跨境自研系统 | `doris_dws_cbs_trade_order_index` |
| 退款 index | `doris_dws_refund_order_index`，实时 `_rt` |
| 供应商常规出库回库 | `dp_dws.doris_app_delivery_return_report` |
| 供应商代发出库回库 | `dp_dws.doris_dws_drop_shipping_delivery_return_report` |
| 供应商收货入库 | `dp_dws.doris_dws_inbound_and_outbound_index` + `dp_dws.doris_dws_srm_purchase_num_percentage_mid` |
| 采购到货 index | `doris_dws_srm_delivery_order_index` |
| 采购计划 index | `doris_dws_srm_delivery_plan_index` |
| 班牛工单 index（售后补发） | `doris_dws_bn_work_order_index` |
| 推广费用 / 上传费用明细 | `dp_ods.doris_ods_upload_expense_detail` |
| 净利 V2（新版） | `doris_app_net_profit_check_report_v2` |
| 国内费用-分摊成功 | `doris_dws_finance_cost_sbjct` |
| 国内费用-分摊失败 | `doris_dws_finance_cost_sbjct_failure` |
| 费用采集策略 | `doris_dim_fms_support_subject` |
| 科目关系 | `doris_dim_expense_subject_relation` |
| 月度部门人力成本（手工上传） | `tmp_data.month_department_employee_cost` |
| 部门绩效目标 | `das_core.performance_objectives` |
| SKU 目标销量 | `dp_ods.doris_ods_SKU_estimate_sales` |
| 上年历史（默认 TOB / 国内） | `last_year2022_*` |
| 财年同期增长率 | `tmp_date.year_income_rate` |
| 货主 / 店铺主数据 | `oms_business.shop`、`dp_dim.doris_dim_srm_supplier_supplier` |

## 字段速查

| 字段 | 含义 |
|---|---|
| `sales_amount` | 销售/支付金额 |
| `refund_amount` | 退款金额（已发货退款） |
| `undelivery_refund_amount` | 未发货退款金额 |
| `paid_num` / `refund_num` | 支付/退款数量 |
| `estimate_cost` / `estimate_refund_cost` | 线上分销（代销）下的供货成本/供货退款成本 |
| `estimate_brand_quotation` / `refund_brand_quotation` | 线上分销（代销）下的供货总额 / 退款总额 |
| `yst_delivery_num` | 昨日发货数量（库存表） |
| `tax_freight_price` / `no_tax_freight_price` | 含税含运 / 不含税含运 采购价 |
| `goods_type` | 1 = 销售货品 |
| `judge_combine` | 2 = 单品 |
| `item_type` | 商品类别（清仓品 / 正常品 / 瑕疵品 …） |
| `is_valid_goods_with_sale_goods` | 2 = 有效，1 = 无效 |
| `warehouse_use_type` | 1 销售仓 / 2 代发仓 / 4 委外仓 |
| `country_type` | 1 = 国内 |
| `business_type` | 2 = TOC |
| `sales_model` | 销售模式：2 线上直销，3 线下分销，4 平台入仓分销，5 线上分销（代销），6 线下零售/直销，7 线上分销（经销），8 线上代销，9 贴牌代工 |

## 公式记忆速查

| 业务概念 | 公式 |
|---|---|
| 不区分销售模式收入 | `sum(sales_amount)` |
| 区分销售模式收入 | 线上分销(代销): `sum(estimate_brand_quotation)`；其他: `sum(sales_amount)` |
| 不区分销售模式金额(减退款) | `sum(sales_amount - refund_amount)` |
| 区分销售模式金额(减退款) | 线上分销(代销): `sum(estimate_cost - estimate_refund_cost)`；其他: `sum(sales_amount - refund_amount)` |
| 含税毛利率 | `1 − sum(含税采购成本) / sum(财务销售收入)` |
| 不含税毛利率 | `1 − sum(不含税采购成本) / sum(财务销售收入)` |
| 7 日环比 | `(过去 7 天金额 − 过去 7~14 天金额) / 过去 7~14 天金额`，其中过去 7~14 天 = 过去 14 天 − 过去 7 天 |
| 件均价 | `近 30 日收入 / 近 30 日销量`，四舍五入取整 |
| 可发天数 | `总库存数量 / 加权日均出库`，向上取整；加权日均出库 = `7 日出库/7×60% + 14 日出库/14×40%` |
| 库存金额（销售仓） | `总库存数量 × 不含税月度成本价`，月度成本价为空或 0 时改取「不含税含运采购价」 |
| 库存金额（代发仓） | `总库存数量 × 不含税含运采购价` |
| 全仓库存金额 | `自营仓库存金额 + 代发仓库存金额` |
| 清仓品库存金额 | `淘汰品 + 瑕疵品 + 停止下单品` 的库存金额 |
| 已发货退款率 | `已发货退款金额 / 收入(不减退款)` |
| 未发货退款率 | `未发货退款金额 / 支付金额(不减退款)` |
| 推广费比 | `推广费用 / 发货收入(已减退款)`；推广费用 = `expense_detail 表支出 − expense_detail 表收入` |
| 人均日产 | `近 30 日销售收入 / 30 / 实时在岗人数`，向上取整 |
| 1 元人力产出 | `上月收入 / 人力成本总额`，四舍五入保留两位 |
| 人力成本占比 | `1 / 一元人力产出` |
| SKU 日产 | `近 30 日支付金额(已减退款) / 有效 SKU 数 / 30`，向上取整；分子不区分销售模式 |
| 月完成率 | `月度发货收入(减退款) / 月度绩效目标` |
| 年完成率 | `财年发货收入(减退款) / 财年绩效目标` |
| 月同比 | `(上月收入 − 同比月收入) / 同比月收入` |
| 同期增长率 | `(本财年收入 − 去年财年同期收入) / 去年财年同期收入` |
| 本年预测收入 | `本年财年收入 + (去年财年收入 × (1 + 同期增长率) − 本年财年收入)` |
| 周转天数 | `货主对应总库存数量 / 加权日均出库`，向上取整，限销售仓 + 代发仓 |
| 单均价 | `已付金额(不减退款) / 去重原始单量(不减退款)`，四舍五入保留两位 |
| 财年已交付采购额 | `sum(actual_receive_num × 不含税含运采购单价)` |
| 财年未交付采购额 | `sum(uncollected_num × 不含税含运采购单价)` |
| 税后净利 | `利润总额 − 所得税` |
| 所得税（非产销） | `(利润总额 + 销售费用无票) × 0.15` ，分子 < 0 时所得税取 0 |
| 利润总额（非产销） | `V2 不含税收入 + 2 个费用表不含税收入 − V2 不含税成本 − 2 个费用表成本 − 2 个费用表费用 − V2 表费用 − 税金及附加 − 水利建设基金 − 印花税(买卖合同)` |
| 水利建设基金 | `(EP028 不含税收入 + 主营业务收入 6001.99 + 其他业务收入 6051.03) × 0.05%` |
| 印花税买卖合同 | `(EP028 不含税收入 + 6001.99 + 6051.03 + 主营业务成本 6401.99 + 不含税成本 EP003) × 0.0003` |
| 应交增值税 | `销项税额 − 进项税额(成本) − 进项税额(费用)` |
| 税金及附加 | `应交增值税 × 0.12` |

## 使用约定

1. 回答指标问题前，**先指明该指标所在的页面**（清仓品 / 排行榜 / 部门 / 公司大屏 / 供应商 / 渠道 / 平台链接 / 净利），不同页面下同名指标的库表与限定逻辑可能不同。
2. 引用公式时**带上库表名 + 限定逻辑**（如「限制销售货品」「排除班牛平台」「仓库功能 in (1,2)」），避免给出残缺答案。
3. 若用户问「实时 / 历史 哪个口径」，直接按 [references/global-rules.md](./references/global-rules.md) 第 4 条与各页面文档区分。
4. 净利相关指标默认走**新版税后净利**逻辑（[net-profit-new.md](./references/net-profit-new.md)），仅当明确询问「老版含税净利」或时间在 2026-04 之前才走 [net-profit-old.md](./references/net-profit-old.md)。
5. 涉及具体 SQL 时，必须遵守各页面文档中的费用 / 科目排除清单（subject_code、cost_code 黑名单）。
