# 运行协议 V3.0.0

## 阶段结构

所有请求均含action与request_scope，接口为 `run(request) -> dict`。完整源码与请求作为一次代码提交，不执行本地命令。run捕获输入、类型和协议错误，返回status=error、stage、query_id、error、business_conclusion=null、files=[]；不得把错误输出当作业务结果。

plan返回queries、manifest、plan_digest、all_partitions。每条查询含query_id、source、db_name、sql、required_columns、row_limit、partition、time_slice、sql_sha256。manifest不重复SQL正文；consume会从request_scope与partition重新生成并逐字段比较，不能删除清单项或篡改行上限。

consume的payload仅包含一个完整manifest和一个responses数组。每条回执的query_id必须与计划一一对应，success/truncated/has_more必须为严格布尔值。raw为未改写的SQL响应字符串。支持对象行数组JSON、标量repr，以及单个text/content文本块信封；多块、有分页、错误对象、datetime/Decimal对象repr及未知信封均拒绝，不能只取第一块。

工具若返回其他行信封，必须先根据真实契约修改解析器并新增样例测试；禁止临时让智能体手工抽取行来伪装原始响应。

consume输出含version、request_scope、partition、rule_results、include_matches、validation、artifact_digest。validation含planned_query_count、verified_query_count、source_row_counts、payload_bytes、plan_digest、partition。SHA256仅检测阶段输出意外混用/改写，不是数据库真实性签名，真实状态由工具原始回执和编排审计提供。

finalize必须携带全部consume输出。检查范围、版本、摘要、所有必要分片、各分片查询数与来源统计。验证完成后合并净差额、统计与差异行。validation增加verified_partitions、required_partitions、total_source_rows和part_digests。全量成功后的所有规则assessment均为match时all_rules_match才为true。

render_csv携带完整final；mode=differences导出汇总与差异，mode=all_part还携带一个完整part，仅允许导出在final.part_digests内且include_matches=true的分片。文件描述含file_name、content、content_type；download_status=not_uploaded，只有上传工具成功后智能体才返回URL。完整导出采用分片多文件，不依赖临时磁盘或平台未证明支持的文件追加。

## 全量与分片

1–6最多6个共用来源查询，不重复执行相同口径。7固定64片、每片两来源。双方SQL使用对应关联键的MOD(CRC32(CAST(key AS CHAR)),64)，NULL归入第0片后由Python拒绝，不能被WHERE悄悄排除。每片覆盖同一完整日期范围；跨日期但同月同键数据仍在同片比较。

分片不是数据库快照。应在已关账或确认无数据变更的期间执行；数据仍变动时，需要目标平台提供一致性快照策略。不能因所有页都返回成功就宣称跨查询具有事务一致性。检测或怀疑数据变化时重新取得同一一致来源，否则报告证据边界，不作验收通过结论。

## 保护阈值及依据

| 保护项 | 值 | 依据与越界行为 |
| --- | --- | --- |
| 日期 | 同一成本月、最多31天 | 本技能按月成本核对；跨成本月拆任务 |
| 查询返回 | 5000行，SQL LIMIT 5001 | 物料组历史约1889，留余量；N+1即失败 |
| 规则7分片 | 64 | 历史月188097条/侧，平均每片约2939，预计适配5000行；偏斜则失败，不能截断 |
| 查询 | 每片最多6，全任务最多134 | 6共用汇总+64×2领料 |
| 累计来源行 | 550000 | 历史领料双侧376194行及汇总留余量；超限缩小时间范围 |
| 输入、输出 | 各8MiB/调用 | 比参考版10MiB保守，逐片控制；不是已核验的平台限制 |
| SQL | 8192 UTF-8字节 | 固定模板，不生成动态IN明细查询；当前无二级键批次 |
| 执行 | 30秒/调用 | 纯计算预算，完成前超时则失败；宿主还必须提供硬超时 |
| 内存 | 256MiB宿主预算 | 行数/载荷控制降低占用；运行时不测量或伪称强制RSS上限，需平台验证配额 |
| CSV | 2MiB/文件、4MiB/调用 | 内存输出与上传体积保护，实际上传限额更低时采用更低值 |

这些是工程初始保护值，参考历史数据确定，未通过生产规模或真实MCP验证。平台更低上限优先；调整前同步代码、文档和边界测试。不能照搬参考对账技能7天、500行、1500查询的限制。

## 旧输出兼容关系

云端统一用left_value/right_value/diff/status，原规则1的finish_qty/report_qty，2的finish_qty/cost_qty，3的finish_qty/produce_qty，4/5的finish_amount/cost_amount，6的actual_restore_outsource_amount/finance_outsource_amount，7的iom_qty/mes_qty分别映射左右值。字段命名统一是显式输出契约变化，不是数值口径变化。规则7保留原业务键、单据、基本单位、MES生产单位字段；增加anomalies。完整比较行可选分片导出，默认不传大量一致行。
