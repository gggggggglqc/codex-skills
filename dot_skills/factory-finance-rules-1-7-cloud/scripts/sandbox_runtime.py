"""Stateless cloud runtime. Submit this complete source, then call run(request)."""
import ast
import calendar
import csv
import hashlib
import io
import json
import time
import zlib
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation, localcontext

VERSION = '3.0.0'
RULES = {
    1: ('完工入库与调整后报工数量', 'finish_main', 'report', 'qty', 'qty'),
    2: ('完工入库与实际成本还原数量', 'finish', 'cost', 'qty', 'qty'),
    3: ('完工入库与生产成本管理数量', 'finish', 'cost', 'qty', 'qty'),
    4: ('完工入库与实际成本还原金额', 'finish', 'cost', 'amount', 'amount'),
    5: ('完工入库与生产成本管理金额', 'finish', 'cost', 'amount', 'amount'),
    6: ('实际委外加工与财务委外金额', 'outside', 'finance', 'amount', 'amount'),
    7: ('领料出库与倒冲领料数量', 'issue', 'backflush', 'qty', 'qty'),
}
LIMITS = dict(max_days=31, shards=64, rows_per_query=5000, queries_per_part=6,
              total_queries=134, total_source_rows=550000, payload_bytes=8*1024*1024,
              output_bytes=8*1024*1024, sql_bytes=8192, csv_bytes=2*1024*1024,
              export_bytes=4*1024*1024, execution_seconds=30, memory_budget_mib=256)

class ProtocolError(ValueError):
    def __init__(self, reason, query_id=None):
        super().__init__(reason)
        self.query_id = query_id

def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)

def digest(value):
    return hashlib.sha256(canonical(value).encode('utf-8')).hexdigest()

def require(ok, reason, query_id=None):
    if not ok:
        raise ProtocolError(reason, query_id)

def obj(value, label):
    require(isinstance(value, dict), label+' 必须是对象')
    return value

def number(value):
    require(type(value) in (str, int), '数量/金额必须是十进制字符串或整数，禁止浮点和空值')
    require(len(str(value)) <= 80, '数值文本过长')
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise ProtocolError('非法十进制数') from exc
    require(result.is_finite() and abs(result) < Decimal('1e40'), '数值非有限或超出保护边界')
    require(result.as_tuple().exponent >= -24 and len(result.as_tuple().digits)<=50, '数值精度或指数超出固定SQL数值字段范围')
    return result

def count(value):
    n = number(value)
    require(n >= 0 and n == n.to_integral_value(), '记录数必须是非负整数')
    return int(n)

def key(value):
    require(isinstance(value, str) and 0 < len(value) <= 128, '业务键必须是非空字符串且不超过128字符')
    return value

def scope_of(value):
    v = obj(value, 'request_scope')
    require(set(v) <= {'start_date','end_date','calc_month','rules','finish_time_field','report_quantity_mode'}, '存在不支持的请求字段')
    try:
        start, end = date.fromisoformat(v['start_date']), date.fromisoformat(v['end_date'])
    except (KeyError, ValueError, TypeError) as exc:
        raise ProtocolError('必须提供明确的 start_date/end_date，格式 YYYY-MM-DD') from exc
    require(start.isoformat() == v['start_date'] and end.isoformat() == v['end_date'], '日期格式必须为 YYYY-MM-DD')
    require(0 <= (end-start).days < LIMITS['max_days'], '日期范围必须顺序正确且最多31天')
    require(end.year < 9999, '日期超出支持范围')
    rules = v.get('rules', list(range(1,8)))
    require(isinstance(rules,list) and rules and all(type(n) is int and n in RULES for n in rules), 'rules 只能是1至7的非空整数数组')
    require(len(rules) == len(set(rules)), '规则不可重复')
    month = v.get('calc_month', start.replace(day=1).isoformat())
    try:
        md = date.fromisoformat(month)
    except (ValueError, TypeError) as exc:
        raise ProtocolError('calc_month 必须是 YYYY-MM-01') from exc
    require(md.day == 1 and md.isoformat() == month, 'calc_month 必须是月份首日')
    if set(rules) & {2,3,4,5,6}:
        require(start.replace(day=1) == md and end.replace(day=1) == md, '成本规则只支持同一成本月内的业务范围')
    field = v.get('finish_time_field','billing_time')
    require(field in {'billing_time','create_time','finish_time'}, '完工日期字段不在白名单')
    mode = v.get('report_quantity_mode','adjusted_from_finish')
    require(mode in {'adjusted_from_finish','report_work_num'}, '报工数量模式不在白名单')
    return dict(start_date=start.isoformat(),end_date=end.isoformat(),calc_month=month,
                rules=sorted(rules),finish_time_field=field,report_quantity_mode=mode)

def partitions(scope):
    out = ['summary'] if set(scope['rules']) & set(range(1,7)) else []
    if 7 in scope['rules']:
        out += ['rule7:%02d'%i for i in range(LIMITS['shards'])]
    return out

def sources(scope):
    used = set()
    for r in scope['rules']:
        if r != 7:
            used.update(RULES[r][1:3])
    return sorted(used)

def source_sql(scope, source, shard=None):
    # All identifiers are fixed constants or whitelisted above; dates are parsed ISO values.
    start = "'%s'"%scope['start_date']
    end = "'%s'"%(date.fromisoformat(scope['end_date'])+timedelta(days=1)).isoformat()
    month = "'%s'"%scope['calc_month']
    f = scope['finish_time_field']
    total = 'COALESCE(d.actual_num,0)+COALESCE(d.defective_actual_num,0)'
    bounds = f'h.{f}>={start} AND h.{f}<{end}'
    if source in {'finish_main','finish'}:
        extra = ' AND d.product_type=1' if source=='finish_main' else ''
        sql = (f'SELECT CAST(d.material_code AS CHAR) AS material_code, CAST(SUM({total}) AS CHAR) AS qty, '
               f'CAST(SUM(COALESCE(d.cost_price,0)*({total})) AS CHAR) AS amount, '
               'CAST(COUNT(*) AS CHAR) AS source_count, '
               'CAST(SUM(CASE WHEN COALESCE(d.cost_price,0)=0 THEN 1 ELSE 0 END) AS CHAR) AS zero_price_count '
               'FROM erp_iom.finish_job_stock_order_detail d JOIN erp_iom.finish_job_stock_order h ON h.stock_order_id=d.stock_order_id '
               f'WHERE {bounds}{extra} GROUP BY d.material_code ORDER BY d.material_code')
        columns = ['material_code','qty','amount','source_count','zero_price_count']
        db = 'erp_iom'
    elif source == 'report':
        if scope['report_quantity_mode']=='adjusted_from_finish':
            amount = 'COALESCE(x.finish_qty,0)'
            join = ('LEFT JOIN (SELECT report_work_order_detail_id, '
                    'SUM(COALESCE(actual_num,0)+COALESCE(defective_actual_num,0)) AS finish_qty '
                    'FROM erp_iom.finish_job_stock_order_detail WHERE product_type=1 GROUP BY report_work_order_detail_id) x '
                    'ON x.report_work_order_detail_id=r.detail_id ')
        else:
            amount, join = 'COALESCE(r.report_work_num,0)', ''
        sql = (f'SELECT CAST(r.material_code AS CHAR) AS material_code, CAST(SUM({amount}) AS CHAR) AS qty, '
               'CAST(COUNT(*) AS CHAR) AS source_count FROM mes_aps.report_work_order_detail r '
               'JOIN mes_aps.report_work_order o ON o.report_work_order_id=r.report_work_order_id '+join+
               f'WHERE o.create_time>={start} AND o.create_time<{end} GROUP BY r.material_code ORDER BY r.material_code')
        columns, db = ['material_code','qty','source_count'], 'mes_aps'
    elif source == 'cost':
        sql = ('SELECT CAST(material_code AS CHAR) AS material_code, CAST(SUM(COALESCE(produce_num,0)) AS CHAR) AS qty, '
               'CAST(SUM(COALESCE(actual_produce_amount,0)) AS CHAR) AS amount, CAST(COUNT(*) AS CHAR) AS source_count '
               f'FROM erp_cost.produce_cost WHERE calc_month={month} GROUP BY material_code ORDER BY material_code')
        columns, db = ['material_code','qty','amount','source_count'], 'erp_cost'
    elif source == 'outside':
        sql = ('SELECT CAST(material_code AS CHAR) AS material_code, CAST(SUM(COALESCE(outside_cost,0)) AS CHAR) AS amount, '
               f'CAST(COUNT(*) AS CHAR) AS source_count FROM erp_cost.produce_cost_detail WHERE calc_month={month} '
               "AND status=20 AND parent_id='root' GROUP BY material_code ORDER BY material_code")
        columns, db = ['material_code','amount','source_count'], 'erp_cost'
    elif source == 'finance':
        sql = ('SELECT CAST(d.material_code AS CHAR) AS material_code, '
               'CAST(SUM(COALESCE(d.outsourcing_not_tax_freight_cost,0)) AS CHAR) AS amount, CAST(COUNT(*) AS CHAR) AS source_count '
               'FROM erp_cost.outsourcing_order_detail d JOIN erp_cost.outsourcing_order h ON h.outsourcing_order_id=d.outsourcing_order_id '
               f'WHERE h.order_billing_time>={start} AND h.order_billing_time<{end} AND h.outsourcing_order_type=2 '
               'GROUP BY d.material_code ORDER BY d.material_code')
        columns, db = ['material_code','amount','source_count'], 'erp_cost'
    else:
        require(source in {'issue','backflush'} and type(shard) is int and 0<=shard<64, '非法领料分片')
        if source == 'issue':
            identifier, doc, qty = 'd.material_order_detail_id','d.stock_order_id','d.actual_num'
            table = 'erp_iom.take_material_stock_order_detail d JOIN erp_iom.take_material_stock_order h ON h.stock_order_id=d.stock_order_id'
            bounds, db = f'h.billing_time>={start} AND h.billing_time<{end}', 'erp_iom'
        else:
            identifier, doc, qty = 'd.detail_id','d.take_material_order_id','d.base_unit_apply_num'
            table = 'mes_aps.take_material_order_detail d JOIN mes_aps.take_material_order h ON h.take_material_order_id=d.take_material_order_id'
            bounds, db = f'h.take_time>={start} AND h.take_time<{end}', 'mes_aps'
        sql = (f'SELECT CAST({identifier} AS CHAR) AS detail_id, CAST({doc} AS CHAR) AS doc_id, '
               f'CAST(d.material_code AS CHAR) AS material_code, CAST(COALESCE(d.base_unit_code,\'\') AS CHAR) AS base_unit_code, '
               f'CAST(COALESCE({qty},0) AS CHAR) AS qty FROM {table} WHERE {bounds} '
               f'AND COALESCE(MOD(CRC32(CAST({identifier} AS CHAR)),64),0)={shard} ORDER BY {identifier},{doc}')
        columns = ['detail_id','doc_id','material_code','base_unit_code','qty']
        if source=='backflush':
            sql=sql.replace(' AS qty FROM ', " AS qty, CAST(COALESCE(d.produce_unit_code,'') AS CHAR) AS produce_unit_code FROM ")
            columns.append('produce_unit_code')
    return sql+' LIMIT 5001', columns, db

def plan(scope, part):
    require(part in partitions(scope), '分片不属于当前规则请求')
    used = sources(scope) if part=='summary' else ['issue','backflush']
    queries=[]
    for source in used:
        sql, columns, db = source_sql(scope,source,None if part=='summary' else int(part.split(':')[1]))
        require(len(sql.encode())<=LIMITS['sql_bytes'], 'SQL超长')
        queries.append(dict(query_id=part+':'+source,source=source,db_name=db,sql=sql,
            required_columns=columns,row_limit=5000,partition=part,
            time_slice=dict(start_date=scope['start_date'],end_date_exclusive=(date.fromisoformat(scope['end_date'])+timedelta(days=1)).isoformat()),
            sql_sha256=hashlib.sha256(sql.encode()).hexdigest()))
    manifest=dict(version=VERSION,stage='query',request_scope=scope,partition=part,
        queries=[{k:v for k,v in q.items() if k!='sql'} for q in queries])
    return dict(status='ok',stage='plan',request_scope=scope,partition=part,queries=queries,
        manifest=manifest,plan_digest=digest(manifest),all_partitions=partitions(scope))

def parse_raw(raw, query_id):
    require(isinstance(raw,str) and raw.strip(), 'raw响应为空或不是字符串',query_id)
    def parse(text):
        try:
            return json.loads(text,parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite')))
        except (ValueError,TypeError):
            try:
                return ast.literal_eval(text)
            except (ValueError,SyntaxError,RecursionError) as exc:
                raise ProtocolError('raw不是可解析的JSON/标量repr',query_id) from exc
    value=parse(raw)
    for _ in range(3):
        if isinstance(value,dict) and value.get('isError') is True:
            raise ProtocolError('工具返回isError',query_id)
        if isinstance(value,dict) and (value.get('truncated') is True or value.get('has_more') is True or value.get('success') is False):
            raise ProtocolError('raw原生状态与成功完整回执矛盾',query_id)
        # Accept only single text block envelopes; never silently discard other blocks.
        blocks = value.get('content') if isinstance(value,dict) and 'content' in value else value
        if isinstance(blocks,list) and len(blocks)==1 and isinstance(blocks[0],dict) and 'text' in blocks[0] and blocks[0].get('type','text')=='text' and set(blocks[0])<={'type','text'}:
            value=parse(blocks[0]['text']);continue
        if isinstance(value,dict) and set(value)=={'text'} and isinstance(value['text'],str):
            value=parse(value['text']);continue
        break
    require(isinstance(value,list), 'SQL结果必须是对象行数组，错误对象不能当成一行',query_id)
    require(len(value)<=5000,'命中LIMIT+1哨兵，缩小日期范围',query_id)
    return value

def checked_rows(scope, part, payload):
    expected=plan(scope,part)
    require(payload.get('manifest')==expected['manifest'], 'manifest与当前请求重新生成的查询计划不一致')
    receipts=payload.get('responses')
    require(isinstance(receipts,list), '缺少responses数组')
    by_id={}
    ids={q['query_id'] for q in expected['queries']}
    for receipt in receipts:
        obj(receipt,'回执');qid=receipt.get('query_id')
        require(isinstance(qid,str) and qid in ids, '空或未计划的query_id',qid)
        require(qid not in by_id,'重复query_id',qid)
        for flag,truth in [('success',True),('truncated',False),('has_more',False)]:
            require(type(receipt.get(flag)) is bool and receipt[flag] is truth, '原生状态不完整或异常：'+flag,qid)
        by_id[qid]=receipt
    for q in expected['queries']:
        require(q['query_id'] in by_id,'缺少计划回执',q['query_id'])
    out={}
    for q in expected['queries']:
        qid=q['query_id']; rows=parse_raw(by_id[qid].get('raw'),qid);seen=set()
        for row in rows:
            require(isinstance(row,dict) and set(q['required_columns'])<=set(row),'行不是对象或缺少必填列',qid)
            try:
                identity=key(row['detail_id'] if part!='summary' else row['material_code'])
                if part!='summary':
                    require(zlib.crc32(identity.encode('utf-8'))%64==int(part.split(':')[1]),'业务键不属于当前CRC32分片',qid)
                require(identity not in seen,'重复业务键；禁止覆盖或重复计数',qid);seen.add(identity)
                key(row['material_code'])
                if part!='summary':
                    key(row['doc_id'])
                    require(isinstance(row['base_unit_code'],str),'基本单位编码必须为字符串',qid)
                for field in ('qty','amount'):
                    if field in q['required_columns']:number(row[field])
                if 'source_count' in row:
                    require(count(row['source_count'])>0,'聚合行source_count必须大于零',qid)
                if 'zero_price_count' in row:
                    require(count(row['zero_price_count'])<=count(row['source_count']),'零价记录数大于总记录数',qid)
            except ProtocolError as exc:
                raise ProtocolError(str(exc),qid) from exc
        out[q['source']]=rows
    validation=dict(planned_query_count=len(ids),verified_query_count=len(by_id),
        source_row_counts={s:len(rows) for s,rows in out.items()},payload_bytes=len(canonical(payload).encode()),
        plan_digest=expected['plan_digest'],partition=part)
    return out, validation

def seal(value):
    value['artifact_digest']=digest(value)
    return value

def verify_artifact(value, stage, scope):
    obj(value,'上游输出')
    require(value.get('status')=='ok' and value.get('stage')==stage and value.get('version')==VERSION,'上游阶段、状态或版本不符')
    require(value.get('request_scope')==scope,'上游范围、月份或规则不符')
    require(value.get('artifact_digest')==digest({k:v for k,v in value.items() if k!='artifact_digest'}),'上游输出完整性摘要不一致')
    validation=obj(value.get('validation'),'validation')
    require(type(validation.get('planned_query_count')) is int and type(validation.get('verified_query_count')) is int and
        validation['planned_query_count']==validation['verified_query_count'],'上游查询校验不完整')
    return validation

def compare_summary(scope, data, include_matches):
    maps={s:{r['material_code']:r for r in rows} for s,rows in data.items()}
    out=[]
    for rule in scope['rules']:
        if rule==7:continue
        name,ls,rs,lf,rf=RULES[rule];left,right=maps[ls],maps[rs]
        rows=[];diffs=[];lt=Decimal(0);rt=Decimal(0)
        for material in sorted(set(left)|set(right)):
            l=number(left[material][lf]) if material in left else Decimal(0)
            r=number(right[material][rf]) if material in right else Decimal(0)
            item=dict(material_code=material,left_value=str(l),right_value=str(r),diff=str(l-r),
                status='MATCH' if l==r else 'DIFF',left_present=material in left,right_present=material in right)
            lt+=l;rt+=r
            if l!=r:diffs.append(item)
            if include_matches:rows.append(item)
        assessment='different' if diffs else 'match'
        if not left and not right:assessment='no_data'
        elif not left or not right:assessment='missing_side'
        elif rule in (4,5) and lt==0 and rt==0:assessment='zero_amount_review'
        out.append(dict(rule=rule,name=name,comparison_count=len(set(left)|set(right)),difference_count=len(diffs),
            left_total=str(lt),right_total=str(rt),total_diff=str(lt-rt),assessment=assessment,
            left_source_count=sum(count(r['source_count']) for r in left.values()),
            right_source_count=sum(count(r['source_count']) for r in right.values()),
            zero_price_count=sum(count(r.get('zero_price_count','0')) for r in left.values()),
            difference_rows=diffs,rows=rows if include_matches else None))
    return out

def compare_rule7(data,include_matches):
    left={r['detail_id']:r for r in data['issue']};right={r['detail_id']:r for r in data['backflush']}
    diffs=[];anomalies=[];rows=[];lt=Decimal(0);rt=Decimal(0)
    for identifier in sorted(set(left)|set(right)):
        l=left.get(identifier);r=right.get(identifier)
        lv=number(l['qty']) if l else Decimal(0);rv=number(r['qty']) if r else Decimal(0)
        flags=[]
        if not l or not r:flags.append('missing_side')
        if l and r and l['base_unit_code']!=r['base_unit_code']:flags.append('unit_mismatch')
        if l and r and l['material_code']!=r['material_code']:flags.append('material_mismatch')
        item=dict(detail_id=identifier,material_code=(l or r)['material_code'],stock_order_id=l['doc_id'] if l else '',
            take_material_order_id=r['doc_id'] if r else '',iom_base_unit_code=l['base_unit_code'] if l else '',
            mes_base_unit_code=r['base_unit_code'] if r else '',left_value=str(lv),right_value=str(rv),diff=str(lv-rv),
            mes_produce_unit_code=r['produce_unit_code'] if r else '',
            status='MATCH' if lv==rv else 'DIFF',anomalies=flags)
        if lv!=rv:diffs.append(item)
        if flags:anomalies.append(item)
        if include_matches:rows.append(item)
        lt+=lv;rt+=rv
    assessment='different' if diffs else 'match'
    if not left and not right:assessment='no_data'
    elif anomalies:assessment='review_required'
    return [dict(rule=7,name=RULES[7][0],comparison_count=len(set(left)|set(right)),difference_count=len(diffs),
        left_total=str(lt),right_total=str(rt),total_diff=str(lt-rt),assessment=assessment,
        left_source_count=len(left),right_source_count=len(right),difference_rows=diffs,anomaly_rows=anomalies,
        rows=rows if include_matches else None)]

def consume(scope,request):
    part=request.get('partition');payload=obj(request.get('payload'),'payload')
    include=request.get('include_matches',False)
    require(type(include) is bool,'include_matches必须是布尔值')
    data,validation=checked_rows(scope,part,payload)
    result=compare_summary(scope,data,include) if part=='summary' else compare_rule7(data,include)
    return seal(dict(status='ok',stage='consume',version=VERSION,request_scope=scope,partition=part,
        rule_results=result,include_matches=include,validation=validation))

def finalize(scope,request):
    parts=request.get('parts');require(isinstance(parts,list),'parts必须是完整消费输出数组')
    expected=partitions(scope);seen={};total_rows=0;query_count=0
    for part in parts:
        v=verify_artifact(part,'consume',scope);identifier=part.get('partition')
        require(identifier in expected and identifier not in seen,'上游分片缺失、额外或重复')
        p=plan(scope,identifier)
        require(v.get('plan_digest')==p['plan_digest'] and v.get('partition')==identifier,'上游分片计划不匹配')
        require(v['planned_query_count']==len(p['queries']),'上游查询数不匹配')
        counts=obj(v.get('source_row_counts'),'source_row_counts')
        require(set(counts)=={q['source'] for q in p['queries']},'来源统计不完整')
        for n in counts.values():
            require(type(n) is int and 0<=n<=5000,'来源行数统计非法')
            total_rows+=n
        query_count+=v['verified_query_count'];seen[identifier]=part
        rules={r['rule'] for r in part.get('rule_results',[])}
        require(rules==(set(scope['rules'])-{7} if identifier=='summary' else {7}),'上游规则结果不完整')
    require(set(seen)==set(expected),'缺少必要分片；禁止部分完成')
    require(query_count<=LIMITS['total_queries'] and total_rows<=LIMITS['total_source_rows'],'累计查询数或来源行数超限')
    results=[]
    if 'summary' in seen:
        results=[{k:v for k,v in r.items() if k!='rows'} for r in seen['summary']['rule_results']]
    if 7 in scope['rules']:
        values=[seen[p]['rule_results'][0] for p in expected if p!='summary']
        combined=dict(rule=7,name=RULES[7][0])
        for field in ['comparison_count','difference_count','left_source_count','right_source_count']:
            combined[field]=sum(r[field] for r in values)
        for field in ['left_total','right_total','total_diff']:
            combined[field]=str(sum((number(r[field]) for r in values),Decimal(0)))
        for field in ['difference_rows','anomaly_rows']:
            combined[field]=sorted([item for r in values for item in r[field]],key=lambda r:r['detail_id'])
        combined['assessment']='different' if combined['difference_count'] else 'match'
        if combined['anomaly_rows']:combined['assessment']='review_required'
        if not combined['comparison_count']:combined['assessment']='no_data'
        results.append(combined)
    results.sort(key=lambda r:r['rule'])
    validations=dict(planned_query_count=query_count,verified_query_count=query_count,verified_partitions=len(seen),
        required_partitions=len(expected),total_source_rows=total_rows,
        part_digests={p:seen[p]['artifact_digest'] for p in expected})
    return seal(dict(status='ok',stage='finalize',version=VERSION,request_scope=scope,
        difference_direction='left_minus_right',rule_results=results,validation=validations,
        all_rules_match=all(r['assessment']=='match' for r in results),
        notification=dict(title='工厂财务1-7核对结果',content='\n'.join(
            '规则%s：%s，差异%s行，净差%s'%(r['rule'],r['assessment'],r['difference_count'],r['total_diff']) for r in results))))

def csv_file(name,rows,fields):
    stream=io.StringIO(newline='');writer=csv.DictWriter(stream,fieldnames=fields,extrasaction='ignore')
    writer.writeheader();writer.writerows(rows)
    content='\ufeff'+stream.getvalue()
    require(len(content.encode('utf-8'))<=LIMITS['csv_bytes'],'单个CSV超过2MiB，请按分片导出或缩小范围')
    return dict(file_name=name,content=content,content_type='text/csv; charset=utf-8')

def render(scope,request):
    final=obj(request.get('final'),'final');v=verify_artifact(final,'finalize',scope)
    expected=partitions(scope)
    require(v.get('verified_partitions')==len(expected)==v.get('required_partitions') and
        set(v.get('part_digests',{}))==set(expected),'最终结果并未完成全部必要分片')
    files=[];mode=request.get('mode','differences')
    fields=['material_code','left_value','right_value','diff','status','left_present','right_present']
    detail_fields=['detail_id','material_code','stock_order_id','take_material_order_id','iom_base_unit_code','mes_base_unit_code','mes_produce_unit_code','left_value','right_value','diff','status','anomalies']
    if mode=='all_part':
        part=obj(request.get('part'),'part');verify_artifact(part,'consume',scope)
        require(v['part_digests'].get(part.get('partition'))==part['artifact_digest'],'导出分片不属于完整核对')
        require(part.get('include_matches') is True,'导出全部行必须在consume时显式include_matches=true')
        for r in part['rule_results']:
            files.append(csv_file('规则%s-%s-完整明细.csv'%(r['rule'],part['partition'].replace(':','-')),
                r['rows'],detail_fields if r['rule']==7 else fields))
    else:
        require(mode=='differences','未知导出模式')
        files.append(csv_file('工厂核对汇总.csv',final['rule_results'],
            ['rule','name','assessment','comparison_count','difference_count','left_total','right_total','total_diff']))
        for r in final['rule_results']:
            if r['difference_rows']:
                files.append(csv_file('规则%s-差异明细.csv'%r['rule'],r['difference_rows'],detail_fields if r['rule']==7 else fields))
            if r.get('anomaly_rows'):
                files.append(csv_file('规则7-关联与单位异常.csv',r['anomaly_rows'],detail_fields))
    require(sum(len(f['content'].encode()) for f in files)<=LIMITS['export_bytes'],'单次导出总内容超过4MiB，缩小导出范围')
    return dict(status='ok',stage='render_csv',version=VERSION,request_scope=scope,files=files,
        validation=final['validation'],download_status='not_uploaded')

def run(request):
    """Only interface: a single JSON-compatible request produces a JSON-compatible result."""
    started=time.monotonic();action=request.get('action','unknown') if isinstance(request,dict) else 'unknown'
    try:
        obj(request,'request')
        require(len(canonical(request).encode('utf-8'))<=LIMITS['payload_bytes'],'请求载荷超过8MiB')
        scope=scope_of(request.get('request_scope'))
        with localcontext() as context:
            context.prec=80
            if action=='plan':result=plan(scope,request.get('partition','summary'))
            elif action=='consume':result=consume(scope,request)
            elif action=='finalize':result=finalize(scope,request)
            elif action=='render_csv':result=render(scope,request)
            else:raise ProtocolError('action只能为plan/consume/finalize/render_csv')
        require(time.monotonic()-started<=LIMITS['execution_seconds'],'本次纯计算超过30秒预算')
        require(len(canonical(result).encode('utf-8'))<=LIMITS['output_bytes'],'输出超过8MiB，缩小日期或改用分片结果')
        return result
    except (ProtocolError,ValueError,TypeError,KeyError,OverflowError,RecursionError) as exc:
        return dict(status='error',stage=action,version=VERSION,query_id=getattr(exc,'query_id',None),
            error=str(exc),business_conclusion=None,files=[],
            message='核对未完成：%s；未使用部分结果，未生成差异结论或文件。'%str(exc))
