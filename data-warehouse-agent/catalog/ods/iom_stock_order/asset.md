---
asset_id: ods.iom_stock_order
layer: ODS
table_name: stock_order
database: erp_iom
business_name: 通用出入库开单主表
status: 部分确认
refresh: { frequency: 待确认, timezone: Asia/Shanghai }
grain: 一张通用出入库单（stock_order_code）
primary_key: id
partition: { strategy: 业务库表，无分区 }
version: { scene: 库存模块 V6.5.1, valid_from: 2026-08-17, valid_to: null, change_summary: 登记通用出入库开单主表 DDL }
source_evidence:
  - { type: business_ddl, path: /Users/liuqingchen/.codex/attachments/9234458b-a3a6-435a-91a6-3acd3f7773b6/pasted-text.txt, locator: erp_iom.stock_order, observed_at: 2026-08-17 }
implementation_mapping:
  warehouse_references:
    - downstream_asset: dwd.stock_order_combine
      join: stock_order_code；主表字段与出入库子单打平
---

# 通用出入库开单主表

已确认 `in_out_type`：`1` 入库、`2` 出库。`reason` 枚举已在 DDL 中给出，可用于解释普通仓、拆箱异常、拆包组装、样品、项目自采、线下采买、普通仓出库等原因。

`order_type`、`status`、`source` 的应用枚举已确认，见 [枚举映射](enums.md)。通用 IOM 出入库单可直接映射为库存模块标准出入库类型、状态和单据来源；MES 等非 IOM 单据不要求统一细分映射，保留来源事实表及其原始状态字段。
