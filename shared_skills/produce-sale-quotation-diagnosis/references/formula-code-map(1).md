# 公式与代码映射

来源：

- Excel：`C:\Users\lqc\Downloads\05-报价手册.xlsx`
- 业务 Sheet：`05-报价规则`
- 代码：`D:\code\erp-cost`

## Excel 关键规则

### 更新报价前提

- BOM 必须正确维护。
- 损耗口径：预装工序损耗 0%；注塑件损耗 0.1% 维护在 2000- 层级；所有外采件损耗 0.1%。
- 预装工序效率是该道工序效率；组装工序拉通报价，不按产线平衡 80% 校验。
- 模具基础资料、模具与注塑机绑定、设备报价信息、人工、循环周期必须完整。

代码落点：

- 标准成本还原入口：`jbs-erp-cost-service/src/main/java/com/jbs/erp/cost/service/impl/ProduceStandardCostServiceImpl.java`
- 计算上下文和资料收集：`buildCalcContext`
- BOM 明细递归：`fillMiddleCost`、`calcMiddleCost`
- 工序费用匹配：`fillStandardCostFromProcess`

### 标准成本还原

Excel 口径：

```text
标准生产成本 =
  (物料成本 + 注塑成本 + 包材成本 + 辅料成本 + 预装费用 + 组装费用 + 委外加工费)
  * (1 + 管理费占比 + 研发费比)

管理费 =
  (下级成本之和 + 委外加工费 + 注塑成本 + 组装成本 + 预装成本) * 管理费占比
```

代码口径：

- `StandardCostCalcBO.getNotCoproductProduceCost()` = `costSum + outsourcingCost + injectionCost + assembleCost + preInstallCost`
- `StandardCostCalcBO.calcManageCost()` = `getNotCoproductProduceCost() * manageCostRatio`
- `StandardCostCalcBO.calcResearchCost()` = `getNotCoproductProduceCost() * researchRate`
- `StandardCostCalcBO.calcMainProduceCost()` = `getNotCoproductProduceCost() * (1 + manageCostRatio + researchRate)`
- `ProduceStandardCostServiceImpl.fillManageCost()` 从基础报价取 `manageFeeRatio`、`targetManageFeeRatio`、`researchRate`
- `ProduceStandardCostServiceImpl.buildProduceStandardCost()` 汇总 `packageCostSum`、`accessoryCostSum`、`injectionCostSum`、`preInstallCostSum`、`assembleCostSum`、`outsideCostSum`

排查字段：

- `produce_standard_cost.produce_cost`
- `produce_standard_cost.target_produce_cost`
- `produce_standard_cost.manage_cost_ratio`
- `produce_standard_cost.research_rate`
- `produce_standard_cost.error_type`
- `produce_standard_cost_detail.*_cost`

### 设备报价 / 注塑

Excel 口径：

```text
费用合计 = 设备折旧费 + 设备电费 + 机边设备电费 + 机边设备折旧费 + 基础配套分摊
实际产能 = 60 * 60 / 成型周期 * 模穴数
费用单价 = 费用合计 / 实际产能 + 人工费用 + 模具折旧费
人工单价 = (平均月薪 * 需求人数 / 月工作天数 / 上班时长) / 实际产能
24h产能 = floor(24 * 60 * 60 / 成型周期 * 模穴数)
加工成本 = 费用单价 * 单品用量 * (1 + 损耗率)
材料成本 = 零件克重 * 材料价格 * 单品用量 * (1 + 损耗率)
小计 = 加工成本 + 材料成本
```

代码落点：

- 注塑工序映射：`ProduceStandardCostServiceImpl.fillStandardCostFromProcess`
- 注塑详情展示：`OfferPriceOrderServiceImpl.buildInjectionProcessCostResponses`
- 设备报价信息：`MouldMaterialDetailBO`
- `OfferPriceOrderServiceImpl` 中实际日产能使用 `floor(86400 / cycleTime) * cavityNum`
- `OfferPriceOrderServiceImpl` 中若 `cycleTime == 0`，展示计算时按 1 处理

排查字段：

- `mould_material_detail.cavity_num`
- `mould_material_detail.cycle_time`
- `mould_material_detail.unit_price`
- `mould_material_detail.target_price`
- `mould_material_detail.total_fee`
- `offer_price_order_injection.formula_cost`
- `offer_price_order_injection.produce_cost`
- `offer_price_order_injection.sub_total`

### 外购物料 / 材料配方

Excel 口径：

- 包材：需求数量 * 上月收货入库数量最大的不含税含运采购价。
- 辅料：需求数量 * 上月收货入库数量最大的不含税含运采购价。
- 原材料且编码包含 `4000-H/J/K/L/V`：需求数量 * 最新不含税含运采购价。
- 原材料且编码不包含上述前缀：需求数量 * 最新含税含运采购价。
- 委外：物料属性为委外时，按物料编码获取最新委外报价。
- 配方：注塑件下级是配方，配方下级是原料；配方价格来自子项物料单价 * 子项用量。

代码落点：

- 末级材料成本：`ProduceStandardCostServiceImpl.calcEndCost`
- 配方展示：`OfferPriceOrderServiceImpl.buildFormulaResponses`
- 注塑配方材料成本：`OfferPriceOrderServiceImpl.buildInjectionProcessCostResponses`
- 采购价策略类：`jbs-erp-cost-service/src/main/java/com/jbs/erp/cost/service/handler/purchasePrice/*Strategy.java`
- 委外报价：`ProduceStandardCostServiceImpl.fillOutsourcingCost`

### 预装 / 组装

Excel 口径：

```text
节拍 = 标准工时 * (1 - 优化率) / 人数
时产 = 60 * 60 / 节拍
日产能 = 最小时产 * 工作时长
组装合计 =
  ((sum(子单人数 * 平均月薪) / 月工作天数) / (MIN时产 * 上班时长))
  + sum(子单设备单价)
```

代码落点：

- 标准成本匹配预装/组装报价：`ProduceStandardCostServiceImpl.fillStandardCostFromProcess`
- 预装/组装详情：`OfferPriceOrderServiceImpl.buildReAssemblyCostResponse`
- 报价维护与基础信息联动：`ReassemblyQuotationServiceImpl`

排查字段：

- `reassembly_quotation.unit_price`
- `reassembly_quotation.target_price`
- `reassembly_quotation_process_detail.*`
- `reassembly_quotation_related_equipment.*`
- `produce_standard_cost_info_mapping.type`

### 生成报价

Excel 口径：

- 按标准成本还原生成报价。
- 根据不同客户取不同代发费。
- 已启用、已生成采购价的报价单不可删除。

代码口径：

- 入口：`OfferPriceOrderServiceImpl.batchAddOfferPriceOrder`
- 生成前置条件：
  - `produce_standard_cost.error_type == NULL_ERROR`
  - `produce_standard_cost.create_offer_price == false`
- 生成明细：
  - 主表：`offer_price_order`
  - 配方：`offer_price_order_formula`
  - 注塑：`offer_price_order_injection`
  - 委外/外购材料：`offer_price_order_outsource`
  - 预装/组装：`offer_price_reassembly_quotation`
- 删除限制：非手工创建不能删；已启用/已生成采购价场景要看状态和 `created_purchase_price_warehouse`

### 报价单出厂价

代码口径来自 `OfferPriceOrderBO`：

```text
利润 =
  利润率 * (注塑 + 包材 + 辅料 + 预装 + 组装 + 委外 - 不计利润成本) / 100

出厂价 =
  利润 + 注塑 + 包材 + 辅料 + 预装 + 组装 + 委外 + 管理费 + 研发费

自研品加价 = 出厂价 / 0.9

目标出厂价 =
  目标利润 + 目标注塑 + 包材 + 辅料 + 目标预装 + 目标组装 + 委外 + 目标管理费
```

特殊点：

- `outPurchaseParts=true` 时，利润和管理费会置 0。
- 外采不计利润策略命中的包材/辅料会从利润基数中扣除。
- 目标出厂价代码未加 `researchCost`，排查目标价时不要按普通出厂价公式套研发费。

### 操作费 / 代发费

Excel 口径：

```text
普通代发费 = (人工成本 + 打单费 + 装车费) * (1 + 管理费)
贴牌代发费 = (人工成本 + 打单费 + 装车费) * (1 + 管理费)
产销代发费 = 装车费 * (1 + 管理费)
配件 = 0.3 元/个
```

客户分流：

- 客户类型=供应商，客户=兴平市佳供云霄日用品有限公司：贴牌代发费。
- 客户类型=供应商，客户=西安佳帮手家居用品有限公司：产销代发费。
- 其他：普通代发费。

代码落点：

- 自动生成报价：`OfferPriceOrderServiceImpl.buildSaveOfferPrices`
- 手工新增/编辑报价：`OfferPriceOrderServiceImpl.fillOfferPriceOperationFee`
- 客户分流配置：`USE_OEM_REPLACE_SHIPPING_FEE_CUSTOMER`、`USE_PRODUCE_REPLACE_SHIPPING_FEE_CUSTOMER`
- 操作费报价表：`operation_fee_quotation`
- 配件默认代发费：`PJ_REPLACE_SHIPPING_FEE`

### 周转箱 / 天地盖 / 打捆费

Excel 口径：

- 天地盖代发：`sum(天地盖编码采购价) * 1 * (1 + 管理费 + 产销利润)`
- 天地盖自营：`sum(天地盖编码采购价) / 装箱数 * (1 + 管理费 + 产销利润)`
- 周转箱费用按天地盖策略优先；不在策略内时按辅料名称是否包含“周转箱”“打包带”判断。
- 打捆费与小时产能、装箱数、设备报价单价相关。

代码落点：

- `OfferPriceOrderServiceImpl.calcTurnoverBoxFee`
- `OfferPriceOrderServiceImpl.calcReplaceTurnoverBoxFee`
- `strategyDomain.searchWorldCoverStrategyMap`
- `OperationFeeQuotationBO.bundlingFee`、`selfWorldCoverFee`、`replaceWorldCoverFee`

### 运费

Excel 口径：

```text
天地盖：长 * 宽 * 高 / 1000000000 / 装箱数 * 15.4 * 1.1
非天地盖：长 * 宽 * 高 / 1000000000 * 15.4 * 1.1
优先自发包装尺寸；没有则使用产品尺寸。
```

代码落点：

- `OfferPriceOrderBO.calcWorldCoverFreightFee`
- `OfferPriceOrderBO.calcFreightFee`
- `OfferPriceOrderServiceImpl.calcFreightFee`

### 生成采购价

Excel 口径：

```text
不含税单价 = 自研品加价 + 周转箱费用
工厂实体仓：加周转箱-代发，单位运费=0
西安/跨境/航天自营实体仓：加周转箱-自营，单位运费=产销报价单-运费
金额 >= 0.01 时四舍五入保留两位；金额 < 0.01 保留实际小数位
```

代码落点：

- `OfferPriceCreatePurchasePriceServiceImpl`
- 外部创建采购价接口：`OfferPriceCreatePurchasePriceFacade.addPurchasePriceAndAlterPrice`
- 报价单已生成采购价仓库：`offer_price_order.created_purchase_price_warehouse`

## 常见差异判断

- Excel 写“管理费 5% 可改”，代码实际取基础报价中的工厂维度比例。
- Excel 写“产销代发费只含装车费”，代码最终取 `operation_fee_quotation.produce_replace_shipping_fee`，要先确认该字段是否已经按规则算好。
- Excel 写“选费用单价最低数据”，代码标准成本生成时使用注塑成本 Map；是否排除 0 值或异常设备要追 `buildCalcContext` 和设备报价查询。
- Excel 写“目标价”时容易误把研发费加进去；代码目标出厂价不含研发费。
