# FMS 核对规则

处理工厂账务核对时，优先按以下 7 条规则建立检查项。先确认时间口径、状态过滤、分组维度和单位，再判断差异是否真实存在。

## 规则 1

名称：完工入库单数量 = 报工入库数量

- 当前脚本：`scripts/check_rule1_db.py`
- 完工入库侧：
  `erp_iom.finish_job_stock_order_detail`
- 报工侧：
  `mes_aps.report_work_order_detail`
- 关联口径：
  以 `report_work_order_detail_id` 回连完工入库明细，按报工明细粒度核对
- 数量口径：
  完工入库数量 = `actual_num + defective_actual_num`
  报工数量默认也调整为关联完工入库的 `actual_num + defective_actual_num`
- 说明：
  这是按用户确认后的“报工数量调整口径”执行，不再直接取原始 `report_work_num`

## 规则 2

名称：完工入库单数量 = 实际成本还原的完工入库数量

- 当前脚本：`scripts/check_rule2_db.py`
- 完工入库侧：
  `erp_iom.finish_job_stock_order_detail`
  账期按表头 `erp_iom.finish_job_stock_order.billing_time`
- 实际成本还原侧：
  `erp_cost.produce_cost.produce_num`
- 数量口径：
  完工入库数量 = `actual_num + defective_actual_num`
- 当前结论：
  2026-03 已核对一致

## 规则 3

名称：完工入库单数量 = 生产成本管理的生产入库数量

- 当前脚本：`scripts/check_rule3_db.py`
- 完工入库侧：
  `erp_iom.finish_job_stock_order_detail`
  账期按表头 `erp_iom.finish_job_stock_order.billing_time`
- 生产成本管理侧：
  `erp_cost.produce_cost.produce_num`
- 数量口径：
  完工入库数量 = `actual_num + defective_actual_num`
- 当前结论：
  2026-03 已核对一致

## 规则 4

名称：完工入库单成本单价 * 数量 = 实际成本还原的生产成本总金额

- 当前脚本：`scripts/check_rule4_db.py`
- 完工入库侧：
  `erp_iom.finish_job_stock_order_detail`
  金额 = `cost_price * (actual_num + defective_actual_num)`
  账期按表头 `erp_iom.finish_job_stock_order.billing_time`
- 实际成本还原侧：
  `erp_cost.produce_cost.actual_produce_amount`
- 说明：
  不设容差，正常展示差异

## 规则 5

名称：完工入库单成本单价 * 数量 = 生产成本管理的实际生产入库总金额

- 当前脚本：`scripts/check_rule5_db.py`
- 完工入库侧：
  `erp_iom.finish_job_stock_order_detail`
  金额 = `cost_price * (actual_num + defective_actual_num)`
  账期按表头 `erp_iom.finish_job_stock_order.billing_time`
- 生产成本管理侧：
  `erp_cost.produce_cost.actual_produce_amount`
- 说明：
  不设容差，正常展示差异

## 规则 6

名称：实际成本还原的实际委外加工总费用 = 财务-委外加工明细金额

- 当前脚本：`scripts/check_rule6_db.py`
- 实际成本还原侧：
  `erp_cost.produce_cost_detail.outside_cost`
- 实际成本还原过滤：
  `calc_month = 月份`
  `status = 20`
  `parent_id = 'root'`
- 财务侧：
  子表 `erp_cost.outsourcing_order_detail.outsourcing_not_tax_freight_cost`
  主表 `erp_cost.outsourcing_order`
- 财务关联：
  `outsourcing_order.outsourcing_order_id = outsourcing_order_detail.outsourcing_order_id`
- 财务过滤：
  `order_billing_time = 月份`
  `outsourcing_order_type = 2`
- 说明：
  `outsourcing_order_type = 2` 对应外部往来
  这是金额核对，不是数量核对
- 当前结论：
  2026-03 已核对一致

## 规则 7

名称：领料出库单数量 = 生产收发-倒冲领料单数量

- 当前脚本：`scripts/check_rule7_db.py`
- IOM 侧：
  表头 `erp_iom.take_material_stock_order`
  明细 `erp_iom.take_material_stock_order_detail`
- MES 侧：
  表头 `mes_aps.take_material_order`
  明细 `mes_aps.take_material_order_detail`
- 单头关联：
  `take_material_stock_order.material_order_id = take_material_order.take_material_order_id`
- 明细关联：
  `take_material_stock_order_detail.material_order_detail_id = take_material_order_detail.detail_id`
- 数量口径：
  IOM 取 `actual_num`
  MES 取 `base_unit_apply_num`
- 时间口径：
  IOM 按 `billing_time`
  MES 按 `take_time`
- 单位说明：
  这条必须按基本单位核对
  `base_unit_apply_num` 与 IOM `actual_num` 对应
  `pro_unit_real_num` 是生产单位口径，不能直接替代基本单位核对
- 当前结论：
  2026-03 已核对一致

## 推荐分组维度

若业务允许，优先按最细粒度分组后再比对，而不是只看总额。

- 单据号
- 明细行号
- 生产工单号
- 物料编码
- 批号
- 仓库
- 会计期间

## 差异排查建议

- 先确认双方是否在同一账期字段上过滤
- 数量不一致时，先核对单位，再核对业务逻辑
- 金额不一致时，先核对是否混入含税金额、运费金额或重复展开金额
- 如果总额一致但明细不一致，优先从最小分组向上回溯
- 如果一侧缺记录，优先检查状态、红冲、作废和会计期间边界

## 自动发送

如果需要在规则 1-7 结果文件生成后自动调用机器人发送汇总，可使用：

- `scripts/run_rules_1_7_and_notify.py`
- `scripts/send_robot_message.py`

支持两种接法：

- 在 `.env` 里设置 `RECONCILE_NOTIFY_COMMAND`
  适合复用你当前已经在用的机器人命令或脚本
  命令模板可使用 `{title}` 和 `{content_file}`
- 在 `.env` 里设置 `RECONCILE_NOTIFY_WEBHOOK`
  并配合 `RECONCILE_NOTIFY_TYPE=wecom|dingtalk|feishu`
  如果是钉钉加签机器人，再补 `RECONCILE_NOTIFY_SECRET`

说明：

- 只有规则 1-7 的结果文件都成功生成后，才会进入机器人发送步骤
- 规则存在差异不算执行失败，仍会生成汇总并触发发送
- 如果机器人配置缺失，汇总文件仍会保留在 `output` 目录
