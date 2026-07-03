---
name: 老板报表T1净利
description: 老板报表/大屏（2025-04 发货口径）所有页面指标的计算逻辑 + T+1 净利核算（凭证科目、科目费用分摊、净利 V2、费用编码 EP001-EP037、业务上传临时表、跨境分摊、差异排查）+ das-core 代码实现（Java 净利引擎、SQL 查询、Apollo 配置、调度流程）。当用户询问大屏/老板报表中任意指标口径，或 T+1 净利的费用分摊、数据核对、SQL 实现、差异排查、代码逻辑、系统实现原理时使用。
---

# 老板报表 & T+1 净利 综合 Skill

## 用途

本 skill 整合了两大业务模块的完整规则：

**模块 A — 老板报表 / 大屏（2025-04 发货口径）**，覆盖 9 张大屏 + 4 个公共模块：清仓品大屏、货品/自研/外采/品类/SKU 五张排行榜、店铺排行榜、部门排行榜、公司大屏、供应商大屏、渠道排行榜、平台链接、售后补发商品、原子 SKU、旧版含税净利、新版税后净利。

**模块 B — T+1 净利核算**，覆盖：凭证科目中间表、科目费用分摊（成功/失败表）、净利 V2 汇总表、费用编码字典（EP001-EP037）、业务上传临时表、国内/跨境费用分摊、供应商采购占比分摊、天猫超市特殊分摊、差异排查清单。

**模块 C — das-core 代码实现**，覆盖：Java 净利计算引擎（MonitorNetProfitDetailSupport.java）的完整公式与数据流、MyBatis SQL 映射（MonitorNetProfitDetailMapper.xml）的查询结构与过滤条件、EP 编码在 SQL 中的实际映射逻辑、税费计算代码实现（增值税/税金附加/水利建设基金/印花税/所得税含产销分支）、费用分摊枚举（CostShareRuleEnum/ShareSceneEnum）、Apollo 运行时配置项、**数据同步 MQ 异步架构**（FanoutExchange 广播 + SyncMultiAnalysisAllDataConsumer 消费 + SkuCalcSendMsgSupport SKU 计算异步化至 das-batch）、对比弹窗构建逻辑。

**模块 D — 字段逻辑总览**，覆盖老板报表各页面字段和 T+1 净利字段的统一速查：公司、部门、店铺、渠道、SKU/货品/品类、清仓品、供应商、平台链接、售后补发、净利链路、EP 编码、税后净利、上传规则和排查清单。

## 何时使用本 skill

当用户提到下列关键字时，**必须**先按需读取对应参考文档再回答：

- 老板报表 / 大屏 / 看板 / 报表口径 / 报表公式 / 计算逻辑
- 发货口径、支付口径、不减退款、已减退款
- 清仓品 / 清仓库存金额 / 清仓处理金额
- SKU 日产 / 人均日产 / 1 元人力产出 / 人力成本占比
- 毛利率（含税 / 不含税 / 含税含运）/ 月同比 / 同期增长率
- 净利 / 税后净利 / 利润总额 / 销项税 / 进项税 / 应交增值税 / 印花税 / 水利建设基金
- 平台链接 / 渠道排行 / 店铺排行 / 部门排行 / 供应商大屏
- 货主合并 / 店铺过滤 / 平台映射
- **T+1 净利 / 净利核算 / 费用分摊 / 科目费用 / 凭证科目 / 费用编码 / EP001 / EP012 研发费用**
- **分摊成功表 / 分摊失败表 / 业务上传临时表 / 费比 / 费用金额**
- **供应商采购占比 / 天猫超市分摊 / 跨境费用分摊**
- **差异排查 / 数据核对 / 回刷窗口**
- **das-core / 代码实现 / 代码逻辑 / Java 实现 / SQL 实现 / 系统怎么算的 / 代码里怎么写**
- **MonitorNetProfitDetailSupport / ExpenseParser / Mapper / 净利引擎**
- **Apollo 配置 / 调度任务 / 数据同步 / syncMultiAnalysisAllData**
- **MQ / FanoutExchange / das-batch / SkuCalcSendMsgSupport / SyncMultiAnalysisAllDataConsumer**
- **CostShareRuleEnum / ShareSceneEnum / NeTProfitCalcTaxTypeEnum**
- **产销数据 / 产销临时表 / 产销所得税 / 不含税收入_产销**
- **字段逻辑 / 字段怎么算 / 每个页面字段 / 老板报表和 T+1 净利字段总览**

## 全局页面逻辑（老板报表必须先读）

回答老板报表任何指标问题前，**先把 [references/global-rules.md](./references/global-rules.md) 中的 17 条全局逻辑带入上下文**。

关键摘录：

- **近 30 日** = 包含昨天的前 30 天；**本月** = 当月 1 号至昨天，不含当天；**财年** = 最近的 4 月 1 号至昨天。
- 数据源主要是订单表（系统订单 / 退单 / 分销订单 / 跨境订单），业务日期一般取**发货日期**，费用取**账单日期或凭证日期**。
- 业态默认只展示 TOB / TOC，sales_model = (1, -1) 与新增销售模式都归入"其他"。
- 2024-01 起，**供应商大屏的毛利率和成本全部改为含税含运口径**。
- 实时 vs 历史**同周期数据不可对比**：实时表每天跑最近 30 天；历史表每天只跑昨日。
- SKU、货品类目相关属性**统一从动销表取值**；库存 index 表统一限制销售仓 + 代发仓。

## 模块速查路由

按用户问的对象/页面读取对应文档：

| 用户问到 | 读取的文档 |
|---|---|
| **每个页面字段逻辑 / 老板报表和 T+1 净利字段总览 / 指标速查** | [references/boss-report-t1-field-logic.md](./references/boss-report-t1-field-logic.md) |
| 整体页面规则 / 时间口径 / 业态规则 | [references/global-rules.md](./references/global-rules.md) |
| 清仓品大屏 | [references/clearance.md](./references/clearance.md) |
| 货品 / 自研 / 品类 / 外采 / SKU 汇总排行榜 | [references/sku-rank.md](./references/sku-rank.md) |
| 店铺 / 达人 / 天猫京东 / 抖音快手 / 拼多多 店铺排行 | [references/shop-rank.md](./references/shop-rank.md) |
| 部门排行榜（货主合并 / 人力 / 清仓 / SKU） | [references/department-rank.md](./references/department-rank.md) |
| 公司大屏（库存 / 收入 / 预测 / 自研占比） | [references/company-dashboard.md](./references/company-dashboard.md) |
| 供应商大屏（含税含运成本 / 产值 / 采购额） | [references/supplier-dashboard.md](./references/supplier-dashboard.md) |
| 渠道排行榜 / 渠道与店铺平台映射 | [references/channel-rank.md](./references/channel-rank.md) |
| 平台链接（支付 / 退款 / 毛利率 / 推广费） | [references/platform-link.md](./references/platform-link.md) |
| 售后补发商品 / 原子 SKU | [references/after-sales-and-atomic.md](./references/after-sales-and-atomic.md) |
| 旧版含税净利（2026-04 之前） | [references/net-profit-old.md](./references/net-profit-old.md) |
| 新版税后净利（价税分离 2026-04 起） | [references/net-profit-new.md](./references/net-profit-new.md) |
| **T+1 净利核算**（凭证科目 / 费用分摊 / V2 汇总 / EP 编码 / 业务上传 / 跨境分摊 / 差异排查） | [references/t1-net-profit-rules.md](./references/t1-net-profit-rules.md) |
| **das-core 代码实现**（Java 净利引擎公式 / 税费计算 / 科目层级 / Apollo 配置 / 调度流程 / 产销处理） | [references/das-core-implementation.md](./references/das-core-implementation.md) |
| **das-core SQL 查询**（Mapper XML 结构 / SQL 片段 / EP 编码 SQL 映射 / 过滤条件 / 新旧版本对比） | [references/das-core-sql-queries.md](./references/das-core-sql-queries.md) |

---

## 表名速查

### 老板报表核心表

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
| 推广费用明细 | `dp_ods.doris_ods_upload_expense_detail` |
| 净利 V2 | `doris_app_net_profit_check_report_v2` |
| 国内费用-分摊成功 | `doris_dws_finance_cost_sbjct` |
| 国内费用-分摊失败 | `doris_dws_finance_cost_sbjct_failure` |
| 费用采集策略 | `doris_dim_fms_support_subject` |
| 科目关系 | `doris_dim_expense_subject_relation` |
| 月度部门人力成本 | `tmp_data.month_department_employee_cost` |
| 部门绩效目标 | `das_core.performance_objectives` |
| SKU 目标销量 | `dp_ods.doris_ods_SKU_estimate_sales` |
| 上年历史 | `last_year2022_*` |
| 财年同期增长率 | `tmp_date.year_income_rate` |
| 货主 / 店铺主数据 | `oms_business.shop`、`dp_dim.doris_dim_srm_supplier_supplier` |

### T+1 净利核心表

| 用途 | 表名 | 说明 |
|---|---|---|
| 凭证科目中间表 | `doris_dws_voucher_subject_mid` | voucher + voucher_detail + accounting_dimension + subject + cost_gather_strategy 关联生成；每日回刷最近 45 天 |
| 科目费用分摊成功 | `dp_dws.doris_dws_finance_cost_sbjct` | 承接凭证、费用明细、单据费用、人资薪酬、系统单、分销单、跨境订单分摊结果 |
| 科目费用分摊失败 | `dp_dws.doris_dws_finance_cost_sbjct_failure` | 分摊依据找不到时进入 |
| 净利 V2 汇总 | `doris_app_net_profit_check_report_v2` | 按 dt + 货主 + 店铺 + SKU + 供应商等维度输出收入/成本/费用金额 |
| 供应商采购占比 | `dp_dws.doris_dws_srm_purchase_num_percentage_mid` | SKU 金额/成本/体积分摊到供应商的主依据 |
| 国内费用明细 | `doris_ods_upload_expense_detail` | 收入取 `income_cost`，支出取 `expend_cost`，限制 `occurrence_type=1` |
| 跨境费用明细 | `expense_detail_cb` | 跨境订单关联窗口 3 个月 |
| 费用采集策略 | `doris_dim_fms_support_cost_gather_strategy` | `cost_belong`：1=收入(加法)、2=成本(减法)、3=费用(减法) |

## 字段速查

### 老板报表通用字段

| 字段 | 含义 |
|---|---|
| `sales_amount` | 销售/支付金额 |
| `refund_amount` | 退款金额（已发货退款） |
| `undelivery_refund_amount` | 未发货退款金额 |
| `paid_num` / `refund_num` | 支付/退款数量 |
| `estimate_cost` / `estimate_refund_cost` | 线上分销（代销）下的供货成本/供货退款成本 |
| `estimate_brand_quotation` / `refund_brand_quotation` | 线上分销（代销）下的供货总额/退款总额 |
| `yst_delivery_num` | 昨日发货数量（库存表） |
| `tax_freight_price` / `no_tax_freight_price` | 含税含运/不含税含运采购价 |
| `goods_type` | 1 = 销售货品 |
| `judge_combine` | 2 = 单品 |
| `item_type` | 商品类别（清仓品 / 正常品 / 瑕疵品 …） |
| `is_valid_goods_with_sale_goods` | 2 = 有效，1 = 无效 |
| `warehouse_use_type` | 1 销售仓 / 2 代发仓 / 4 委外仓 |
| `country_type` | 1 = 国内 |
| `business_type` | 2 = TOC |
| `sales_model` | 销售模式：2 线上直销，3 线下分销，4 平台入仓分销，5 线上分销（代销），6 线下零售/直销，7 线上分销（经销），8 线上代销，9 贴牌代工 |

### T+1 净利专用字段

| 字段 | 含义 |
|---|---|
| `cost_share_method` | 分摊方式：0=按销售收入、1=按销售成本、2=按发货方量 |
| `cost_belong` | 费用归属：1=收入(正号)、2=成本(负号)、3=费用(负号) |
| `expense_code` | 费用编码（EP001-EP037，详见下节） |
| `expense_amount` | 费用金额 |
| `no_tax_amount` | 不含税费用金额 |
| `tax_amount` | 税额 |
| `income_cost` | 费用明细表收入金额 |
| `expend_cost` | 费用明细表支出金额 |
| `occurrence_type` | 费用明细类型：1=实际发生 |
| `cost_type` | 费用粒度：0=店铺级、1=订单级、2=链接级、3=订单+链接级 |
| `trans_dt` | 费用发生日期 |
| `sub_logistics_cost_fee` | 子单预估物流费 |
| `sub_agent_delivery_fee` | 子单预估代发费 |
| `product_cost` / `purchase_cost` | 含税净利成本 |
| `no_tax_product_cost` | 不含税净利成本 |
| 费用来源标识 | 0=费用账单detail、1=凭证科目中间表、2=单据费用index、3=薪酬费用 |

---

## 费用编码字典（EP001-EP037）

| 编码 | 名称 | 科目编码 |
|---|---|---|
| EP001 | 销售收入（已减退款） | 从数仓关联科目表获取，限制账套=4 |
| EP002 | 净利成本含税（已乘下单数量） | — |
| EP003 | 不含税成本（已乘下单数量） | — |
| EP004 | 快递自发费 | 6601.36 |
| EP005 | 快递代发费 / 仓储服务费 | 6601.36, 6601.51 |
| EP006 | 耗材费 | 6601.62 |
| EP007 | 退货挽损 | 6601.49.04 |
| EP008 | 售后补贴 | 6601.54 |
| EP009 | 管理费用（税金） | 6602.38 |
| EP010 | 人工费用（职工薪酬） | 6602.01 |
| EP011 | 分摊费用 | 6601.41 |
| EP012 | 研发费用 | 6602.35；>= 2025-04-01 有历史数据 |
| EP013 | 其他费用 | 虚拟编码（财务无法提供科目编码时使用） |
| EP014 | 集团管理费用 | 6602.03.05 |
| EP015 | 供应链管理费 | 6601.39 |
| EP016 | 销售费用_宿舍费 | 6601.03.02 |
| EP017 | 管理费用_宿舍费 | 6602.03.03 |
| EP018 | 销售费用_工位费 | 6601.03.03 |
| EP019 | 管理费用_工位费 | 6602.03.02 |
| EP020 | 直播间使用费 | 6602.03.04 |
| EP021 | 影棚使用费 | 6601.41.03 |
| EP022 | 电服/物流服务费 | 6601.41.02 |
| EP023 | 客服管理费/客服服务费 | 6601.41.04 |
| EP024 | 售后服务费 | 6601.41.01 |
| EP025 | 业务协作费（SA 成本） | 6601.45 |
| EP026 | 平台佣金 | 6601.47.01 |
| EP027 | 品牌宣传费 | 6602.50 |
| EP028 | 不含税收入（减退款） | — |
| EP029 | 销项税额（减退款） | 2221.01.01 |
| EP030 | 进项税额（成本） | 2221.01.02 |
| EP031 | 不含税卖家运费 | 6601.36 |
| EP032 | 不含税仓储服务费 | 6601.51 |
| EP033 | 卖家运费进项税额 | — |
| EP034 | 代发费进项税额 | — |
| EP035 | 包装耗材费进项税额 | — |
| EP036 | 不含税包装耗材费 | 6601.62 |
| EP037 | 其他进项税额（费用） | 代码中归入"进项税额（费用）" |

---

## 公式记忆速查

### 老板报表通用公式

| 业务概念 | 公式 |
|---|---|
| 不区分销售模式收入 | `sum(sales_amount)` |
| 区分销售模式收入 | 线上分销(代销): `sum(estimate_brand_quotation)`；其他: `sum(sales_amount)` |
| 不区分销售模式金额(减退款) | `sum(sales_amount - refund_amount)` |
| 区分销售模式金额(减退款) | 线上分销(代销): `sum(estimate_cost - estimate_refund_cost)`；其他: `sum(sales_amount - refund_amount)` |
| 含税毛利率 | `1 - sum(含税采购成本) / sum(财务销售收入)` |
| 不含税毛利率 | `1 - sum(不含税采购成本) / sum(财务销售收入)` |
| 7 日环比 | `(过去 7 天 - 过去 7~14 天) / 过去 7~14 天`，其中过去 7~14 天 = 过去 14 天 - 过去 7 天 |
| 件均价 | `近 30 日收入 / 近 30 日销量`，四舍五入取整 |
| 可发天数 | `总库存 / 加权日均出库`，向上取整；加权日均出库 = `7 日/7*60% + 14 日/14*40%` |
| 库存金额（销售仓） | `总库存 * 不含税月度成本价`，月度成本价为空/0 取不含税含运采购价 |
| 库存金额（代发仓） | `总库存 * 不含税含运采购价` |
| 全仓库存金额 | 自营仓 + 代发仓 |
| 清仓品库存金额 | 淘汰品 + 瑕疵品 + 停止下单品 |
| 已发货退款率 | `已发货退款金额 / 收入(不减退款)` |
| 未发货退款率 | `未发货退款金额 / 支付金额(不减退款)` |
| 推广费比 | `推广费用 / 发货收入(已减退款)`；推广费用 = `expense_detail 支出 - 收入` |
| 人均日产 | `近 30 日销售收入 / 30 / 实时在岗人数`，向上取整 |
| 1 元人力产出 | `上月收入 / 人力成本总额`，四舍五入保留两位 |
| 人力成本占比 | `1 / 一元人力产出` |
| SKU 日产 | `近 30 日支付金额(已减退款) / 有效 SKU 数 / 30`，向上取整；分子不区分销售模式 |
| 月/年完成率 | 发货收入(减退款) / 绩效目标 |
| 月同比 | `(上月收入 - 同比月收入) / 同比月收入` |
| 同期增长率 | `(本财年收入 - 去年财年同期收入) / 去年财年同期收入` |
| 本年预测收入 | `本年财年收入 + (去年财年收入 * (1 + 同期增长率) - 本年财年收入)` |
| 周转天数 | `货主总库存 / 加权日均出库`，向上取整，限销售仓 + 代发仓 |
| 单均价 | `已付金额(不减退款) / 去重原始单量`，四舍五入保留两位 |
| 财年已交付采购额 | `sum(actual_receive_num * 不含税含运采购单价)` |
| 财年未交付采购额 | `sum(uncollected_num * 不含税含运采购单价)` |
| 税后净利 | `利润总额 - 所得税` |
| 所得税（非产销） | `max((利润总额 - 税金及附加 - 其他税金 + 销售费用无票) * 0.15, 0)`，其中其他税金 = 水利建设基金 + 印花税 |
| 所得税（包含产销） | `max((利润总额 - 税金及附加 - 其他税金 - 产销不含税收入 + 销售费用无票) * 0.15, 0)` |
| 利润总额（非产销） | `V2 不含税收入 + 2 个费用表不含税收入 - V2 不含税成本 - 2 个费用表成本 - 2 个费用表费用 - V2 表费用 - 税金及附加 - 水利建设基金 - 印花税(买卖合同)` |
| 水利建设基金 | `(EP028 + 6001.99 + 6051.03) * 0.05%` |
| 印花税买卖合同 | `(EP028 + 6001.99 + 6051.03 + 6401.99 + EP003) * 0.0003` |
| 应交增值税 | `销项税额 - 进项税额(成本) - 进项税额(费用)` |
| 税金及附加 | `应交增值税 * 0.12` |

### T+1 净利专用公式

| 业务概念 | 公式 |
|---|---|
| 费用金额（国内费用明细） | `income_cost - expend_cost`，限制 `occurrence_type=1` |
| 科目费用正负号 | 费用归属=收入 → 正数；费用归属=成本/费用 → 负数 |
| 供应商采购占比分摊 | SKU 金额 * 供应商占比；未命中时兜底到第一个非瑕疵品供应商（排除 `G100197`） |
| 本月每日人工费用 | `临时表上月费用 / 本月天数`；当前月缺失时取最新上传月份 / 目标月份天数 |
| 本月每日集团管理费 | `临时表上月费用 / 本月天数` |
| 费比类费用 | `SKU 收入/成本/体积基础 * 上传的店铺粒度费比值`；费用金额优先于费比 |
| 退货挽损 | `销售收入(已减退款) * 分销商损失挽回比例`，比例来源 `sms_product.distributor` |
| 售后补贴 | `销售收入(已减退款) * 分销商售后补贴比例` |
| 天猫超市兜底 | 无收入/成本/体积基础时按发货数量占比分摊；无发货数量时按发货 V1 中该店铺 SKU 均分 |

---

## T+1 差异排查清单

核对或排查 T+1 净利差异时，优先检查：

1. **日期口径**：费用发生日期、发货日期、业务发生日期是否混用。
2. **回刷窗口**：最近 45 天、上月 8 号回刷，或特殊 5 号/7 号回刷。
3. **国内/跨境过滤**：计算跨境指标时是否去掉跨境限制。
4. **排除条件**：产销事业群、`班牛`、`佳帮手分销旗舰店XX【业务公共】`。
5. **供应商分摊**：采购占比表命中率，是否正确兜底到第一个非瑕疵品供应商。
6. **分摊方式**：是否按 `cost_share_method` 使用收入、成本或发货方量。
7. **费用来源标识**：费用 detail(0)、凭证科目(1)、单据费用 index(2)、薪酬费用(3) 是否区分正确。
8. **上传数据**：空值转 0、费用金额优先于费比、研发费用仅允许费用金额。
9. **天猫超市**：没有收入/成本/体积基础时是否按发货数量占比兜底。
10. **失败表**：无法分摊的数据是否进入 `doris_dws_finance_cost_sbjct_failure`。

---

## 使用约定

1. 回答指标问题前，**先指明该指标所在的页面**（清仓品 / 排行榜 / 部门 / 公司大屏 / 供应商 / 渠道 / 平台链接 / 净利 / T+1 净利），不同页面下同名指标的库表与限定逻辑可能不同。
2. 引用公式时**带上库表名 + 限定逻辑**（如"限制销售货品""排除班牛平台""仓库功能 in (1,2)"），避免给出残缺答案。
3. 若用户问"实时 / 历史 哪个口径"，直接按 [references/global-rules.md](./references/global-rules.md) 第 4 条与各页面文档区分。
4. 净利相关指标默认走**新版税后净利**逻辑（[net-profit-new.md](./references/net-profit-new.md)），仅当明确询问"老版含税净利"或时间在 2026-04 之前才走 [net-profit-old.md](./references/net-profit-old.md)。
5. T+1 净利的费用分摊细节（分摊层级、兜底逻辑、跨境差异等）统一查 [t1-net-profit-rules.md](./references/t1-net-profit-rules.md)。
6. 涉及具体 SQL 时，必须遵守各页面文档中的费用 / 科目排除清单（subject_code、cost_code 黑名单）。
7. T+1 差异排查时，按上方"差异排查清单"逐条检查。
8. 涉及 das-core 代码实现细节（如"系统怎么算净利的""SQL 怎么查的""Apollo 配置了什么"）时，先读 [das-core-implementation.md](./references/das-core-implementation.md) 和 [das-core-sql-queries.md](./references/das-core-sql-queries.md)。
9. 产销相关问题需区分三种模式（NeTProfitCalcTaxTypeEnum）：全是产销(PRODUCTION_AND_SALES)、包含产销(PRODUCTION_AND_SALES_EXISTS)、不含产销(IGNORE)，不同模式下税费和所得税计算逻辑不同。
