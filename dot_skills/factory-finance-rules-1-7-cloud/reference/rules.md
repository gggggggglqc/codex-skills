# 业务基线

本文件冻结原单条数据库脚本、check-rules.md及本会话既有核对中明确采用的口径；旧CSV演示配置的0.01容差、原始报工量示例不是本次默认规则。原总入口规则1误将报工明细表当表头并覆盖为create_time，存在无法正确关联的缺陷；本云端入口沿用此前用户任务实际采用的单条脚本表头和billing_time，不复用该损坏总入口。

## 规则1

左侧：`erp_iom.finish_job_stock_order_detail d` JOIN `finish_job_stock_order h`，`h.stock_order_id=d.stock_order_id`；默认按表头billing_time，`d.product_type=1`。数量为 `COALESCE(actual_num,0)+COALESCE(defective_actual_num,0)`。

右侧：`mes_aps.report_work_order_detail r` JOIN 表头 `report_work_order o`，按 `o.create_time`。默认数量取关联完工入库明细按 `report_work_order_detail_id=r.detail_id` 汇总的同一数量，限定关联入库明细product_type=1，但不额外按完工日期过滤关联子查询。用户明确选择原始报工模式时取 `report_work_num`。

按material_code汇总比较。这保留原单条脚本实现；旧说明提到报工明细关联粒度，但原最终CSV实际为物料汇总，本次不冒充新增明细级校验。调整后报工数量不是独立原始报工数量。

## 规则2、3

左侧同完工入库关联，包含主、副产品，不加product_type过滤；数量为actual_num+defective_actual_num，默认表头billing_time。

右侧均为 `erp_cost.produce_cost`，`calc_month=指定月份首日`，按material_code SUM(produce_num)。不新增status、warehouse、factory、company或cost_price_type过滤。2与3只在业务名称上不同。

## 规则4、5

左侧同规则2/3，金额为逐行 `COALESCE(cost_price,0)*(COALESCE(actual_num,0)+COALESCE(defective_actual_num,0))` 再SUM，不先舍入单行金额。

右侧均为produce_cost的SUM(actual_produce_amount)，同一成本月份。无容差、无额外舍入。单价复算尾差原样展示。

## 规则6

左侧 `erp_cost.produce_cost_detail`，指定calc_month，`status=20 AND parent_id='root'`，SUM(outside_cost)。右侧 `erp_cost.outsourcing_order_detail d` JOIN `outsourcing_order h`，关联outsourcing_order_id，按表头order_billing_time，`outsourcing_order_type=2`，SUM(outsourcing_not_tax_freight_cost)。按material_code比较。

## 规则7

左侧IOM take_material_stock_order_detail JOIN take_material_stock_order，按billing_time，取actual_num；业务键为material_order_detail_id。

右侧MES take_material_order_detail JOIN take_material_order，按take_time，取base_unit_apply_num；业务键为detail_id。输出单据号、物料、双方基本单位及MES生产单位供审查。禁止用pro_unit_real_num替代。

原字典按业务键保存记录会覆盖重复键；云端在重复时停止，属于数据完整性保护，不擅自求和。缺失对侧时数值按0计算仍保留原数值结果，另记missing_side异常；单位、物料不一致另记异常。

## 共同约束

业务日期为首日00:00:00包含，结束日期次日00:00:00不含；成本月等值过滤不随分片重复累加。所有金额、数量边界值由SQL转CHAR，内部使用Decimal精确计算。日期/表名/字段仅代码白名单生成SQL。比较排序为material_code或detail_id升序。单边数值按0，源字段NULL使用原SQL的COALESCE0；业务键NULL则失败，不把空键合成一个合法物料。

不将已发现的副产品计算/汇总缺陷修复逻辑植入核对技能；核对只读报告实际表值。诊断和数据修复属于其他明确任务。
