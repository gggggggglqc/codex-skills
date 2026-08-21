# DAS 代码—数仓文档比对基线

## 代码基线

| 项目 | 值 |
|---|---|
| DAS 源码仓库 | `/Users/liuqingchen/工作/代码/das-core` |
| 当前待上线分支 | `das-feature-v5.8.6` |
| 当前待上线基线提交 | `8448e45a5ba222326433eda9c28ca273abb8fdb9` |
| 提交说明 | `fix(monitor): 过滤掉PlatSpuId为-1的无效数据` |
| 已同步主干 | `master@540e3af8f6a4b3a9a157f03c607e210ec956106c` |
| 同步日期 | 2026-08-19 |

代码仓库负责 DAS 应用接口、查询和部分 Doris 数据同步；DWS/ODS 的离线 ETL 不一定在该仓库。未在本仓库检索到某张数仓表的构建 SQL，只能说明该构建不在当前 DAS 代码基线中，不能推断表不存在。

## 已比对资产

| 文档资产 | 文档口径 | 代码定位 | 比对结论 |
|---|---|---|---|
| `tmp_data.other_expense_data` | 月度上传，按 `month` 先删后写；按费用名称字典映射 `expense_code` 后进入 V2 | `OtherExpenseDataEntity.java`、`OtherExpenseDataDomain.java`、`OtherExpenseDataServiceImpl.java` | 存在物理表名和删除方式差异，见下方。`importOtherExpenseData` 仅写入上传表，未在 DAS 代码中发现写 V2 的 ETL。 |
| `dp_dim.doris_dim_expense_subject_relation` | 费用名称字典/EP—科目关系的应用侧辅助关系 | `jbs-das-core-domain/.../DorisDimExpenseSubjectRelationDomain.java`、`OtherExpenseDataServiceImpl.selectAllExpenseSubjectRelation` | DAS 提供关系表读取接口；T+1 文档中 EP—科目权威口径仍以「费用名称字典表V6.4.9.3」为准。 |
| `dp_dws.doris_app_net_profit_check_report_v2` | 净利 V2 事实，由离线任务写入 | `MonitorNetProfitDetailMapper.xml`、`MonitorShopMapper.xml`、`MonitorPlatSpuMapper.xml` | DAS 为查询消费者：按 `country_type`、`expense_code`、店铺/链接等维度读取 V2；当前仓库未检索到 V2 构建或回刷调度实现。 |
| `dp_dws.doris_dws_stock_turnover_index` | 周转天数/可发天数的库存及加权日销来源 | `MonitorSpuMapper.xml` | DAS 聚合读取 `all_stock` 与 `avg_daily_sales_qty`；7/14 日加权日销的生产计算在 Index 离线任务，不在当前 DAS 查询代码。 |

## 已确认差异 / 定位点

1. **其他费用上传表物理名**：文档和用户提供 DDL 是 `tmp_data.other_expense_data`；v5.8.6 代码 `OtherExpenseDataEntity` 的注释仍为该表，但 `@Table` 实际配置为 `tmp_data.other_expense_data_test`。需确认生产环境是否应切换为正式表，或 `_test` 是否为预发布隔离表。
2. **删除新增流程**：文档规则为上传前删除对应月份后写入。代码中 `batchDeleteOtherExpenseData` 需调用方传入 `md5Keys`，而 `importOtherExpenseData` 仅按 `month + owner_code + shop_code + warehouse_code + cost_type` 生成 MD5 后执行 `batchSaveOrUpdate`；导入方法本身未自动执行整月删除。需核验前端/调用链是否先调用删除接口。
3. **V2 写入责任边界**：代码可上传、查询其他费用并读取费用—科目关系，但未发现 `other_expense_data → doris_app_net_profit_check_report_v2` 的作业实现；该转换应继续在离线 ETL/调度代码中核验。

## 后续定位流程

1. 先按业务问题定位 `catalog/` 的指标规则和字段来源。
2. 再按本文件列出的代码锚点检查当前分支实现；回答时标明“文档规则”“代码实现”或“离线 ETL 未在 DAS 仓库发现”。
3. 每次更新 DAS 代码后，记录新的提交号，并复核已登记差异是否关闭或新增。
