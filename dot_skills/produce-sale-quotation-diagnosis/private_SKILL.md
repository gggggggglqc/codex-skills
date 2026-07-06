---
name: produce-sale-quotation-diagnosis
description: 用于核对和排查 ERP Cost 产销报价、生产报价、标准成本还原、操作费/代发费、周转箱/天地盖费用、设备注塑报价、预装组装报价、委外报价、报价生成采购价等问题。适用于用户提到报价手册、05-报价规则、产销报价、报价单详情、标准成本还原、生成报价、报价终于到/算错/取不到、报价与 Excel 公式不一致、需要结合 erp-cost 代码和数据库查询定位差异时。
version: 1.0.0
---

# 产销报价排查

## 先确认输入

优先向用户收集这些字段；缺少时先用已有字段排查，不要卡住：

- 报价单号：`offer_price_id`
- 标准成本还原单号：`standard_cost_id`
- 工厂：`factory_code`
- 物料编码：`material_code`
- 客户类型/客户编码：影响代发费取值
- 仓库/实体仓：影响生成采购价时不含税单价、单位运费
- 现象：算错、取不到、不能生成、不能启用、生成采购价异常、与报价手册公式不一致

## 工作流

1. 查规则来源：先读 `references/formula-code-map.md`，确认 Excel《05-报价手册.xlsx》第一张业务表 `05-报价规则` 对应的业务公式。
2. 查代码落点：按规则映射打开对应 Java/Mapper 文件，优先看当前 `D:\code\erp-cost`，不要只凭规则文档判断。
3. 查数据库现状：用 `scripts/query_quotation_db.py` 查询关键表，或打开 `references/database-queries.md` 复制只读 SQL。
4. 对照三层结果：Excel 公式口径、代码实际口径、数据库落库值。结论必须说明差异发生在“规则口径、代码计算、基础资料、源数据、落库/状态”中的哪一层。
5. 输出排查结果：包含命中数据、关键字段、公式复算、代码位置、疑似根因和下一步处理建议。

## 常用命令

数据库脚本使用 `pymysql` 连接 MySQL；若当前 Python 环境缺少该依赖，换用已有数据库排查环境或先安装依赖后再执行。

```powershell
py -3 C:\Users\lqc\.codex\skills\produce-sale-quotation-diagnosis\scripts\query_quotation_db.py --offer-price-id BJxxxx --env-file D:\codex\codex-file-organizer\.env --output C:\Users\lqc\Desktop\quotation_diag.json
```

```powershell
py -3 C:\Users\lqc\.codex\skills\produce-sale-quotation-diagnosis\scripts\query_quotation_db.py --standard-cost-id SCxxxx --material-code 1000-xxx --factory-code F001 --env-file D:\codex\codex-file-organizer\.env
```

## 排查重点

- 生成报价前，`produce_standard_cost.error_type` 必须为空/无错误，且 `create_offer_price=false`；否则代码不会生成报价单。
- 标准成本主公式：`标准生产成本 = 成本基数 * (1 + 管理费率 + 研发费率)`；代码中基数来自下级成本、委外、注塑、预装、组装等汇总。
- 报价单出厂价：`利润 + 注塑 + 包材 + 辅料 + 预装 + 组装 + 委外 + 管理费 + 研发费`；目标出厂价不含研发费。
- 配件或外采件可能触发“不计管理费/不计利润/不加研发费”等特殊口径，必须看 `out_purchase_parts`、物料属性、存货类别和策略表。
- 代发费按客户分流：贴牌客户、产销客户、其他客户取不同字段；配件默认可能直接取固定值。
- 周转箱/天地盖/打捆费按策略、物料名称关键字、包装方式和装箱数判断；排查时要查操作费报价、天地盖策略和 BOM 辅料名称。
- 生成采购价时，不含税单价和单位运费受实体仓影响；西安/跨境/航天自营仓会带出运费，兴平工厂实体仓单位运费为 0。

## 引用资料

- 公式与代码映射：`references/formula-code-map.md`
- 数据库查询模板：`references/database-queries.md`
- 只读查询脚本：`scripts/query_quotation_db.py`

## 输出格式

排查结果建议按以下结构输出：

1. 问题定位：一句话说明最可能原因。
2. 数据证据：列关键表和字段值。
3. 公式复算：写出当前使用的公式和代入值。
4. 代码依据：给出文件和行号。
5. 处理建议：说明是维护基础资料、重新标准成本还原、重新生成报价、生成采购价，还是提代码修正。

---

## 版本管理（遵循数仓文档管理规范v1.0）

> 来源：[数仓文档管理规范v1.0](https://alidocs.dingtalk.com/i/nodes/QOG9lyrgJP3PAm3kuvy0z6E3VzN67Mw4)

### 版本说明

| 版本号 | 版本内容 | 上线状态 | 上线时间 | 维护人 | 备注 |
|--------|----------|----------|----------|--------|------|
| V1.0.0 | 初始版本，录入核心规则与核对流程 | 已上线 | 2026-07-06 | QoderWork | 按数仓文档管理规范v1.0补充版本管理章节 |

### 版本更新规则

1. **版本号**：与禅道版本号保持一致（如 V1.0.0、V1.1.0、V2.0.0）
2. **Sheet 命名**：指标说明按"版本号 + 简述"格式（如 `V1.1.0 口径调整`）
3. **变更标识**：本期新增或修改内容使用**红色字体**标识；删除内容使用~~画线~~处理
4. **历史版本**：只隐藏不删除，便于追溯
5. **额外说明**：绑定版本号，格式为 `【V1.x.0 额外说明】`
6. **更新流程**：复制上一版本 → 修改本期内容（标红）→ 更新版本说明 → 检查额外说明 → 隐藏历史版本 → 上线后更新状态
