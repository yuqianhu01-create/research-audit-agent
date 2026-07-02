import argparse
import json
import re
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"


def slugify(value):
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value or "").strip("-").lower()
    return value[:70] or "untitled"


def text_blob(record):
    return " ".join([
        record.get("title", ""),
        record.get("abstract", ""),
        record.get("why_candidate", ""),
        record.get("source", ""),
    ]).lower()


def display_type(record):
    source_type = record.get("source_type", "")
    article_type = record.get("article_type", "")
    blob = text_blob(record)
    if article_type == "clinical_trial_record" or source_type in {"clinical_trial", "clinical_trial_database"}:
        return "临床试验登记"
    if source_type == "preprint":
        return "预印本"
    if source_type == "regulator":
        return "监管信息"
    if source_type in {"company_site", "company_news"}:
        return "公司/产业动态"
    if source_type == "official_product_page":
        return "产品功能更新"
    if "review" in blob or "综述" in blob:
        return "综述/研究进展"
    if any(term in blob for term in ["randomized", "clinical trial", "phase ", "patients", "human"]):
        return "临床/人体研究"
    if any(term in blob for term in ["mouse", "mice", "rat", "murine", "animal"]):
        return "动物研究/临床前"
    if any(term in blob for term in ["clock", "biomarker", "model", "multi-omics", "machine learning"]):
        return "方法学/生物标志物"
    return "机制研究/原创论文"


def field_label(record):
    blob = text_blob(record)
    section = record.get("section", "")
    if "mitochond" in blob:
        return "线粒体衰老"
    if "senescence" in blob or "senolytic" in blob or "sasp" in blob:
        return "细胞衰老/SASP"
    if "nad" in blob or "nmn" in blob or "nicotinamide" in blob:
        return "NAD+代谢"
    if "telomere" in blob:
        return "端粒"
    if "epigen" in blob or "methylation" in blob or "clock" in blob:
        return "表观遗传时钟"
    if "stem cell" in blob:
        return "干细胞衰老"
    if "skin" in blob:
        return "皮肤抗衰"
    if "microbiome" in blob or "gut" in blob or "nutrition" in blob:
        return "肠道菌群/营养"
    if "wearable" in blob or "watch" in blob or "oura" in blob or "garmin" in blob:
        return "可穿戴监测"
    if "clinical" in blob or "trial" in blob or "phase" in blob:
        return "临床转化"
    if "ai" in blob or "artificial intelligence" in blob or "machine learning" in blob:
        return "AI健康管理"
    defaults = {
        "academic": "衰老机制",
        "industry": "产业/监管动态",
        "ai-aging": "AI × 衰老科学",
        "ai-apps": "AI应用落地",
    }
    return defaults.get(section, "抗衰老")


def trim_sentence(value, max_chars):
    value = re.sub(r"\s+", " ", value or "").strip()
    if len(value) <= max_chars:
        return value
    cut = value[:max_chars].rsplit(" ", 1)[0]
    return (cut or value[:max_chars]).rstrip(" ,.;") + "..."


def method_phrase(record):
    blob = text_blob(record)
    if "multi-omics" in blob or "proteomic" in blob or "transcriptomic" in blob:
        return "研究结合多组学、转录组或蛋白组证据"
    if "clinical" in blob or "patients" in blob or "phase" in blob:
        return "资料来自人体研究、临床试验登记或临床数据读出"
    if "machine learning" in blob or "deep learning" in blob or "artificial intelligence" in blob:
        return "研究使用 machine learning（机器学习）或 AI 模型进行分析"
    if "mouse" in blob or "mice" in blob:
        return "研究仍处于动物实验阶段"
    return "研究基于原文报告的实验体系、数据分析或官方披露信息"


def summary_cn(record):
    section = record.get("section", "academic")
    title = record.get("title", "该条目")
    source = record.get("source", "原始来源")
    abstract = trim_sentence(record.get("abstract") or record.get("why_candidate") or title, 210)
    field = field_label(record)

    if section == "academic":
        return (
            f"研究发现：{title} 聚焦{field}，原文指出该方向与衰老机制、功能退化或干预评估密切相关。"
            f"方法：{method_phrase(record)}，并以原文数据支持关键结论。"
            f"意义：该研究可为抗衰老原料筛选、机制验证或检测指标解释提供参考。"
        )
    if section == "industry":
        return (
            f"事件：{source} 发布或维护了与{field}相关的产业信息，反映抗衰老商业化、临床转化或监管环境的近期信号。"
            f"数据：当前条目以官方页面、注册库或监管来源为依据。"
            f"影响：可用于跟踪竞品路线、合作机会和合规窗口。"
        )
    if section == "ai-aging":
        return (
            f"技术方法：该条目关注 AI 与{field}的结合，信息来自{source}。"
            f"关键进展：{abstract}"
            f"应用价值：可为应天系统的衰老评估、候选物筛选或模型指标设计提供技术参照。"
        )
    return (
        f"产品描述：{source} 相关页面展示了 AI 或数字化健康工具在{field}中的应用形态。"
        f"关键数据：本条以官方产品页、注册信息或公开说明为依据，优先观察功能入口、数据采集和反馈闭环。"
        f"竞合分析：可作为 Infinitus 评估用户体验、合作接口和产品差异化设计的参考。"
    )


def opportunity(record):
    section = record.get("section", "academic")
    field = field_label(record)
    if section == "academic":
        return f"可转化为{field}方向的研发假设：用于设计原料筛选指标、机制验证实验，或解释检测报告中的生物年龄/功能衰退信号。"
    if section == "industry":
        return f"可作为{field}商业化雷达：观察竞品管线、监管路径和合作窗口，帮助判断哪些技术路径正在从实验室进入市场。"
    if section == "ai-aging":
        return f"可为应天系统提供{field}模块灵感：关注可接入的数据类型、模型指标和干预推荐逻辑，而不仅是整理信息。"
    return f"可作为产品形态参考：拆解其用户入口、数据采集、AI反馈和复购闭环，寻找可借鉴的健康评估或个性化干预体验。"


def to_website_candidate(record, issue="next"):
    section = record.get("section", "academic")
    title = record.get("title", "")
    return {
        "id": f"{issue}-{section}-{slugify(title)}",
        "channel": section,
        "group": field_label(record),
        "publishedAt": record.get("published_date", "") or "日期待核实",
        "contentType": "current",
        "title": title,
        "summaryDraft": summary_cn(record),
        "originalAbstract": record.get("abstract", "") or record.get("why_candidate", ""),
        "opportunityDraft": opportunity(record),
        "auditStatus": record.get("audit_status"),
        "auditIssues": record.get("audit_issues", []),
        "sourceName": record.get("source", ""),
        "displayType": display_type(record),
        "evidenceLevel": "A-direct source" if record.get("audit_status") == "passed" else "official source needs date review",
        "sources": [
            {
                "name": record.get("source", "source"),
                "url": record.get("url", ""),
                "type": record.get("source_type", ""),
                "titleEn": title,
            }
        ],
        "rawCandidate": record,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(DATA_DIR / "audit_report.json"))
    parser.add_argument("--issue", default="next")
    parser.add_argument("--include-needs-review", action="store_true")
    args = parser.parse_args()

    audited = json.loads(Path(args.input).read_text(encoding="utf-8"))
    allowed = {"passed"}
    if args.include_needs_review:
        allowed.add("needs_review")
    output = [to_website_candidate(item, args.issue) for item in audited if item.get("audit_status") in allowed]
    package = {
        "generatedAt": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "issue": args.issue,
        "records": output,
    }
    output_path = DATA_DIR / "website_candidates.json"
    output_path.write_text(json.dumps(package, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Publishing Agent wrote {len(output)} website candidate records to {output_path}")


if __name__ == "__main__":
    main()
