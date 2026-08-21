# 待处理问题清单

本清单是销售模块数据资产建设的唯一待办入口。每次处理资料后必须同步更新；未全部关闭前，交付说明须附上仍未关闭的事项。

## 已完成

- 销售模块 V6.5.1 的三张 DWS Index 表及其基础 ODS 主/子单链路。
- 三张 Index 每日重算最近 60 天的删除重写规则。
- 原始订单子单 → 系统订单子单的 `source_sub_order_id` 关联。
- 含税采购成本规则与阶梯价/融合价/成本价来源边界。
- 货主返利比率及其来源 `doris_dim_owner_markup_rule`。
- 返利后成本来源 `srm_billing.purchase_cost_price`。
- Excel 局部删除线识别：不含税采购成本为历史/废弃口径，当前只保留返利后成本（不含税）。
- 按最新 Excel 更新 V6.5.1：净利成本、返利成本金额/进项税额、供货成本的有效指标和已知物理字段。

## 已确认待上线依赖

- `dp_dim.doris_dim_stock_cost.accounting_organization` 计划于月底上线；上线后售后分销退货采购/净利成本取价限制 `accounting_organization = 1`，正向销售成本不使用该筛选。
- `dp_dim.doris_dim_district_stock_cost` 是库存区域存货成本新表，当前尚未上线；上线后补充 DDL，并启用库存月度成本价规则的自动核查。
- `dp_dim.doris_dim_warehouse` 的仓库所在区域字段将在后续上线时增加；上线后补充字段名及其与采购价格区域键的对应，并启用区域取价核查。

## 发货 V1 应用层待确认

当前无 V1 应用层待处理问题。

已确认：易仓 DWS `doris_dws_eb_trade_order_goods_index` 已停止更新，仅作为发货 V1 的历史冻结数据源；不需要日常调度或重算窗口。产销结算店铺（`distributor_settle_shop_code`）、结算店铺名称是文档明确标注的**后续开发字段**，不纳入当前 V1 的结构完整性或待办。天猫超市补充使用 `doris_dws_finance_cost_sbjct`；卖家运费、代发费、含/不含税订单收入及销项/进项税额均已有销售模块直接字段，不需要科目策略编码。`doris_dws_finance_cost_sbjct_failure` 仅作失败分摊核查。

## 多维报表－老板报表待确认

详见 [老板报表待确认事项](/Users/liuqingchen/Documents/Codex/windows-projects/Das/catalog/application/boss_report_multidim/open-items.md)。首要事项是确认当前生效版本；随后补齐多维净利、实时、产销导入等应用表的 DDL/字段映射，并处理已标记的成本税别、跨境、库存取价和有效 SKU 规则。

## T+1 净利待确认

详见 [T+1 净利待确认事项](/Users/liuqingchen/Documents/Codex/windows-projects/Das/catalog/application/net_profit_t1/open-items.md)。已确认本月底上线 DWP-V6.4.9.3、DWP-V6.4.9.4、DWP-V6.4.9.5；DWP-V6.4.9.6 尚未评审。仍需补齐 V2、净利指标中间表、凭证中间表、跨境/业务上传表的物理结构与字段映射。

## 代码—文档比对待核验

- `tmp_data.other_expense_data`：DAS `das-feature-v5.8.6@8448e45a5` 实体配置为 `tmp_data.other_expense_data_test`，与已确认文档/DDL不一致；需确认生产环境使用的物理表名。
- 其他费用上传：代码删除接口按 MD5 键独立调用，导入接口不会自动整月删除；需确认调用链是否先删除目标月份后导入。
- `other_expense_data → doris_app_net_profit_check_report_v2`：当前 DAS 代码未找到 ETL 实现；需提供或定位离线调度/ETL 仓库。

详见 [DAS 代码—数仓文档比对基线](/Users/liuqingchen/Documents/Codex/windows-projects/Das/governance/code-doc-baseline.md)。

## 数据核对试点待处理

- `doris_app_finance_profit_business` 计划月底正式上线。2026-08-19 的只读核对显示：V1、V2 最新均为 2026-08-18，而该表最新为 2026-07-31；这是上线前基线，不作为数据异常。上线后仅需确认首次回刷范围；产品侧按结果数据继续核对，不依赖 ETL 代码或调度记录。详见 [REC-20260819-001](/Users/liuqingchen/Documents/Codex/windows-projects/Das/governance/reconciliation/REC-20260819-001-app-chain-metadata.md)。
- V1 → V2 → 经营净利的首批字段级金额勾稽集合已定义，见 `agents/reconciliation-mappings/delivery-v1-net-profit-chain.md`；待经营净利表正式上线并完成首次回刷后，按 `expense_code`、`country_type`、店铺、货主、商品进行逐日复验。`input_tax_amount → EP030` 已完成验证。
- V1 → V2 首轮试点（2026-08-18）已通过：使用“绝对差额不超过 `0.01` 元或相对差异不超过 `0.01%`”的日汇总容差；供应商层因采购占比拆分不做一对一金额相等核对。详见 [REC-20260820-002](/Users/liuqingchen/Documents/Codex/windows-projects/Das/governance/reconciliation/REC-20260820-002-v1-v2.md)。

## 处理规则

- 待提供项在拿到 DDL、ETL SQL、字段对照或产品确认后才可关闭。
- “待数仓确认”不得作为自动核查或 Agent 的确定性回答依据。
- 延后项不阻塞正向订单模块，但不得被误标为已完成。
