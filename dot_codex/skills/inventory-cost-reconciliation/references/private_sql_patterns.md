# SQL 排查模式

以下 SQL 为模式示例，执行时根据具体 `owner_code`、`warehouse_code`、`goods_code`、月份替换参数。

## 成本侧明细

```sql
SELECT
    order_type,
    cost_source,
    income_num,
    income_unit_price,
    delivery_num,
    delivery_unit_price,
    create_time
FROM erp_cost.inventory_cost_details
WHERE calculation_month = %s
  AND owner_code = %s
  AND warehouse_code = %s
  AND goods_code = %s
ORDER BY order_type, cost_source, delivery_unit_price;
```

## 退货应收业务侧明细

```sql
SELECT
    h.return_order_id,
    h.owner_code,
    h.warehouse_code,
    h.delivery_order_id,
    h.delivery_order_status,
    h.order_status,
    h.arrive_time,
    d.goods_code,
    d.arrive_num + COALESCE(d.arrive_imperfect_num, 0) AS qty,
    d.cost_price,
    d.cost_source,
    (d.arrive_num + COALESCE(d.arrive_imperfect_num, 0)) * d.cost_price AS amount
FROM erp_iom.return_order h
JOIN erp_iom.return_order_detail d ON h.return_order_id = d.return_order_id
WHERE h.owner_code = %s
  AND h.warehouse_code = %s
  AND d.goods_code = %s
  AND h.arrive_time >= %s
  AND h.arrive_time < %s
  AND h.order_status IN (50, 70)
ORDER BY d.cost_source, d.cost_price, h.arrive_time, h.return_order_id;
```

## 无单退货业务侧明细

```sql
SELECT
    h.inbound_order_code,
    h.relative_code,
    h.source_order_id,
    h.owner_code,
    h.warehouse_code,
    h.delivery_order_id,
    h.delivery_order_status,
    h.status,
    h.arrive_time,
    d.goods_code,
    d.arrive_num + COALESCE(d.arrive_defective_num, 0) AS qty,
    d.cost_price,
    d.cost_source,
    (d.arrive_num + COALESCE(d.arrive_defective_num, 0)) * d.cost_price AS amount
FROM erp_iom.no_order_inbound_order h
JOIN erp_iom.sub_no_order_inbound_order d ON h.inbound_order_code = d.inbound_order_code
WHERE h.owner_code = %s
  AND h.warehouse_code = %s
  AND d.goods_code = %s
  AND h.arrive_time >= %s
  AND h.arrive_time < %s
  AND h.status IN (20, 30)
ORDER BY d.cost_source, d.cost_price, h.arrive_time, h.inbound_order_code;
```

## 销售出库业务侧明细

如果直接联查超时，先查头表 ID，再用 ID 查明细。

头表：

```sql
SELECT
    delivery_order_id,
    owner_code,
    warehouse_code,
    order_status,
    warehouse_delivery_time
FROM erp_iom.delivery_order
WHERE owner_code = %s
  AND warehouse_code = %s
  AND warehouse_delivery_time >= %s
  AND warehouse_delivery_time < %s
  AND order_status IN (7, 10);
```

明细：

```sql
SELECT
    delivery_order_id,
    goods_code,
    goods_num,
    cost_price,
    cost_source,
    goods_num * cost_price AS amount
FROM erp_iom.sub_delivery_order
WHERE delivery_order_id IN (...)
  AND goods_code = %s;
```

## 抵消关系

按来源单：

```sql
SELECT
    calc_month,
    delivery_order_id,
    source_order_id,
    cost_type
FROM erp_cost.cost_deduction_order
WHERE source_order_id IN (...);
```

按销售出库单：

```sql
SELECT
    calc_month,
    delivery_order_id,
    source_order_id,
    cost_type
FROM erp_cost.cost_deduction_order
WHERE delivery_order_id IN (...);
```

严格历史月时加：

```sql
AND calc_month = %s
```

## 货主错位验证

同仓同 SKU 查多个货主：

```sql
SELECT
    h.owner_code,
    h.warehouse_code,
    d.goods_code,
    d.cost_source,
    d.cost_price,
    SUM(d.arrive_num + COALESCE(d.arrive_imperfect_num, 0)) AS qty,
    SUM(d.arrive_num + COALESCE(d.arrive_imperfect_num, 0)) * d.cost_price AS amount
FROM erp_iom.return_order h
JOIN erp_iom.return_order_detail d ON h.return_order_id = d.return_order_id
WHERE h.warehouse_code = %s
  AND d.goods_code = %s
  AND h.arrive_time >= %s
  AND h.arrive_time < %s
  AND h.order_status IN (50, 70)
GROUP BY h.owner_code, h.warehouse_code, d.goods_code, d.cost_source, d.cost_price
ORDER BY h.owner_code, d.cost_source, d.cost_price;
```
