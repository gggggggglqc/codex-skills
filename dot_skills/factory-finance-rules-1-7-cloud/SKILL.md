---
name: factory-finance-rules-1-7-cloud
description: 在提供 Python 沙箱和只读 SQL 工具的云端智能体中，按月份执行工厂财务1–7规则的完工入库、成本、委外与领料核对。用于明确要求云端版或服务器版工厂1–7核对；本地直连版仍使用 factory-finance-rules-1-7。
metadata:
  version: 3.0.0
---

# 工厂财务1–7云端核对

按 [规则口径](reference/rules.md) 执行；[运行协议](reference/runtime-contract.md) 定义完整字段、限额和失败行为。[平台绑定](reference/platform-binding.md) 定义接入前要验证的工具能力。不得把示例工具名或实例信息当作已经可用的连接。

## 输入与执行边界

从用户给定的上下文取得明确年份、月份和规则；缺少年份且无法唯一确定时一次询问。月份展开为首日至末日，默认规则1–7。支持显式选择2–6等子集。业务日期按 Asia/Shanghai 解释，不自行按执行主机时区转换。

`request_scope` 示例：

```json
{"start_date":"2026-09-01","end_date":"2026-09-30","calc_month":"2026-09-01","rules":[1,2,3,4,5,6,7]}
```

可选 `finish_time_field` 为 `billing_time`（默认）、`create_time` 或 `finish_time`；可选 `report_quantity_mode` 为 `adjusted_from_finish`（默认）或显式要求的 `report_work_num`。报工日期固定采用本会话已确认的报工表头 `create_time`。成本规则必须在同一成本月内，最多31天。不增加工厂、仓库、状态或成本类型过滤；不把本地其他报表的规则带入。

## 工具职责

- Python：完整执行 `scripts/sandbox_runtime.py` 源码后调用 `run(request)`；仅标准库，不访问数据库、网络、环境变量或本地文件。
- SQL 工具：智能体按 Python 输出逐条执行只读 SQL，按每条 `db_name` 选择数据库；要求同一实例可访问 `erp_iom`、`mes_aps`、`erp_cost` 并支持跨库只读关联。
- 上传工具：仅在用户要求导出时上传运行时生成的文本。未上传不得宣称有下载链接。
- 消息工具：仅在用户明确要求发送且已有接收目标时发送最终 `notification`。Python 不读取 webhook，也不发送机器人消息。

首次接入先按平台绑定文档验证真实工具参数、原生成功/截断/分页状态、返回行信封和载荷限制。缺少可靠状态映射时停止查库，不让智能体凭有数据猜测成功。当前交付的本地验证不能替代真实云端联调。

## 无状态编排

每次 Python 调用都提交完整运行时源码和本次唯一请求对象；不依赖脚本路径执行、stdin、同级 import、上次变量或临时文件。工具若支持这些能力，可自行包装调用，但核心接口仍为 `run(request)`。

1. `run({"action":"plan","request_scope":S,"partition":"summary"})` 为所选1–6规则生成共用汇总查询。仅选择规则7时跳过 summary。
2. 如选择规则7，分别对 `rule7:00` 至 `rule7:63` 调用 plan。双方使用同一业务键CRC32分片，查询仍覆盖整个请求日期，避免逐日比较把跨日记录误判成差异。
3. 对每个分片，严格执行全部 `queries`。保留工具原始响应及原生状态，不改写行、不补字段、不重新汇总。
4. 调用 consume：

```json
{"action":"consume","request_scope":S,"partition":"summary","include_matches":false,"payload":{"manifest":完整原样manifest,"responses":[{"query_id":"原查询标识","success":true,"truncated":false,"has_more":false,"raw":"SQL工具完整原始响应"}]}}
```

以上为结构示意；实际请求必须是合法 JSON 对象。每个分片单独 consume，保存完整成功输出。`include_matches=true` 仅在用户需要全部比较行导出时使用。

5. 所有必要分片均成功后调用 `run({"action":"finalize","request_scope":S,"parts":[各分片完整consume输出]})`。缺少任何分片均失败。最终合并全月净差额和数量；不以某个分片的通过代表整月通过。
6. 用户要求文件时，对完整 finalize 输出调用 `render_csv`。默认 `mode="differences"` 生成汇总与差异 CSV；需要全部比较行时，逐个提交 `mode="all_part"`、完整 `final` 和已启用 include_matches 的 `part`，生成分片 CSV。分别上传；不假设平台支持合并或追加文件。

每阶段收到 `status="error"` 时停止整个任务，不调用 finalize、导出、上传或通知。统一说明“核对未完成：阶段、query_id、原因；未使用部分结果”。不自动重试；修复失败原因后重新执行当前完整分片，其他分片只有在范围一致且来源快照仍可证明一致时才能复用，否则全流程重来。

## 结果判断

固定差异方向为左侧减右侧；规则6为成本还原委外费减财务委外金额。规则2/3、4/5分别共用同一成本字段，结果不应被当成四组独立证据。

返回每项规则的比较数、差异数、左右总额、净差额、assessment及差异行，并给出 validation 的计划数/已验证数、分片数、来源行数。数量跨物料合计只作辅助勾稽，不能随意称为件或公斤。

- `match`：该项数值一致且无额外完整性疑点。
- `different`：存在数值差异，差异不代表执行失败。
- `no_data` / `missing_side`：明确空数据或单侧缺失，不能说通过。
- `zero_amount_review`：规则4/5双侧总金额为零，需要业务复核。
- `review_required`：规则7有关联或单位异常，数值碰巧相等也不能说通过。

逐行 `status` 保留原技能的纯数值比较含义；最终验收采用 assessment。重复业务键属于完整性错误，停止处理，不沿用本地字典覆盖行为。新增这些判断不改数量、金额公式和无容差口径。

## 版本与范围

V3.0.0 为本地核对规则的云端运行架构版，参考 reconcile v3 的 manifest/receipt、Decimal、LIMIT+1、内存CSV和失败即停止协议。不复用其业务表、仓库白名单、实例标识或7天切片阈值。部署包仅含本入口、运行时及三个 reference；开发测试和迁移报告位于包外。
