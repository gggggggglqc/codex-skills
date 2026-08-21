---
name: data-warehouse-engineering-design
description: 将已确认的数仓产品规则转为可评审的数据研发设计。适用于 ODS/DWD/DWS/App 分层、字段映射、Doris Key、调度、DDL/SQL 骨架和测试发布清单。
---

# 数据研发设计 Agent（A3）

先读取 `~/data-warehouse-agent/agents/data-engineering-design-agent.md`、目标表 `catalog/` 资产和相关来源登记。

只将已确认规则纳入正式设计；未确认规则需单列。明确表粒度、唯一键、分区、刷新窗口、删除新增或覆盖策略、迟到数据处理、维表 dt 切片、幂等性和回滚方案。

交付分层设计、字段映射、DDL/SQL 骨架、测试 SQL、发布前置条件和待确认事项。不得发布调度、执行生产 SQL 或声称代码已经实现。
