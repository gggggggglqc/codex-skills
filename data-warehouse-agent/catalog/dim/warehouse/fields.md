# 字段摘要

| 业务字段 | 物理字段 | 类型 |
|---|---|---|
| 仓库 ID / 编码 / 名称 | `id` / `warehouse_code` / `warehouse_name` | varchar |
| 仓库状态 / 类别 / 功能 | `status` / `warehouse_type` / `warehouse_use_type` | int |
| 仓库地址 | `warehouse_address_code` / `warehouse_address` | varchar |
| 发货范围 | `warehouse_manage_area` | string |
| 供应商 / 公司 / 部门 | `supplier_code` / `company_code` / `structure_id` | varchar |
| 创建/更新时间 | `create_time` / `update_time` | datetime |

仓库所在区域的正式来源为本表，关联键为 `warehouse_code`。当前 DDL 中 `warehouse_address_code` 为仓库地址省市区编码，`warehouse_manage_area` 为发货范围；成本取价使用的区域字段将在后续上线时增加。
