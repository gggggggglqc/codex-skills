---
name: 问答知识库
description: 记录和检索历史问答，分析高频问题和薄弱环节，生成技能优化建议。每次回答用户问题后自动记录，回答前先检索历史相似问答。当需要查看问答统计、分析哪些问题被频繁问到、评估回答质量、生成技能改进建议时使用。
---

# 问答知识库

## 核心职责

1. **每次回答问题后**，自动记录问答对（问题、答案摘要、分类、质量评分）
2. **回答新问题前**，先检索历史相似问答，复用高质量答案
3. **定期分析**，找出高频问题、回答失败的分类，生成优化建议
4. **反向优化**，将分析结果反馈到对应技能中

## Python 环境

**必须使用**: `C:\Users\lqc\AppData\Local\Python\bin\python.exe`
**禁止使用**: `python` 或 `python3`（Windows Store 桩程序）

## 脚本用法

脚本路径: `C:\Users\lqc\.qoderwork\skills\问答知识库\scripts\qa_manager.py`

### 记录问答

```bash
# 记录一条问答（自动分类）
python scripts/qa_manager.py add auto "5月凭证审核了多少" "已审核6183张，未审核68598张" good

# 记录并指定分类和质量
python scripts/qa_manager.py add 费用差异 "CI168差异多少" "MySQL 823万 vs Doris 1086万，差异263万" good

# 质量评分: good(完整回答) / partial(部分回答) / failed(无法回答)
python scripts/qa_manager.py add 凭证审核 "帮我查3月数据" "" failed
```

### 搜索历史

```bash
python scripts/qa_manager.py search CI168
python scripts/qa_manager.py search 凭证
```

### 统计分析

```bash
# 总体统计
python scripts/qa_manager.py stats

# 按分类统计
python scripts/qa_manager.py stats 费用差异
```

### 查看最近问答

```bash
python scripts/qa_manager.py recent 20
```

### 生成优化建议

```bash
python scripts/qa_manager.py suggest
```

### 导出报告

```bash
python scripts/qa_manager.py export
```

## 问题自动分类

脚本内置以下分类关键词映射，使用 `auto` 时自动匹配：

| 分类 | 触发关键词 |
|---|---|
| 凭证审核 | 凭证、审核、未审核、凭证状态 |
| 出纳推送 | 付款单、收款单、推送失败、出纳、下推 |
| 费用差异 | 差异、对不上、CI168、CI044、科目、分摊 |
| EP费用编码 | EP001-EP036、费用编码、净利V2 |
| 报表口径 | 公式、口径、毛利率、收入、退款 |
| 流程排期 | 几号、排期、负责人、月初、结账 |
| 重复检查 | 重复、重复凭证、CI165 |
| 数据查询 | 查一下、多少、汇总、明细 |
| 系统问题 | 报错、错误、失败、超时 |

## 工作流程（必须遵守）

### 回答前：检索历史

收到用户问题后，**先搜索历史问答**：

```bash
python scripts/qa_manager.py search "<问题关键词>"
```

如果找到高质量的相似问答，可以参考其答案快速回复，同时仍然执行实际查询以获取最新数据。

### 回答后：记录问答

每次回答完，**必须记录**：

```bash
python scripts/qa_manager.py add auto "<用户问题>" "<答案摘要>" <quality>
```

- `good`：完整准确地回答了问题
- `partial`：部分回答，有些信息缺失
- `failed`：无法回答或查询失败

答案摘要控制在 200 字以内，只记录关键结论，不需要完整回复文本。

### 定期优化：分析并改进

当用户问到"问答统计""哪些问题多""优化建议"时，运行：

```bash
python scripts/qa_manager.py suggest
```

根据分析结果，主动建议：
1. 高频问题对应的技能是否需要补充查询脚本
2. 回答失败的分类是否需要新建技能或更新知识
3. 未分类问题过多时，建议新增分类关键词
4. 将反复出现的标准答案沉淀到对应技能的 FAQ 中

## 与其他技能的协作

| 场景 | 动作 |
|---|---|
| 凭证审核类问题频繁 | 建议增强「数据查询助手」的凭证查询能力 |
| 费用差异类回答不好 | 建议增强「数据查询助手」的跨库比对脚本 |
| 报表口径类回答不好 | 建议补充「老板报表T1净利」或「老板报表公式说明」的 FAQ |
| 流程排期类回答不好 | 建议补充「T1对数流程」的 FAQ |
| 出现全新类别的问题 | 建议创建新技能来覆盖 |
