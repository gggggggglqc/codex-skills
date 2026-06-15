# 跨境销售

跨境销售数据来源于易仓系统，通过 OMS 转化为内部订单。核心业务库表为 `oms_ops.eb_trade_order`（主订单）和 `oms_ops.eb_sub_trade_order`（子订单）。

## 维度类字段

| 字段名称 | 字段业务说明 | 字段开发说明 | 业务库表 | 业务库表字段 |
|---|---|---|---|---|
| dt | OMS跨境系统订单下单日期 | | | |
| 系统订单号 | OMS系统将易仓销售订单转化为内部订单后的主订单编号 | 直接取ERP库表字段值 | oms_ops.eb_trade_order | order_id |
| 系统子订单号 | 子订单编号 | 直接取ERP库表字段值 | oms_ops.eb_sub_trade_order | sub_order_id |
| 易仓销售单号 | 易仓系统抓取跨境电商平台的单号 | 直接取ERP库表字段值 | oms_ops.eb_trade_order | sale_order_code |
| 易仓仓库单号 | 仓储系统的出库单号 | 直接取ERP库表字段值 | oms_ops.eb_trade_order | warehouse_order_no |
| 参考单号 | 跨境电商平台订单的原始编号 | 直接取ERP库表字段值 | oms_ops.eb_trade_order | ref_order_no |
| 跟踪单号 | 类似国内电商的快递单号 | 直接取ERP库表字段值 | oms_ops.eb_trade_order | shipping_method_no |
| 订单平台编码/名称 | 平台编号/名称 | 名称需关联平台维表 | oms_ops.eb_trade_order | plat |
| 店铺平台编码/名称 | 店铺所属平台 | 需关联店铺维表 | | |
| 易仓店铺编码/名称 | 店铺在易仓系统中的编码/名称 | 直接取ERP库表字段值 | oms_ops.eb_trade_order | seller_account / seller_account_name |
| 店铺编码/名称 | | 名称需关联店铺维表 | oms_ops.eb_trade_order | oms_shop_code |
| 店铺类型/合作货主/所属部门/所属事业群/绑定公司 | | 需关联店铺维表获取 | | |
| 易仓仓库ID/仓库编码/名称 | | 名称需关联仓库维表 | oms_ops.eb_trade_order | warehouse_id / oms_warehouse_code |
| 订单状态 | 枚举: -1未知, 10已取消, 20待付款, 30待审核, 40编辑中, 50已审核, 60已发货 | 直接取ERP库表字段值 | oms_ops.eb_trade_order | status |
| 订单下单时间 | | | oms_ops.eb_trade_order | date_create_platform |
| 订单支付时间 | | | oms_ops.eb_trade_order | date_paid_platform |
| 易仓发货时间 | | | oms_ops.eb_trade_order | date_warehouse_shipping |
| 平台发货时间 | | | oms_ops.eb_trade_order | platform_ship_time |
| FBA发货时间 | | | oms_ops.eb_trade_order | fba_shipping_date |
| 订单创建时间（ERP） | | | oms_ops.eb_trade_order | create_time |
| 国家二字码/英文名/中文名 | 全球标准国家二字码 | 英文/中文需关联国家维表 | oms_ops.eb_trade_order | country_code |
| 省/州 | 收件人所在省份 | 直接取ERP库表字段值 | oms_ops.eb_trade_order | state |
| 城市 | 收件人所在城市 | 直接取ERP库表字段值 | oms_ops.eb_trade_order | city_name |
| 订单类型 | sale=正常销售, resend=重发, line=线下 | | oms_ops.eb_trade_order | order_type |
| 销售模式 | 正常销售/线下→线上直销; 重发→非销售订单 | | | |
| 订单功能 | 正常销售/线下→一般交易订单; 重发→补发货品订单 | | | |
| 易仓发货商品编码 | | | oms_ops.eb_sub_trade_order | warehouse_sku |
| SKU编码/名称 | | 直接取ERP库表字段值 | oms_ops.eb_sub_trade_order | goods_code / goods_name |
| 货品编码/名称 | | 通过SKU编码关联SKU维表 | | |
| 货品类别/一级~四级类目 | | 通过SKU编码关联SKU维表 | | |
| 是否自研品/控价品/淘汰品 | | 通过SKU编码关联SKU维表 | | |
| 组合装编码/数量 | | | oms_ops.eb_sub_trade_order | combine_code / combine_qty |

## 指标类字段

所有外币金额均有原币种和人民币两个版本，人民币版本按**订单支付日期当天的汇率表**转换。

| 字段名称 | 字段业务说明 | 业务库表字段 |
|---|---|---|
| 币种 | 订单各项初始金额的币种 | currency |
| 订单金额 | 交易费+买家运费+平台补贴费 | amount_paid |
| 订单交易额 | 仅包含产品金额，不含运费（类似国内"货款"） | subtotal |
| 订单运费 | | ship_fee |
| 订单手续费 | | platform_fee_total |
| 订单交易费 | | finalvalue_fee_total |
| 订单其他费用 | | other_fee |
| 订单平台补贴费 | | seller_rebate |
| 订单已付金额 | | already_paid |
| 订单FBA费用 | | fba_fee |
| 订单税费 | | tax |
| SKU数量 | | qty |
| SKU单价 | | unit_price |
| SKU单个交易费 | | unit_final_value_fee |
| SKU单个手续费 | | transaction_price |
| SKU总额 | SKU单价×SKU数量（计算字段） | |
| SKU采购不含税含运费单价/总成本 | | |
| SKU采购含税含运费单价/总成本 | | |

## 跨境销售特殊规则

1. **币种转换**: 所有人民币金额按订单支付日期当天的汇率表转换
2. **订单金额 vs 交易额**: 订单金额=交易费+买家运费+平台补贴费; 交易额仅含产品金额
3. **销售模式判定**: 正常销售订单(sale)和线下订单(line)→线上直销; 重发订单(resend)→非销售订单
4. **订单功能判定**: 正常销售/线下→一般交易订单; 重发→补发货品订单
5. **易仓发货商品编码 vs SKU编码**: warehouse_sku是仓库实际发货的商品编码，goods_code是系统内部SKU编码，两者可能不同
