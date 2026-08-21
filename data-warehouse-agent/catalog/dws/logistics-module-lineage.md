# 物流模块穿透表

```mermaid
flowchart LR
  C["DWD 物流订单组合\ndoris_dwd_oms_logistics_order_combine\norder_status in (7,8)"] --> M["DWS 物流主单 Index\ndoris_dws_logistics_order_index"]
  C --> S["DWS 物流宽表中的子单逻辑粒度\ndoris_dws_logistics_order_index"]
  A["ODS 物流调账\ndoris_ods_fms_adjust_logistics_adjust_accounts\n已匹配/已核对"] --> M
  A --> S
  T["业务物流轨迹\noms_logistics.logistics_track"] --> M
  T --> S
  D["店铺、仓库、货主、物流、物流类别、地区维表"] --> M
  D --> S
  M -->|同一宽表中的物流单主单费用| S
  W["商品体积 weight\ncombine 新字段"] -->|体积占比分摊| S
```

## 过滤边界

- combine：仅出库单状态“已发货、已完成”。
- 调账：仅匹配状态“已匹配”、核对状态“已核对”。
- 商品 SKU 种类超过 20 的物流单：过滤。
- 箱规直接取物流明细 `carton_code`，不匹配白名单维表。
- 物流轨迹直接按 `express_code` 关联；业务确认运单号全局唯一。
- 物流宽表：每日覆盖更新最近 61 天。
- 物流宽表物理模型：`UNIQUE KEY(dt, express_code)`，`dt` 月分区。
