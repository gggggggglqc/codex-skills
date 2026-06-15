# das-core 核心 SQL 查询参考

> 来源：`MonitorNetProfitDetailMapper.xml`（39.8KB），`das-core` 项目核心 MyBatis Mapper。
> 所有 SQL 面向 Doris 数仓（dp_dws / dp_dim / tmp_data），使用标准 SQL 语法（兼容 MySQL 协议）。

## 涉及的数据库表

| 库名 | 表名 | 用途 |
|---|---|---|
| dp_dws | doris_dws_finance_cost_sbjct | 费用科目分摊成功表（含 share/no_tax_amount/tax_amount） |
| dp_dws | doris_dws_finance_cost_sbjct_failure | 费用科目分摊失败表（含 result_amount），排除 business_group=6 |
| dp_dws | doris_app_net_profit_check_report_v2 | 净利核对报表V2（EP费用编码维度） |
| dp_dim | doris_dim_expense_subject_relation | EP费用编码到科目的映射维表（dt=前一天） |
| dp_dim | doris_dim_expense_subject_relation_test | 同上（test版，dt=max(dt)） |
| dp_dim | doris_dim_sku_dynamic_sales | SKU动态销售维表（商品属性过滤） |
| tmp_data | sales_production_revenue_profit | 产销收入利润临时表（业务上传） |
| tmp_data | other_expense_data | 其他费用数据临时表（研发费用等） |

## SQL 查询清单

### 1. queryProfitSubjectDetail — 净利科目明细汇总

**用途**：按科目代码聚合所有费用金额（单页面展示）。

**结构**：两段 UNION ALL
- **Part A（costSbjct 片段）**：从费用科目分摊表取数，取 `-sum(share)` 作为 expense
- **Part B（核对报表）**：EP001→"收入"，EP002→"成本"，其他→维表subject_code；EP003的expense取0

**关键过滤**：
- 默认国内：`country_type = 1`，跨境时改为 `country_type != 1`
- 维表dt：`date_add(CURRENT_DATE(), interval -1 day)`（T+1逻辑）
- 排除科目/成本编码（Apollo配置）

### 2. costSbjct — 费用科目分摊SQL片段

**用途**：汇总三层数据来源的费用科目分摊。

**三层 UNION ALL**：
1. **正常分摊**：`doris_dws_finance_cost_sbjct` → `share` 字段
2. **分摊失败**（searchFailure=true）：`doris_dws_finance_cost_sbjct_failure` → `result_amount`，sales_model=-1
3. **临时表**（searchTmp=true）：`tmp_data.sales_production_revenue_profit`

**最终聚合**：按 `subject_code` 分组，取 `-sum(expense)`（负值表示费用支出方向）

### 3. contrastCostSubject — 对比查询费用科目分摊

**用途**：对比弹窗的费用科目部分，使用 `no_tax_amount`（不含税金额）。

**与 costSbjct 的区别**：
| 片段 | 金额字段 | 用途 |
|---|---|---|
| costSbjct | `share`（分摊金额） | 汇总查询 |
| contrastCostSubject | `no_tax_amount`（不含税金额） | 对比查询 |

**额外分组维度**：`code`（业务组/货主/渠道）+ `shop_code`

### 4. queryProfitSubjectContrastDetail — 净利科目对比明细

**用途**：弹窗对比查询，带 shop_code 级别的多维度对比。

**四段 UNION ALL**：
1. `contrastCostSubject` — 费用科目分摊（不含税金额 no_tax_amount）
2. `selectTmpV2` — 产销临时表（条件 searchTmp=true）
3. 核对报表 Part1 — 非税科目（排除 EP004/005/006/028/029/030/033/034/035/037）
4. 核对报表 Part2 — 税相关科目（仅 EP001/028/029/003/030/033/034/035/037）

**维表差异**：使用 `_test` 后缀维表，取 `max(dt)` 而非固定前一天。

### 5. queryProfitSubjectContrastDetailTaxAmount — 科目税额查询

**用途**：查询科目级别的税额合计。

```sql
sum(ifnull(t.tax_amount, 0)) AS tax_amount,
sum(CASE WHEN t.subject_code = '2221.04.01.01' THEN t.tax_amount ELSE 0 END) AS filter_tax_amount
```

- `tax_amount`：全部税额合计
- `filter_tax_amount`：仅科目 `2221.04.01.01`（应交税费-应交增值税-进项税额）的税额

### 6. selectTmp / selectTmpV2 — 产销临时表查询

**用途**：从业务上传的产销临时表获取收入/成本数据。

**EP编码映射**：
| field_code | selectTmp | selectTmpV2 |
|---|---|---|
| EP001 | "收入" | "不含税收入_产销" |
| EP003 | "不含税成本_产销" | "不含税成本_产销" |

**过滤条件**：
- 国内：`country_code = 'CN'`
- 跨境：`country_code != 'CN' OR country_code IS NULL`（允许NULL）
- 时间：`shipping_month BETWEEN netProfitStartDate AND dateEnd`
- 金额：selectTmp 取负值 `-revenue_expense_amount`，selectTmpV2 取原值

### 7. queryNetProfitRDExpense — 研发费用查询

```sql
SELECT month, max(amount) as research_development_expense
FROM tmp_data.other_expense_data
WHERE cost_type = '研发费用' AND month >= '2025-04-01'
GROUP BY month ORDER BY month DESC
```

### 8. queryContrastSalesProductionDetail — 产销对比查询

**用途**：产销数据按维度分组对比。

**分组维度**（groupByField 动态切换）：
- `owner_code` → CASE WHEN 做货主映射
- `channel_code` → 动态SQL渠道映射
- `shop_code` → 直接使用
- null → 不分组

**两层聚合**：先按 `subject_code + shop_code` 聚合，再按 `code + subject_code` 聚合。

### 9. querySalesProductionDetail — 产销明细查询

**用途**：简化版产销查询，仅按科目代码聚合。

对 selectTmp 结果按 `subject_code` 分组，取 `-sum(revenue_expense_amount)`。

## SQL 片段说明

### whereCondition — 通用动态条件

所有查询共享的基础过滤条件：

```xml
<if test="netProfitStartDate != null and dateEnd != null">
    and a.dt BETWEEN #{netProfitStartDate} AND #{dateEnd}
</if>
<if test="shopCodes != null and shopCodes.size() > 0">
    and a.shop_code IN <foreach>...</foreach>
</if>
<if test="ownerCodes != null and ownerCodes.size() > 0">
    and a.owner_code IN <foreach>...</foreach>
</if>
<!-- 商品属性过滤通过 EXISTS 子查询关联 doris_dim_sku_dynamic_sales -->
```

### whereSbjectCondition — 费用科目分摊表过滤

```xml
and subject_code IS NOT NULL AND subject_code != ''
<!-- 跨境过滤 -->
<choose>
    <when test="countryType == 2">and country_code != 'CN'</when>
    <otherwise>and country_code = 'CN'</otherwise>
</choose>
<!-- 排除科目/成本编码（Apollo配置） -->
<if test="excludeSubjectCodes != null">
    and subject_code NOT IN <foreach>...</foreach>
</if>
```

### whereFailureSubjectCondition — 失败表过滤

额外条件：`a.business_group != 6`（排除特定业务板块）。

### otherOwnerColumns — 货主映射

```sql
(CASE
    WHEN owner_code = 'sourceA' THEN 'targetA'
    WHEN owner_code = 'sourceB' THEN 'targetB'
    ELSE owner_code
END)
```

将多个货主代码合并/重映射到统一口径，由 Apollo `owner.code.relation` 配置。

## 新旧版本对比

| 特性 | 旧版 (Old) | 新版 |
|---|---|---|
| 税/非税分离 | 不分离 | 分离为两段UNION ALL |
| 维表 | doris_dim_expense_subject_relation | doris_dim_expense_subject_relation_test |
| 维表dt | 固定前一天 | max(dt) |
| 分组维度 | 仅 owner_code | owner_code/channel_code/shop_code/business_group |
| 费用金额 | share（分摊额） | no_tax_amount（不含税） |
| shop_code | 不包含 | 包含 |

## 销售模式分类（代码）

| 业态类型 | 销售模式 |
|---|---|
| ToB | 代销、经销、线上代销、线下经销、平台仓储、OEM |
| ToC | 线上直销、线下零售 |
| 其他 | 未知、非销售业务 |
