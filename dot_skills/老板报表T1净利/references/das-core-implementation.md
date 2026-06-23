# das-core 代码实现参考（T+1 净利核算引擎）

> 来源：`das-core` Java 项目（Spring Boot 2.0.2，8 Maven 模块，1381 个 Java 文件）。
> 核心文件：`MonitorNetProfitDetailSupport.java`（112.7KB 净利计算引擎）、`MonitorNetProfitDetailMapper.xml`（39.8KB 核心 SQL）、`ExpenseParser.java`（22.2KB 对比弹窗构建）。

## 项目架构概览

das-core 是老板报表和 T+1 净利核算的后端服务，包含 8 个 Maven 模块：

| 模块 | 文件数 | 职责 |
|---|---|---|
| common | 58 | 工具类、常量、配置读取 |
| dao | 266 | MyBatis Mapper、数据库访问 |
| domain | 94 | 领域模型 |
| interface | 451 | 对外接口、枚举、DTO |
| model | 304 | 数据模型 |
| scheduler | 15 | 定时任务调度 |
| service | 138 | 核心业务逻辑 |
| web | 55 | Controller 层 |

数据源注解：`@DataSource(DataSourceType.DORIS)` 标识所有数仓查询走 Doris。

## 核心数据流

```
前端请求参数
  → buildSearchBo（构建查询条件）
  → handleQueryParam（按页面类型处理参数）
  → searchProfit / searchContrastProfit（查询 Doris 数据）
  → buildNetProfitDetailResponseV2/V3（计算并组装响应）
  → 返回前端
```

## 净利计算公式（代码实现）

### 单页面净利（getNetProfitV1）

```java
netProfitAmount = amount              // 收入总计（已含收入类科目的negate处理）
                - purchasePriceTotal   // 采购成本
                - SUM(所有根级科目expense)  // 根级科目 = subjectCode不含"."的
```

### 弹窗对比净利（getNetProfit）

```java
netProfitAmount = response.getAmount()          // 收入
                - response.getPurchasePriceTotal()  // 成本
                + SUM(收入类科目金额)              // incomeSubjectCode包含的科目 → 加
                - SUM(非收入类科目金额)            // 其他科目 → 减
```

### 最终净利（弹窗对比版）

```java
baseNetProfit = getNetProfit(response, subjectAmount, incomeSubjectCode)
netProfit = baseNetProfit - taxAmountAdd（税金及附加） - otherTaxAmount（其他税金）
afterTaxNetProfit = netProfit - incomeTaxAmount（所得税）
```

### 净利比率

- **V1版（单页面）**：`rate = 100% - 成本占比% - 各费用科目占比%`（逐项从100扣减）
- **V2版（弹窗对比）**：`afterTaxNetProfitRate = netProfitRate（利润总额占比） - incomeTaxAmountRate（所得税占比）`

## 税费计算逻辑（代码实现）

### 增值税（应交增值税）

```java
vatPayableAmount = outputTaxAmount（销项税额，取extAmount["销项税额"]）
                 - costInputTaxAmount（进项税额_成本，= extAmount["进项税额（成本）"] + filterTaxAmount）
                 - expenseInputTaxAmount（进项税额_费用，= extAmount["进项税额（费用）"] + taxAmount - filterTaxAmount）
```

其中 `filterTaxAmount` 是科目 `2221.04.01.01`（应交税费-应交增值税-进项税额）的税额。
`taxAmount` 来自分摊成功表 `doris_dws_finance_cost_sbjct.tax_amount` 字段。

### 税金及附加

```java
if (vatPayableAmount != 0) {
    taxAmountAdd = vatPayableAmount * 0.12
}
// 税率 12% = 城建税7% + 教育费附加3% + 地方教育费附加2%
```

### 水利建设基金

```java
waterConservancyFund = (不含税收入 + 6001.99 + 6051.03) * 0.0005
// 税率 0.05%（万分之五）
// 产销模式下（PRODUCTION_AND_SALES）返回 0
```

### 印花税（买卖合同）

```java
stampDuty = (不含税收入 + 6001.99 + 6051.03 + 6401.99 + 不含税成本) * 0.0003
// 税率 0.03%（万分之三）
// 产销模式下（PRODUCTION_AND_SALES）返回 0
```

### 其他税金

```java
otherTaxAmount = waterConservancyFund + stampDuty
// 产销模式下为 0
```

### 所得税

三种场景（由 `NeTProfitCalcTaxTypeEnum` 控制）：

| 枚举值 | 含义 | 所得税计算 |
|---|---|---|
| `PRODUCTION_AND_SALES`（值=2） | 全是产销数据 | `incomeTaxAmount = 0` |
| `IGNORE`（值=0） | 不包含产销数据 | `incomeTaxAmount = max(利润总额 * 0.15, 0)` |
| `PRODUCTION_AND_SALES_EXISTS`（值=1） | 包含产销数据 | `incomeTaxAmount = max((利润总额 - 产销不含税收入) * 0.15, 0)` |

**所得税基数特殊处理**（公司/部门/渠道维度）：
按店铺粒度重新计算净利作为所得税基数（`buildIncomeTaxNetProfitBaseMapByShop`），仅累加净利 >= 0 的店铺。

**所得税基数计算公式**：
```java
baseNetProfit = getNetProfit(response, subjectAmount, incomeSubjectCode)
result = baseNetProfit - taxAmountAdd - otherTaxAmount + salesNoTicketExpenseAmount
// 注意：销售无票费用（6601.98）加回基数
```

## EP 费用编码在代码中的映射

### 汇总查询（queryProfitSubjectDetail）

| EP编码 | SQL映射标签 | 备注 |
|---|---|---|
| EP001 | "收入" | 含税收入 |
| EP002 | "成本" | 含税成本 |
| EP003 | expense取0 | 避免重复计入成本 |
| 其他 | 取维表 `b.subject_code` | 通过 `doris_dim_expense_subject_relation` 关联 |

### 对比查询（queryProfitSubjectContrastDetail）— 非税科目段

| EP编码 | SQL映射标签 |
|---|---|
| EP001 | "收入" |
| EP002 | "成本" |
| EP004/005/006/028/029/030/033/034/035/037 | 被排除（在税科目段处理） |
| 其他 | 取维表 subject_code |

### 对比查询 — 税科目段（UNION ALL 第二段）

| EP编码 | SQL映射标签 | 含义 |
|---|---|---|
| EP001 | "含税收入" | 含税总收入 |
| EP028 | "不含税收入" | 剔除税额后的收入 |
| EP029 | "销项税额" | 销售侧税额 |
| EP003 | "不含税成本" | 剔除税额后的成本 |
| EP030 | "进项税额（成本）" | 采购成本侧进项税 |
| EP033 | "进项税额（费用）" | 卖家运费进项税额 |
| EP034 | "进项税额（费用）" | 代发费进项税额 |
| EP035 | "进项税额（费用）" | 包装耗材费进项税额 |
| EP037 | "进项税额（费用）" | 其他进项税额 |

### 产销临时表映射

| field_code | 汇总查询标签 | 对比查询标签 |
|---|---|---|
| EP001 | "收入" | "不含税收入_产销" |
| EP003 | "不含税成本_产销" | "不含税成本_产销" |

## 额外科目与计算科目

### 额外科目（放入 extAmount，不计入费用科目树）

```java
EXTRA_SUBJECT_CODES = {
    "含税收入", "不含税收入", "销项税额",
    "不含税成本", "进项税额（成本）", "进项税额（费用）",
    "不含税收入_产销", "不含税成本_产销"
}
```

### 计算科目（同时放入 extAmount 和 subjectAmount）

```java
CALC_SUBJECT_CODE = {"6601.98", "6001.99", "6051.03", "6401.99"}
```

| 科目代码 | 含义 | 在代码中的用途 |
|---|---|---|
| 6001.99 | 主营业务收入-其他 | 水利建设基金/印花税计算基数 |
| 6051.03 | 其他业务收入-其他 | 水利建设基金/印花税计算基数 |
| 6401.99 | 主营业务成本-其他 | 印花税计算基数 |
| 6601.98 | 销售费用-无票费用 | 所得税基数调整项 |
| 6602.35 | 管理费用-研发费用（默认） | 集团研发费用科目（Apollo可配） |
| 2221.04.01.01 | 应交税费-应交增值税-进项税额 | 税额过滤特殊处理 |

## 科目层级解析

科目编码采用点号 `.` 分隔的多级编码（如 `6601.01.02`），代码按以下方式构建层级：

1. 按 `.` 拆分编码：`6601` → `6601.01` → `6601.01.02`
2. 逐级累加金额到 `subjectAmount`
3. 建立父子关系到 `subjectRelation`
4. 一级科目加入 `rootSubjects`

**根级科目判定**：`subjectCode` 不含 `.` 的为根级科目，在 `getNetProfitV1` 中作为减项。

## 费用分摊实现

### 费用分摊规则（CostShareRuleEnum）

| 枚举值 | 值 | 含义 |
|---|---|---|
| SHARE_BY_SALES_AMOUNT | 1 | 按销售额分摊 |
| SHARE_BY_COST_PRICE | 2 | 按成本价分摊 |
| EQUAL_SHARE | 3 | 均分 |

### 分摊场景（ShareSceneEnum）

| 枚举值 | 值 | 含义 |
|---|---|---|
| ORDER_NO_SPU | 1 | 订单无SPU |
| ORDER_COST_SHARE_TO_SPU | 2 | 订单费用分摊至SPU |
| SHOP_COST_SHARE_TO_SPU | 3 | 店铺费用分摊至SPU |
| LINK_COST_SHARE_TO_SPU | 4 | 链接费用汇总分摊至SPU |
| LOGISTICS_COST_SHARE_TO_SPU | 5 | 物流费用分摊至SPU |
| SPU_SHARE_TO_OID | 6 | SPU分摊至OID |
| OID_TO_SYSTEM_SUB_ORDER | 7 | OID分摊至系统单子单 |

### 分摊数据来源三层架构

```
第一层: 费用科目分摊（cost_share）
  doris_dws_finance_cost_sbjct（正常）→ share / no_tax_amount / tax_amount
  doris_dws_finance_cost_sbjct_failure（异常/失败）→ result_amount，排除 business_group=6

第二层: 净利核对报表（check_report_v2）
  doris_app_net_profit_check_report_v2 → expense_code → 维表映射科目
  区分 税/非税 两套 UNION ALL

第三层: 产销临时表（业务上传）
  tmp_data.sales_production_revenue_profit → shipping_month 过滤
  EP001=收入，EP003=成本
```

## 产销数据处理

### 产销查询触发条件

- **公司维度 + ALL组**：`searchTmp=true`，查主表 UNION 产销表
- **公司维度 + PRODUCTION_SALE组**：单独查产销表
- **部门维度**：按货主是否属于产销货主（`MonitorConfig.getOwnerProductionOwnerCodes()`）分开查询

### 产销对税费的影响

- 水利建设基金/印花税在 `PRODUCTION_AND_SALES` 模式下为 0
- 所得税在 `PRODUCTION_AND_SALES_EXISTS` 模式下需扣除产销不含税收入
- 产销 EP001 映射为 "不含税收入_产销"，EP003 映射为 "不含税成本_产销"

## 跨境处理逻辑（代码实现）

### 国别过滤

| countryType | SQL条件 | 分摊表条件 |
|---|---|---|
| 1（国内） | `country_type = 1` | `country_code = 'CN'` |
| 2（跨境） | `country_type != 1` | `country_code != 'CN'`（含NULL） |

### 跨境限制

- 跨境不查研发费用
- 跨境不查税额
- 跨境不查对比明细
- 非 COMPANY/OWNER 的跨境请求直接返回空（`checkSearchDomestic`）

## 研发费用计算

数据源：`tmp_data.other_expense_data`，`cost_type = '研发费用'`，起始日期 `2025-04-01`。

| 时间维度 | 计算逻辑 |
|---|---|
| 昨日 | 月研发费用 / 月总天数 |
| 本月 | (月研发费用 / 月总天数) * 已过天数 |
| 上月 | 上月整月研发费用 |
| 财年 | 财年历史每月费用之和 + 本月按天折算 |

触发条件：`dataType=COMPANY` + `dataGroup=ALL` + 非跨境。

## 数据同步调度（syncMultiAnalysisAllData）— MQ 异步架构（2026-06 重构）

### 整体架构变更

原来的"进程内同步执行"已重构为"MQ 消息驱动的异步解耦架构"：

```
XXL-Job 调度触发
  → syncMultiAnalysisAllData（轻量入口，只发 MQ 消息）
  → FanoutExchange 广播消息
  → SyncMultiAnalysisAllDataConsumer（消费端）
  → syncMultiAnalysisAllDataByMag（实际执行多维数据同步）
  → SKU 计算通过 SkuCalcSendMsgSupport 发送 MQ 到 das-batch 异步执行
  → das-batch 计算完成后统一发送钉钉通知
```

### 入口方法（MonitorNetProfitDetailSupport）

- `syncMultiAnalysisAllData`：轻量级方法，只往 FanoutExchange 发送一条 MQ 消息即返回。**不再同步执行数据计算**。
- `syncMultiAnalysisAllDataByMag`：实际执行多维报表数据同步的方法（公司/部门/店铺/供应商/渠道/达人/原子SKU/平台链接）。由消费者调用。

### 多维数据同步任务（在 syncMultiAnalysisAllDataByMag 中并行执行）

1. 公司销售大屏 → `monitorCompanySalesService.sumMonitorCompanySalesData`
2. 部门 → `monitorOwnerService.syncOwnerSales`
3. 店铺 → `monitorShopService.sync`
4. 供应商 → `monitorSupplierService.syncSupplierSales`
5. 渠道 → `monitorChannelService.sync`
6. 达人 → `monitorAuthorService.sync`
7. 原子SKU → `monitorAtomicSkuService.monitorCalcAtomicSku`
8. 平台链接 → `monitorPlatSpuService.sync`
9. ~~SKU基础数据~~ → **已剥离至 das-batch**，通过 MQ 消息 `das-core_sku_batch_queue_das-batch` 异步执行

### SKU 计算异步化

- **SkuCalcSendMsgSupport**（新增组件）：统一的 SKU 批量计算消息发送入口，通过 `MQSendManager.getMessageSender(MQPlateEnum.OMS)` 发送到队列 `das-core_sku_batch_queue_das-batch`（Direct Exchange 模式）。
- **DasCoreSkuBatchMessageBO**（新增消息体）：
  - `msgId`：消息唯一 ID（SnowFlake 生成）
  - `dates`：需要计算的日期列表
  - `isTodayCalc`：是否计算当天（区分定时触发 vs 历史补数）
  - `isJobSync`：是否由定时 Job 触发
  - `preCalcResult`：前置任务（供应商/渠道/达人等）是否全部成功
  - `content`：预生成的钉钉通知文案

### 消费者（SyncMultiAnalysisAllDataConsumer）

- 监听队列 `${sync.multi.analysis.all.data.queue}`
- 使用**手动 ACK**（`channel.basicAck`），确保消息成功处理后才确认
- 通过 `@Conditional(Load.class)` 条件加载，由 Apollo 配置 `rabbit.consumer.enable` 控制开关
- 收到消息后调用 `syncMultiAnalysisAllDataByMag` 执行实际数据同步

### GoodsMonitorJob（XXL-Job：monitorSkuDataCalc）

- **之前**：在进程内用 `CompletableFuture` 并行跑 SKU 计算，等待结果后发钉钉通知
- **之后**：通过 `SkuCalcSendMsgSupport.senMessage()` 发送 MQ 消息，方法直接返回 SUCCESS，不再等待计算结果
- 钉钉通知时机延迟到 das-batch 端 SKU 计算完成后统一发送
- 通知文案通过 `MonitorNotifySupport.getContent()` 提前生成，随消息传递

### FanoutExchange 配置

- Exchange 类型：**FanoutExchange**（广播模式，支持多消费者扩展）
- Exchange 名：Apollo 配置 `sync.multi.analysis.all.data.exchange`，默认 `sync_multi_analysis_all_data_exchange`
- Queue 名：Apollo 配置 `sync.multi.analysis.all.data.queue`

### 执行时机

- 周一：同步前3天（周六、周日、周一）
- 其他：同步当天
- 可指定日期范围

### 钉钉通知

- Token + Secret + Keyword 从 Apollo 配置读取
- 通知文案由 `MonitorNotifySupport.getContent(Date syncStartDate, Date syncEndDate)` 根据时间段生成
- 发送时机：das-batch 端 SKU 计算完成且 `isJobSync=true` 且 `preCalcResult=true` 时才发送

## Apollo 配置项

| Apollo Key | 常量名 | 默认值 | 用途 |
|---|---|---|---|
| `monitor.exclude.subject.codes` | MULTI_ANALYSIS_NET_PROFIT_EXCLUDE_SUBJECT | 空 | 排除的科目编码（逗号分隔） |
| `monitor.exclude.cost.codes` | MULTI_ANALYSIS_NET_PROFIT_EXCLUDE_COST | 空 | 排除的费用编码（逗号分隔） |
| `monitor.company.expense.subject.code` | MULTI_ANALYSIS_COMPANY_GROUP_EXPENSE_SUBJECT_CODE | `6602.35` | 集团研发费用科目编码 |
| `net.profit.detail.config` | NET_PROFIT_DETAIL_CONFIG | 空 | 净利明细配置JSON |
| `shop.profit.detail.note.dy` | SHOP_NET_PROFIT_DETAIL_NOTE_DY | 空 | 抖音店铺净利明细注释 |
| `shop.profit.detail.note.jdzy` | SHOP_NET_PROFIT_DETAIL_NOTE_JDZY | 空 | 京东直营店铺净利明细注释 |
| `shop.profit.detail.note.other` | SHOP_NET_PROFIT_DETAIL_NOTE_OTHER | 空 | 其他店铺净利明细注释 |
| `monitor.channel.mapping` | MONITOR_CHANNEL_MAPPING | 空 | 渠道映射SQL片段 |
| `monitor.owner.sales.production.owner` | MONITOR_OWNER_SALES_PRODUCTION_OWNER | 空 | 产销货主编码列表 |
| `monitor.owner.sales.production.exclude.subject.code` | MONITOR_OWNER_SALES_PRODUCTION_EXCLUDE_SUBJECT_CODE | 空 | 产销排除科目编码 |
| `monitor.owner.production.income.owner` | MONITOR_OWNER_PRODUCTION_INCOME_OWNER | 空 | 产销收入货主编码 |
| `monitor.spu.sales.modes` | MONITOR_SPU_SALES_MODES | 空 | SPU销售模式列表 |
| `monitor.exclude.shop.codes` | MONITOR_SHOP_EXCLUDE_CONFIG | 空 | 排除店铺编码 |
| `company.management.exclude.shopCodes` | COMPANY_MANAGEMENT_EXCLUDE_SHOP_CONFIG | 空 | 公司管理排除店铺 |
| `company.management.exclude.query.platCodes` | COMPANY_MANAGEMENT_EXCLUDE_QUERY_PLAT_CONFIG | 空 | 公司管理排除平台 |
| `company.management.exclude.query.owner` | COMPANY_MANAGEMENT_EXCLUDE_OWNER_CONFIG | 空 | 公司管理排除货主 |
| `sync.monitor.notify.dingding.secret` | SYNC_MONITOR_NOTIFY_DINGDING_SECRET | 空 | 同步完成通知钉钉secret |
| `sync.monitor.notify.dingding.token` | SYNC_MONITOR_NOTIFY_DINGDING_TOKEN | 空 | 同步完成通知钉钉token |
| `monitor.category.calc.days` | MONITOR_CATEGORY_CALC_DAYS | 空 | 类目计算天数 |
| `monitor.spu.calc.days` | MONITOR_SPU_CALC_DAYS | 空 | SPU计算天数 |
| `monitor.shop.calc.days` | MONITOR_SHOP_CALC_DAYS | 空 | 店铺计算天数 |
| `monitor.channel.calc.days` | MONITOR_CHANNEL_CALC_DAYS | 空 | 渠道计算天数 |
| `monitor.sku.calc.days` | MONITOR_SKU_CALC_DAYS | 空 | SKU计算天数 |
| `monitor.supplier.calc.days` | MONITOR_SUPPLIER_CALC_DAYS | 空 | 供应商计算天数 |
| `monitor.owner.calc.days` | MONITOR_OWNER_CALC_DAYS | 空 | 货主计算天数 |
| `sync.multi.analysis.all.data.exchange` | SYNC_MULTI_ANALYSIS_ALL_DATA_EXCHANGE | `sync_multi_analysis_all_data_exchange` | 多维数据同步 FanoutExchange 名称 |
| `sync.multi.analysis.all.data.queue` | — | — | 多维数据同步消费队列名称 |
| `rabbit.consumer.enable` | — | — | 消费者开关（Load 条件加载） |

## 时间区间定义

| 字段枚举 | 开始时间 | 结束时间 |
|---|---|---|
| yesterdayNetProfitAmount | 昨天 00:00:00 | 昨天 23:59:59 |
| monthlyNetProfitAmount | 本月1号 00:00:00 | 昨天 23:59:59 |
| lastMonthlyNetProfitAmount | 上月1号 00:00:00 | 上月最后一天 23:59:59 |
| fiscalNetProfitAmount | 财年起始日 | 昨天 23:59:59 |
| last3DaysNetProfitAmount | 3天前 00:00:00 | 昨天 23:59:59 |
| last7DaysNetProfitAmount | 7天前 00:00:00 | 昨天 23:59:59 |
| last30DaysNetProfitAmount | 30天前 00:00:00 | 昨天 23:59:59 |
| last365DaysNetProfitAmount | 365天前 00:00:00 | 昨天 23:59:59 |

净利起始日期常量：`MULTI_ANALYSIS_NET_PROFIT_START_DATE = "2025-04-01"`（2025-04 发货口径起点）。
不含税净利起始日期：`MULTI_ANALYSIS_NOT_TAX_NET_PROFIT_START_DATE = "2026-04-01"`（价税分离口径起点）。

## 金额格式化处理

- **公司/部门/渠道/店铺**（及非昨日的达人）：`BigDecimalUtil.handleResultTenThousand`（万元化处理）
- **其他（SKU/SPU/供应商/链接等）**：保留2位小数，四舍五入（HALF_UP）

## SQL 查询通用过滤条件（whereCondition）

所有查询共享以下动态过滤条件：

| 参数 | 字段 | 说明 |
|---|---|---|
| netProfitStartDate + dateEnd | `a.dt BETWEEN ... AND ...` | 日期范围 |
| authorId | `a.author_id` | 负责人 |
| shopCodes | `a.shop_code IN (...)` | 店铺列表 |
| excludePlatCodes | `a.shop_plat_code NOT IN (...)` | 排除平台 |
| platSpuIds | `a.plat_spu_id IN (...)` | 平台SPU |
| ownerCodes | `a.owner_code IN (...)` | 货主 |
| supplierCodes | `a.supplier_code IN (...)` | 供应商 |
| skuCodes | `a.sku_code IN (...)` | SKU |
| spuCodes/categories/isSelfResearch | EXISTS子查询 | 关联 `doris_dim_sku_dynamic_sales` 商品属性过滤 |
| businessGroup | `a.business_group IN (...)` | 业务组列表 |
| salesModelList | `a.sales_model IN (...)` | 销售模式列表 |
| excludeSubjectCodes | `subject_code NOT IN (...)` | 排除科目（Apollo配置） |
| excludeCostCodes | `cost_code NOT IN (...)` | 排除成本编码（Apollo配置） |

EXISTS 子查询关联 `dp_dim.doris_dim_sku_dynamic_sales`（按 `dt=前一天` 取快照），支持过滤：`spu_code`、`category_level3`、`is_self_research`、`self_produced`、`brand_id`。

## 对比弹窗构建（ExpenseParser）

ExpenseParser 是一个纯工具类，核心职责：将多个渠道/维度的净利明细数据合并、对比、构建父子层级关系。

### 核心方法：parseChannelsExpenseUnionV2

四个阶段：
1. 遍历每个渠道，构建渠道级汇总（含税/不含税收入、销项税、进项税、增值税、税金附加、水利基金、印花税、利润总额、所得税、税后净利等）
2. 收集收入科目和成本科目（只取不含"."的顶级编码）
3. 处理费用科目明细（多渠道合并到同一 subjectMap，同科目多渠道数据挂到同一节点下）
4. 构建父子层级（按"."分隔符重建科目树）

### 科目取并集策略

多个渠道的同一 `subjectCode` 数据会合并到同一个节点下的 `subjectListResponses` 列表中，每条记录带有 `code`（渠道标识）用于区分。

### 比率处理

- 比率字段为 null、空或 `"-"` 时视为 0
- 分母为零时返回 `"-"` 而非报错
