# 字段与规则（主单粒度）

| 字段组 | 来源/规则 |
|---|---|
| DWS 主单字段 | `dt`、`express_code`、`source_order_id`、`order_id`、`delivery_order_id`、物流/仓库/店铺/货主字段均已在 `dp_dws.doris_dws_logistics_order_index` DDL 确认；表为 `UNIQUE KEY(dt, express_code)`、`dt` 月分区 |
| 单据、物流、仓库、店铺、货主 | `doris_dwd_oms_logistics_order_combine`；名称经物流、物流类别、仓库、店铺、货主维表补充 |
| 发出地区 | 由发出仓库地址确定；名称经地区维表补充 |
| 收货地区 | combine 收货省市区编码；名称经地区维表补充 |
| 包裹商品明细 | 同物流单全部商品按 `商品编码$$数量` 拼接，商品编码升序；SKU 种类超过 20 时过滤该物流单 |
| 包裹箱规编码 | combine 明细字段 `carton_code`（物流明细已提供箱型/箱规，不再匹配白名单） |
| 包裹包材费用 | 发出仓库 + combine `carton_code` + 发货时间查询 `dp_dim.doris_dim_sku_cost_price.no_tax_freight_price`；多条取最高 |
| 预估重量/预估代发费/预估物流费 | combine 的 `adjust_weight` / `agent_delivery_fee` / `logistics_fee` |
| 导入/结算代发费、导入/结算物流费、导入重量 | `doris_ods_fms_adjust_logistics_adjust_accounts` 的对应 `import_*` / `settle_*` 字段；仅 `matching_status = 1`（已匹配）且 `check_status = 1`（已核对） |
| 出库时间 | combine `warehouse_delivery_time` |
| 发件/派送/签收/退回时间 | `oms_logistics.logistics_track` 按 `express_code` 关联（业务确认运单号全局唯一）；为空记 `1970-01-01 08:00:01`；签收取最新轨迹记录 |
| 揽收时间 | 优先 combine `collect_time`；为空或 1970 再按 `express_code` 取轨迹 `got_time`；仍空记 `1970-01-01 08:00:01` |
| 时效 | 出库-揽收、揽收-派送、揽收-签收、出库-签收，单位分钟；揽收或派送为 1970/空时，揽收-派送时效为 0 |
