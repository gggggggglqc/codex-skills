---
name: reconcile-skill
description: 用于执行采购入库、其他入库、其他出库三类 FMS 与 IOM 的数据核对。当用户提到采购核对、其他入库核对、其他出库核对、按时间范围核对、FMS/IOM 对账、排查差异单号时使用。
---

# 对账技能

本技能用于执行以下三类核对：

1. 采购入库核对
2. 其他入库核对
3. 其他出库核对
4. 退货应收入库单核对
5. 无单退货入库单核对
6. 销售出库核对

技能目录：
`C:\Users\lqc\.codex\skills\reconcile-skill`

Python 路径：
`C:\Users\lqc\AppData\Local\Python\bin\python.exe`

统一入口脚本：
`C:\Users\lqc\.codex\skills\reconcile-skill\scripts\run_reconcile.py`

## 固定规则

### 时间范围

- FMS 使用 `business_date`
- IOM 使用 `billing_time`

### 输出位置

- 所有结果文件默认输出到桌面：
  `C:\Users\lqc\Desktop`

### 仓库过滤规则

- 过滤代发仓：`warehouse_use_type = 2`
- 保留白名单仓库：
  `WH0882, WH0388, WH0390, WH0237, WH0494`

## 采购入库核对

脚本：
`C:\Users\lqc\.codex\skills\reconcile-skill\scripts\purchase_in_stock_reconcile.py`

规则：

- 同时核对普通采购和工厂采购
- FMS 汇总层按 `warehouse_code + goods_code` 核对
- IOM 汇总层按 `warehouse_code + goods_code` 核对
- 普通采购明细使用 `business_no` 关联 FMS 明细
- 工厂采购明细展示与对账使用 `stock_order_code`
- IOM 明细使用 `stock_order_code`
- IOM 数量使用：
  `actual_num + defective_actual_num`
- 采购退货分组使用 `refund_num`
- 其他采购分组使用 `num`
- 当前退款数量分组：
  - 普通采购：`psi_group_type in (6, 202)`
  - 工厂采购：`psi_group_type in (6, 602)`

## 其他入库核对

脚本：
`C:\Users\lqc\.codex\skills\reconcile-skill\scripts\other_in_stock_reconcile.py`

规则：

- FMS 汇总层按 `入库仓库 + 商品编码` 核对
- IOM 汇总层按 `warehouse_code + goods_code` 核对
- IOM 数量使用：
  `actual_num + defective_actual_num`
- 过滤仓内调拨：
  `allocation.allot_type = 1` 不参与
- 过滤其他入库中的指定原因逻辑，以脚本现有实现为准

当前 FMS 分组：
`305,306,313,315,317,318,319,337,338,711,712,713,714,715,716,717,718,719,720,721,722,723,725,737,738,740,741`

## 其他出库核对

脚本：
`C:\Users\lqc\.codex\skills\reconcile-skill\scripts\other_out_stock_reconcile.py`

规则：

- FMS 汇总层按 `出库仓库 + 商品编码` 核对
- IOM 汇总层按 `warehouse_code + goods_code` 核对
- IOM 数量：
  - 普通情况：`actual_num + defective_actual_num`
  - `order_type = 18` 时使用脚本内特殊公式
- 过滤仓内调拨：
  `allocation.allot_type = 1` 不参与
- 排除：
  `order_type = 1 and reason = 13`

当前 FMS 分组：
`301,302,303,304,309,310,311,312,326,332,334,335,336,339,701,702,703,704,705,706,707,708,709,710,724,726,727,728,729,730,732,733,739,742,743,744`

## 退货应收入库单核对

脚本：
`C:\Users\lqc\.codex\skills\reconcile-skill\scripts\return_income_reconcile.py`

规则：

- FMS 来源：`fms_cost.psi_sales`
- IOM 来源：`erp_iom.return_order` + `erp_iom.return_order_detail`
- FMS 时间字段使用 `business_date`
- IOM 时间字段使用 `arrive_time`
- FMS 汇总层按 `in_warehouse_code + goods_code` 核对
- IOM 汇总层按 `warehouse_code + goods_code` 核对
- FMS 数量使用 `refund_num`
- IOM 数量使用：
  `arrive_num + arrive_imperfect_num`
- IOM 仅取状态：
  `order_status in (40, 50, 60, 70)`
- FMS 仅取分组：
  `131,132,133,146,152,153,154,155,167,176,177,181,182,183,184,185,186,187,188`
- FMS 过滤空仓库：
  `in_warehouse_code != ''`

## 常用执行命令

### 用统一入口跑 3 月采购入库

```powershell
& 'C:\Users\lqc\AppData\Local\Python\bin\python.exe' C:\Users\lqc\.codex\skills\reconcile-skill\scripts\run_reconcile.py purchase --start-time '2026-03-01 00:00:00' --end-time '2026-03-31 23:59:59'
```

### 跑 3 月采购入库

```powershell
& 'C:\Users\lqc\AppData\Local\Python\bin\python.exe' C:\Users\lqc\.codex\skills\reconcile-skill\scripts\purchase_in_stock_reconcile.py --start-time '2026-03-01 00:00:00' --end-time '2026-03-31 23:59:59'
```

### 跑 3 月其他入库

```powershell
& 'C:\Users\lqc\AppData\Local\Python\bin\python.exe' C:\Users\lqc\.codex\skills\reconcile-skill\scripts\other_in_stock_reconcile.py --start-time '2026-03-01 00:00:00' --end-time '2026-03-31 23:59:59'
```

### 跑 3 月其他出库

```powershell
& 'C:\Users\lqc\AppData\Local\Python\bin\python.exe' C:\Users\lqc\.codex\skills\reconcile-skill\scripts\other_out_stock_reconcile.py --start-time '2026-03-01 00:00:00' --end-time '2026-03-31 23:59:59'
```

### 跑 3 月退货应收入库单

```powershell
& 'C:\Users\lqc\AppData\Local\Python\bin\python.exe' C:\Users\lqc\.codex\skills\reconcile-skill\scripts\return_income_reconcile.py --start-time '2026-03-01 00:00:00' --end-time '2026-03-31 23:59:59'
```

## 无单退货入库单核对

脚本：
`C:\Users\lqc\.codex\skills\reconcile-skill\scripts\no_order_return_reconcile.py`

规则：

- FMS 来源：`fms_cost.psi_sales`
- IOM 来源：`erp_iom.no_order_inbound_order` + `erp_iom.sub_no_order_inbound_order`
- FMS 时间字段使用 `business_date`
- IOM 时间字段使用 `arrive_time`
- FMS 汇总层按 `in_warehouse_code + goods_code` 核对
- IOM 汇总层按 `warehouse_code + goods_code` 核对
- FMS 数量使用 `refund_num`
- IOM 数量使用：
  `arrive_num + arrive_defective_num`
- IOM 仅取状态：
  `status in (10, 20, 30, 40)`
- FMS 仅取来源：
  `psi_data_from_type = 4`
- FMS 过滤空仓库：
  `in_warehouse_code != ''`

### 跑 3 月无单退货入库单

```powershell
& 'C:\Users\lqc\AppData\Local\Python\bin\python.exe' C:\Users\lqc\.codex\skills\reconcile-skill\scripts\no_order_return_reconcile.py --start-time '2026-03-01 00:00:00' --end-time '2026-03-31 23:59:59'
```

## 销售出库核对

脚本：
`C:\Users\lqc\.codex\skills\reconcile-skill\scripts\sales_outbound_reconcile.py`

规则：

- FMS 来源：`fms_cost.psi_sales`
- IOM 来源：`erp_iom.delivery_order` + `erp_iom.sub_delivery_order`
- FMS 时间字段使用 `business_date`
- IOM 时间字段使用 `warehouse_delivery_time`
- FMS 汇总层按 `out_warehouse_code + goods_code` 核对
- IOM 汇总层按 `warehouse_code + goods_code` 核对
- FMS 数量使用 `actual_num`
- IOM 数量使用 `goods_num`
- IOM 仅取状态：
  `order_status = 7`
- IOM 过滤代发仓，但保留白名单：
  `WH0882, WH0388, WH0390, WH0237, WH0494`
- FMS 仅取分组：
  `142,120,102,141,140,137,135,118,117,113,108,110,148,149,169,170,171,172,106`

### 跑 3 月销售出库

```powershell
& 'C:\Users\lqc\AppData\Local\Python\bin\python.exe' C:\Users\lqc\.codex\skills\reconcile-skill\scripts\sales_outbound_reconcile.py --start-time '2026-03-01 00:00:00' --end-time '2026-03-31 23:59:59'
```

## 排查差异单号时的固定顺序

当用户给出单号要求排查时，优先按以下顺序检查：

1. FMS 是否存在该单
2. IOM 是否存在该单
3. 两边是否命中当前时间范围
4. 单号字段是否一致
5. 数量字段是否应该取 `num` 还是 `refund_num`
6. 是否命中仓库过滤规则

## 回复要求

- 返回汇总行数、差异组合数、单据差异数
- 告诉用户结果文件路径
- 如果差异已定位，要明确说明是：
  - 时间范围问题
  - 单号字段问题
  - 数量字段问题
  - 仓库过滤问题
  - 分组条件遗漏问题
