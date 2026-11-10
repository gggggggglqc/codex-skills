# 内部执行规程

本文件面向执行智能体，核对前读取，用户结果说明保持业务表达。

## 请求参数

下文S指完整request_scope对象，例如：

```json
{"start_date":"2026-09-01","end_date":"2026-09-30","calc_month":"2026-09-01","rules":[1,2,3,4,5,6,7]}
```

可选finish_time_field为billing_time（默认）、create_time或finish_time；可选report_quantity_mode为adjusted_from_finish（默认）或用户明确要求的report_work_num。报工日期固定使用表头create_time。成本规则仅支持同一成本月、最多31天。不得额外增加工厂、仓库、状态或成本类型过滤。

结果assessment为match、different、no_data、missing_side、zero_amount_review或review_required，分别对应一致、数值差异、无数据、单侧缺失、双侧零金额待核及关联/单位待核。用户回复使用业务中文表述；只有全部所选规则assessment=match才能表述为全部一致。

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

