# 店铺排行榜 / 达人 / 天猫京东 / 抖音快手 / 拼多多 店铺排行榜

**默认排序**：今日销售金额降序

**注**：所有业务按已付金额核算支付或发货收入；毛利率统计销售货品，其他指标统计全部货品。

## 大屏分组与店铺平台限定

- 店铺排行榜 → 所有平台店铺
- 天猫京东店铺排行榜 → `TB / JD / TBFX`
- 抖音快手店铺排行榜 → `DY / KS`
- 拼多多店铺排行榜 → `PDD / PDDFX`

所有店铺大屏在上层限制 **最近 365 天收入 > 0**。

## 过滤逻辑

- 实时：渠道近 365 天没收入的不同步统计；店铺禁用 + 近 365 天没收入不同步统计
- 历史：过滤周期内 收入=0 或 销量=0 的数据

## 指标明细

### 今日金额 / 昨日金额(减退款) / 占比 / 自研金额(减退款) / 自研占比
- 库表：`doris_app_real_time_sales_report_rt`（实时表）
- 不区分：`sum(sales_amount − refund_amount)`
- 区分：
  - 线上分销(代销)：`sum(estimate_cost − estimate_refund_cost)`
  - 其他：`sum(sales_amount − refund_amount)`

### 昨日金额 / 近 30 日金额 (不减退款)
- 库表：`doris_app_real_time_sales_report_v1`
- 不区分：`sum(sales_amount)`
- 区分：
  - 线上分销(代销)：`sum(estimate_cost)`
  - 其他：`sum(sales_amount)`

### 今日 / 昨日 支付销量（支付口径）
- 实时：`sum(paid_num − refund_num)`
- 占比：单店铺昨日销量 / 所有店铺昨日销量

### 昨日发货销量（发货口径）/ 近 3/7/30/本月/上月/财年/365 日销量 / 销量占比
- 库表：`doris_app_report_delivery_v1`
- 公式：`sum(paid_num)`

### 7 日环比
- 同 SKU 排行榜的 7 日环比公式

### 昨日收入(不减退款)
- 不区分：`sum(sales_amount + refund_amount)`
- 区分：
  - 线上分销(代销)：`sum(estimate_brand_quotation + refund_brand_quotation)`
  - 其他：`sum(sales_amount + refund_amount)`

### 收入 / 自研收入（昨日 / 近 3/7/30/本月/上月/财年/365 日）
- 同 SKU 排行榜的收入公式

### 昨日 / 近 30 日 含税 / 不含税 采购成本
- `sum(含税采购成本)` / `sum(不含税采购成本)`
- **限制销售货品**

### 昨日含税 / 不含税毛利率 / 近 30 日含税 / 不含税毛利率（含上月同期）
- 公式：`1 − (近 30 日 V1 不含税(含税)采购成本) / (近 30 日 V1 财务销售收入)`
- 限制销售货品
- 实时含税：`1 − 近 30 日销售货品含税采购成本(已减退款) / 近 30 日销售货品发货收入(已减退款)`
- 历史：把「近 30 日」换成「周期内」

### 昨日已发货退款
- `sum(refund_amount)`

### 昨日 / 近 3/7/30/本月/上月/财年/365 日 收入占比 / 自研占比
- 公式：`(V1 自研销售收入) / (V1 财务销售收入)`
- 实时：单店铺自研发货收入(减退款) / 单店铺发货收入(减退款)；及单店铺收入 / 所有店铺收入
- 历史：周期口径

### 本月推广费 / 推广费比 / 财年推广费比
- 库表：`doris_app_report_delivery_v1` + `dp_ods.doris_ods_upload_expense_detail`
- 推广费用 = `expense_detail 表支出 − expense_detail 表收入`
- 推广费比 = `推广费用 / 发货收入(已减退款)`
- 财年推广费用同上换日期范围
- 限制：
  - V1 表
  - `expense_detail` 限制费用项目 `cost_code` 在「一级费用类目=推广费用」的科目集合：
    ```sql
    cost_code in (
      select item.cost_code, cost_name
      from dp_ods.doris_ods_zcm_cost_item item
      left join dp_ods.doris_ods_zcm_cost_attribution attr ON item.cost_attribution_id = attr.id
      where attr.id = 2  -- 一级费用类目为推广费用
    )
    ```
  - 限制费用类型 = 1 实际发生

### 昨日推广费用 / 推广费比
- 公式同上，时间换昨日
- 历史口径：周期内推广费用 / 周期内发货收入(已减退款)

### 昨日已付金额
- 库表：`doris_dws_eb_trade_order_goods_index` + `doris_dws_trade_order_goods_index`
- 公式：`系统 index 表昨日已付金额求和 + 跨境 index 表 SKU 总额-人民币 sku_total_cny`
- 限制：订单功能 = 一般交易订单

### 单均价（近 30 日）
- 库表：`doris_dws_eb_trade_order_goods_index` + `doris_dws_trade_order_goods_index`
- 公式：`∑昨日已付金额 ÷ ∑昨日原始单量`，四舍五入保留两位
- 实时：`近 30 日已付金额(不减退款) ÷ 近 30 日去重的原始单量(不减退款)`
- 历史：周期口径
- 限制：订单功能 = 一般交易订单
