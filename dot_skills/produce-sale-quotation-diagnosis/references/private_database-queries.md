# 数据库查询模板

默认库名按代码 Mapper 使用 `erp_cost`。只做只读查询；不要在排查阶段执行 update/delete/insert。

## 报价单主表与明细

```sql
SELECT *
FROM erp_cost.offer_price_order
WHERE offer_price_id = :offer_price_id;
```

```sql
SELECT *
FROM erp_cost.offer_price_order_formula
WHERE offer_price_id = :offer_price_id
ORDER BY parent_id, material_code;
```

```sql
SELECT *
FROM erp_cost.offer_price_order_injection
WHERE offer_price_id = :offer_price_id
ORDER BY material_code, mould_code, equipment_code;
```

```sql
SELECT *
FROM erp_cost.offer_price_order_outsource
WHERE offer_price_id = :offer_price_id
ORDER BY material_code;
```

```sql
SELECT *
FROM erp_cost.offer_price_reassembly_quotation
WHERE offer_price_id = :offer_price_id
ORDER BY reassembly_quotation_id;
```

## 标准成本还原

```sql
SELECT *
FROM erp_cost.produce_standard_cost
WHERE standard_cost_id = :standard_cost_id
   OR (:material_code IS NOT NULL AND material_code = :material_code AND factory_code = :factory_code)
ORDER BY calc_time DESC
LIMIT 20;
```

```sql
SELECT *
FROM erp_cost.produce_standard_cost_detail
WHERE standard_cost_id = :standard_cost_id
ORDER BY level, parent_detail_id, detail_id;
```

```sql
SELECT *
FROM erp_cost.produce_standard_cost_info_mapping
WHERE cost_detail_id IN (
  SELECT detail_id FROM erp_cost.produce_standard_cost_detail WHERE standard_cost_id = :standard_cost_id
)
   OR cost_detail_id = :standard_cost_id;
```

## 操作费 / 代发费 / 周转箱

```sql
SELECT *
FROM erp_cost.operation_fee_quotation
WHERE (:factory_code IS NULL OR factory_code = :factory_code)
  AND (:material_code IS NULL OR material_code = :material_code OR goods_code = :material_code)
ORDER BY update_time DESC
LIMIT 20;
```

重点字段：

- `replace_shipping_fee`：普通代发费
- `oem_replace_shipping_fee`：贴牌代发费
- `produce_replace_shipping_fee`：产销代发费
- `turnover_box_fee`：周转箱费
- `bundling_fee`：打捆费
- `self_world_cover_fee`：天地盖自营
- `replace_world_cover_fee`：天地盖代发

## 基础报价信息

```sql
SELECT *
FROM erp_cost.basic_offer_price
WHERE (:factory_code IS NULL OR factory_code = :factory_code)
ORDER BY update_time DESC
LIMIT 20;
```

常看字段：

- 管理费率
- 目标管理费率
- 研发费率
- 月工作天数
- 上班时长

## 设备报价 / 注塑

```sql
SELECT *
FROM erp_cost.equipment_quotation
WHERE (:factory_code IS NULL OR factory_code = :factory_code)
ORDER BY update_time DESC
LIMIT 20;
```

```sql
SELECT *
FROM erp_cost.mould_material_detail
WHERE (:material_code IS NULL OR material_code = :material_code)
ORDER BY update_time DESC
LIMIT 50;
```

排查点：

- 是否有模具和注塑机绑定。
- 是否存在 `cycle_time`。
- 需要机边设备时，机边设备折旧/电费是否为 0。
- 不需要机边设备时，主设备折旧/电费、人工、模具折旧是否为 0。

## 预装 / 组装报价

```sql
SELECT *
FROM erp_cost.reassembly_quotation
WHERE (:factory_code IS NULL OR factory_code = :factory_code)
  AND (:material_code IS NULL OR material_code = :material_code)
ORDER BY update_time DESC
LIMIT 20;
```

```sql
SELECT *
FROM erp_cost.reassembly_quotation_process_detail
WHERE reassembly_quotation_id = :reassembly_quotation_id
ORDER BY process_code;
```

```sql
SELECT *
FROM erp_cost.reassembly_quotation_related_equipment
WHERE reassembly_quotation_id = :reassembly_quotation_id
ORDER BY process_code, equipment_code;
```

## 委外报价

```sql
SELECT *
FROM erp_cost.outsourcing_quotation
WHERE (:material_code IS NULL OR material_code = :material_code)
ORDER BY price_start_time DESC, update_time DESC
LIMIT 20;
```

## 生成采购价排查

```sql
SELECT offer_price_id, offer_price, self_research_add_price, turnover_box_fee,
       replace_turnover_box_fee, freight_fee, created_purchase_price_warehouse,
       status
FROM erp_cost.offer_price_order
WHERE offer_price_id = :offer_price_id;
```

判断：

- 工厂实体仓：通常应使用 `self_research_add_price + replace_turnover_box_fee`，单位运费为 0。
- 自营实体仓：通常应使用 `self_research_add_price + turnover_box_fee`，单位运费取 `freight_fee`。
- 若 `created_purchase_price_warehouse` 已包含目标仓库，代码会拒绝重复生成。
