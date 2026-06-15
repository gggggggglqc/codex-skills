"""
问答知识库管理工具
用法: python qa_manager.py <command> [args...]

支持的命令:
  add       <category> <question> <answer> [quality]  - 记录一条问答
  search    <keyword>                                  - 搜索历史问答
  stats     [category]                                 - 统计问答频次分布
  recent    [N]                                        - 查看最近 N 条问答
  suggest                                              - 分析薄弱环节，生成优化建议
  export    [output_path]                              - 导出问答报告
"""
import sys, os, json
from datetime import datetime, timedelta
from collections import Counter

# 知识库文件路径（与本 skill 同目录）
SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QA_FILE = os.path.join(SKILL_DIR, "qa_records.json")

# 问题分类关键词映射
CATEGORY_KEYWORDS = {
    "凭证审核": ["凭证", "审核", "未审核", "凭证状态", "已审", "反审核"],
    "出纳推送": ["付款单", "收款单", "推送失败", "出纳", "push", "下推"],
    "费用差异": ["差异", "对不上", "不一致", "CI168", "CI044", "CI046", "科目", "分摊", "比对"],
    "EP费用编码": ["EP0", "EP1", "EP2", "EP3", "费用编码", "净利V2", "净利表"],
    "报表口径": ["公式", "口径", "计算逻辑", "毛利率", "收入", "退款", "含税", "不含税"],
    "流程排期": ["几号", "什么时候", "排期", "负责人", "月初", "结账", "对数"],
    "重复检查": ["重复", "重复凭证", "重复上传", "CI165"],
    "数据查询": ["查一下", "查数据", "多少", "汇总", "明细", "统计"],
    "系统问题": ["报错", "错误", "失败", "超时", "连不上"],
}

def load_records():
    if not os.path.exists(QA_FILE):
        return []
    with open(QA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_records(records):
    with open(QA_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

def auto_category(question: str) -> str:
    """根据问题内容自动分类"""
    scores = Counter()
    for cat, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in question:
                scores[cat] += 1
    if scores:
        return scores.most_common(1)[0][0]
    return "其他"

def add_record(category: str, question: str, answer: str, quality: str = "good"):
    """添加一条问答记录"""
    records = load_records()
    record = {
        "id": len(records) + 1,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "category": category if category != "auto" else auto_category(question),
        "question": question,
        "answer": answer[:2000],  # 答案截断防止文件过大
        "quality": quality,  # good / partial / failed
    }
    records.append(record)
    save_records(records)
    return {"status": "ok", "id": record["id"], "category": record["category"]}

def search_records(keyword: str):
    """搜索历史问答"""
    records = load_records()
    matches = []
    for r in records:
        if keyword in r["question"] or keyword in r["answer"] or keyword in r.get("category", ""):
            matches.append(r)
    matches.sort(key=lambda x: x["timestamp"], reverse=True)
    return {"关键词": keyword, "匹配数": len(matches), "结果": matches[:30]}

def get_stats(category: str = None):
    """统计问答分布"""
    records = load_records()
    if category:
        records = [r for r in records if r.get("category") == category]

    total = len(records)
    cat_counts = Counter(r.get("category", "未知") for r in records)
    quality_counts = Counter(r.get("quality", "unknown") for r in records)

    # 按日期统计
    date_counts = Counter()
    for r in records:
        day = r["timestamp"][:10]
        date_counts[day] += 1

    # 高频问题（相似问题聚合）
    q_words = Counter()
    for r in records:
        q = r["question"][:50]  # 取前50字符作为key
        q_words[q] += 1
    hot_questions = [{"question": q, "count": c} for q, c in q_words.most_common(10) if c > 1]

    return {
        "总问答数": total,
        "按分类": dict(cat_counts.most_common()),
        "按质量": dict(quality_counts.most_common()),
        "按日期": dict(sorted(date_counts.items(), reverse=True)[:14]),
        "高频问题": hot_questions,
    }

def get_recent(n: int = 10):
    """最近 N 条问答"""
    records = load_records()
    records.sort(key=lambda x: x["timestamp"], reverse=True)
    return {"数量": min(n, len(records)), "记录": records[:n]}

def suggest_improvements():
    """分析薄弱环节，生成优化建议"""
    records = load_records()
    if not records:
        return {"建议": "暂无问答记录，无法生成优化建议。"}

    suggestions = []

    # 1. 检查 failed 和 partial 的问答
    failed = [r for r in records if r.get("quality") == "failed"]
    partial = [r for r in records if r.get("quality") == "partial"]
    if failed:
        failed_cats = Counter(r.get("category") for r in failed)
        suggestions.append({
            "类型": "回答失败的分类",
            "详情": dict(failed_cats.most_common()),
            "建议": "这些分类的问题机器人无法回答，需要在对应技能中补充知识或脚本。"
        })
    if partial:
        partial_cats = Counter(r.get("category") for r in partial)
        suggestions.append({
            "类型": "回答不完整的分类",
            "详情": dict(partial_cats.most_common()),
            "建议": "这些分类的回答质量不高，考虑优化对应技能的说明或脚本。"
        })

    # 2. 检查高频但未覆盖的问题
    cat_counts = Counter(r.get("category") for r in records)
    top_cats = cat_counts.most_common(3)
    if top_cats:
        suggestions.append({
            "类型": "最常被问到的分类",
            "详情": dict(top_cats),
            "建议": "高频分类应确保对应的查询脚本和知识文档完善、准确。"
        })

    # 3. 检查"其他"分类（说明自动分类没覆盖到）
    others = [r for r in records if r.get("category") == "其他"]
    if len(others) > len(records) * 0.2:
        other_questions = [r["question"][:60] for r in others[:20]]
        suggestions.append({
            "类型": "未分类问题过多",
            "详情": {"未分类数": len(others), "占比": f"{len(others)/len(records)*100:.0f}%", "示例": other_questions},
            "建议": "需要增加新的分类关键词，或新建对应技能来覆盖这些问题。"
        })

    # 4. 最近 7 天趋势
    recent_7d = [r for r in records
                 if r["timestamp"] >= (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")]
    if recent_7d:
        recent_cats = Counter(r.get("category") for r in recent_7d)
        suggestions.append({
            "类型": "最近7天热点",
            "详情": {"问答数": len(recent_7d), "分类分布": dict(recent_cats.most_common())},
            "建议": "近期高频问题应优先确保回答准确。"
        })

    return {"问答总数": len(records), "优化建议": suggestions}

def export_report(output_path: str = None):
    """导出问答报告"""
    records = load_records()
    stats = get_stats()
    improvements = suggest_improvements()

    report = {
        "生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "统计概览": stats,
        "优化建议": improvements,
        "全部记录": records,
    }

    if output_path is None:
        output_path = os.path.join(SKILL_DIR, "qa_report.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    return {"状态": "ok", "文件": output_path, "记录数": len(records)}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    try:
        if cmd == "add" and len(sys.argv) >= 5:
            cat = sys.argv[2]
            q = sys.argv[3]
            a = sys.argv[4]
            quality = sys.argv[5] if len(sys.argv) >= 6 else "good"
            print(json.dumps(add_record(cat, q, a, quality), ensure_ascii=False, indent=2))
        elif cmd == "search" and len(sys.argv) >= 3:
            print(json.dumps(search_records(sys.argv[2]), ensure_ascii=False, indent=2))
        elif cmd == "stats":
            cat = sys.argv[2] if len(sys.argv) >= 3 else None
            print(json.dumps(get_stats(cat), ensure_ascii=False, indent=2))
        elif cmd == "recent":
            n = int(sys.argv[2]) if len(sys.argv) >= 3 else 10
            print(json.dumps(get_recent(n), ensure_ascii=False, indent=2))
        elif cmd == "suggest":
            print(json.dumps(suggest_improvements(), ensure_ascii=False, indent=2))
        elif cmd == "export":
            path = sys.argv[2] if len(sys.argv) >= 3 else None
            print(json.dumps(export_report(path), ensure_ascii=False, indent=2))
        else:
            print(f"未知命令或参数不足: {cmd}")
            print(__doc__)
            sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False, indent=2))
        sys.exit(1)
