# 渠道排行榜（发货口径）

## 通用规则

- **默认按今日金额降序**。
- 所有业务均按已付金额核算支付/发货收入；**毛利率统计销售货品**，其他指标统计全部货品。
- 店铺平台不等于"班牛"。
- 实时页面：渠道近 365 天没收入的不同步统计；店铺禁用和近 365 天没收入的不同步统计。
- 历史页面：只过滤周期内 收入=0 的数据。
- 过滤财年收入为 0 的平台；过滤平台为空的数据；平台分类逻辑见需求 DAS2.6。

### 业态维度（按销售模式区分）

| 业态 | 销售模式 |
|---|---|
| ToB | 线下分销 / 平台入仓分销 / 线上分销(代销) / 线上分销(经销) / 线上代销 / 贴牌代工，`sales_model in (3,4,5,7,8,9)` |
| ToC | 线上直销 / 线下零售直销，`sales_model in (2,6)` |
| 其他 | 1=非销售订单 |
| 默认 | 新增放在"其他" |

### 国别

国内：国家=中国；国外：国家≠中国。

### 渠道与店铺所属平台映射（CASE WHEN 简表）

```sql
case
  when shop_plat_code<>'OFFLINE' and shop_plat_code='TB' and shop_type=4 then '淘宝'
  when shop_plat_code<>'OFFLINE' and shop_plat_code='PDD' and shop_type=4 then '拼多多'
  when shop_plat_code in ('MT','HM','XSYX','MTYX','DDMC','ZHZG') then '社团'
  when shop_plat_code in ('TMCS','TB') then '淘宝'
  when shop_plat_code in ('Ali1688','TBFX') then '淘宝'
  when shop_plat_code='OFFLINE' and shop_code in ('SC0221','SC0068','SC0067','SC0195') then '内销'
  when shop_plat_code='OFFLINE' and shop_code='SC0070' then '外贸'
  when shop_plat_code='OFFLINE' and shop_code in ('SC0206','SH048','SC0209') then '拼多多'
  when shop_plat_code='OFFLINE' and shop_code='SC0249' then '礼品'
  when shop_plat_code in ('AMAZON','AliExpress','Tiktok','Alibaba','Shein','Joom','Shopify','coupang',
                          'OZON','Arise','TEMU','LAZADA','SHOPEE','Saleyee','WalMart','MercadoLibre',
                          'TEMU_HALF','TEMU_FULL','Wayfair','Wildberries') then '跨境电商'
  when shop_plat_code='XHS' then '小红书'
  when shop_plat_code='KTT' then '快团团'
  when shop_plat_code in ('WPH','WPHZY') then '唯品会'
  when shop_plat_code='PDD' then '拼多多'
  when shop_plat_code='WXSPH' then '视频号'
  when shop_plat_code in ('JD','JDZY') then '京东'
  when shop_plat_code='DY' then '抖音'
  when shop_plat_code='PDDFX' then '拼多多'
  when shop_plat_code='KS' then '快手'
  when shop_plat_code='TEMU' then 'TEMU'
  when shop_plat_code='JDFX' then '京东分销'
  when shop_plat_code='Wechat' then '微信社群'
  else shop_plat_code
end as 渠道
```

## 销售金额与占比

| 指标 | 库表 | 计算 |
|---|---|---|
| 今日金额 | `doris_app_real_time_sales_report_rt` | 不区分：`sum(sales_amount-refund_amount)`；区分：线上分销(代销) `sum(estimate_cost-estimate_refund_cost)`；其他 `sum(sales_amount-refund_amount)` |
| 昨日金额 / 昨日自研金额 | `doris_app_real_time_sales_report_v1` | 同上口径 |
| 昨日金额占比 | — | 该渠道昨日金额(已减退款) / 所有渠道昨日金额(已减退款) |
| 昨日自研金额占比 | — | 该渠道昨日自研金额(已减退款) / 该渠道昨日金额(已减退款) |
| 7 日环比 | `doris_app_real_time_sales_report_v1` | (过去 7 天支付(减退款) − 过去 7~14 天支付(减退款)) / 过去 7~14 天支付(减退款) ×100%；区分销售模式时分子用供货成本/支付金额 |
| 近3/7/30/本月/上月/财年/365日 收入 / 自研收入 | `doris_app_report_delivery_v1` | 不区分：`sum(sales_amount)`；列表收入会回刷 60 天，净利含税按天回刷结账后不回刷 |
| 收入占比（昨日/近3/7/30/本月/上月/财年/365日） | `doris_app_report_delivery_v1` | 每个渠道近30天收入 / 全渠道总收入 |

均限定：排除店铺平台=班牛。

## 毛利率与采购成本

- **近30日 含税/不含税毛利率、上月同期不含税毛利率、近30日含税毛利率**：
  - 不区分：1 − (近30日 V1 表 不含税/含税采购成本) / (近30日 V1 表 财务销售收入)
  - 区分：分母按销售模式取（线上分销(代销)用 `estimate_brand_quotation`；其他用 `sales_amount`）
  - 限制：销售货品；排除店铺平台=班牛。
- **昨日 不含税/含税采购成本**：`doris_app_report_delivery_v1`，V1 表不含税/含税采购成本。
- **昨日/近3/7/30/本月/上月/财年/365日 自研占比** = V1 表自研销售收入 / V1 表财务销售收入；限制是否自研=是；排除班牛。
