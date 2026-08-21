# 数据研发设计 Agent（A3）

## 1. 产品定位

将 A2 判定为“可实施”的业务口径转化为可供数仓研发评审的设计草案。A3 产出结构、字段、SQL/DDL 骨架、调度与测试方案；不提交代码、不创建生产表、不发布调度。

## 2. 输入契约

```yaml
request_type: new_asset | change_asset | rebuild_window | design_app_chain
scenario: 销售 | 物流 | 售后 | 库存 | 采购 | 跨境 | 净利 | 老板报表
target_version: 必填
approved_analysis: 必填，A2 分析编号
target_asset: 表名或资产 ID
sources: [已确认的表资产、DDL、字段映射]
refresh_constraint: 可选
doris_constraint: 可选
```

前置门禁：若 A2 结论不是“可实施”，或表/字段证据未确认，A3 只输出阻塞清单，不生成可提交的 SQL/DDL。

## 3. 固定设计流程

1. **校验输入**：检查目标版本、A2 分析编号、现行资产、来源表/字段与确认状态。
2. **定义事实边界**：确定层级（ODS/DWD/DWS/APP）、业务粒度、唯一键、分区日期及去重策略。
3. **设计字段映射**：逐字段登记来源、关联键、转换公式、空值/多值/精度规则及数据类型。
4. **设计刷新策略**：明确首次全量、每日窗口、删除新增或覆盖写入、迟到数据和重跑幂等性。
5. **生成评审草案**：输出 Doris DDL 骨架、SQL 逻辑骨架、测试 SQL、发布与回滚清单。
6. **写入设计资产**：保存设计单及待确认项；数仓开发确认后再由人工进入研发与发布。

## 4. 输出契约

```yaml
design_id: DES-YYYYMMDD-NNN
scenario: 净利
target_version: DWP-V6.4.9.5
status: draft | blocked | ready_for_warehouse_review
grain: []
keys: []
partitions: []
refresh: []
field_mapping: []
ddl_skeleton: []
sql_skeleton: []
tests: []
release: []
rollback: []
evidence: []
open_items: []
```

可读设计使用 [数据研发设计单模板](../templates/data-engineering-design.md)。

## 5. 必检项

| 主题 | 设计要求 |
|---|---|
| 粒度与 Key | 事实粒度、主键/唯一键、重复记录处置、聚合边界 |
| Doris 物理设计 | 分区字段、Key 模型、分桶、动态分区、数据类型与精度 |
| 刷新 | 首次加载、每日窗口、删除新增/覆盖更新、幂等、迟到数据、重跑范围 |
| 关联 | 主外键、维表切片日期、单值/多值维度、关联失败兜底 |
| 金额 | 含税/不含税、正负号、汇率、舍入位置、金额/数量精度 |
| 测试 | 行数、主键重复、空值、分区、金额勾稽、边界样本、回刷复验 |
| 发布 | 前置检查、灰度/回填范围、验收人、回滚 SQL 或恢复策略 |

## 6. 设计状态与门禁

| 状态 | 含义 | 下一步 |
|---|---|---|
| `blocked` | 缺口径、字段、DDL、Key 或刷新证据 | 回到 A1/A2 补齐证据 |
| `draft` | 设计已生成，尚未完成数仓评审 | 提交数仓开发评审 |
| `ready_for_warehouse_review` | 所有设计项有证据，等待人工评审 | 人工确认后进入开发 |

- 不得以猜测填充物理字段、Key、分区或调度。
- 不得将 SQL/DDL 草案视为生产执行授权。
- 若与已有 DDL 冲突，保留冲突项，交由 A1/A2 形成版本/口径裁决。

## 7. MVP 验收

1. 能对任一已确认指标输出分层、粒度、字段映射与刷新设计。
2. 能生成可审阅但不可直接生产执行的 DDL/SQL 骨架。
3. 能给出完整测试、发布与回滚清单。
4. 缺少实现证据时，明确阻塞，而不是编造设计。
