import argparse
import json
import re
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"

BAD_EVIDENCE_PREFIXES = (
    "clinicaltrials.gov match:",
    "pubmed recent search match",
    "crossref recent journal search match",
    "arxiv search match",
)

SECTION_FALLBACK_GROUP = {
    "academic": "衰老机制",
    "industry": "产业/监管动态",
    "ai-aging": "AI × 衰老科学",
    "ai-apps": "AI应用落地",
}

TITLE_TRANSLATIONS = {
    "multi-omics profiling reveals systemic rejuvenation of the aged kidney through senolytic therapy": "多组学分析揭示通过 senolytic 疗法使老年肾脏发生系统性年轻化",
    "longitudinal lipidomic markers of cardiac aging and risk of coronary heart disease": "美国印第安人心脏衰老与冠心病风险的纵向脂质组学标志物",
    "targeted treatment for hyperuricemia": "高尿酸血症的靶向治疗：药物管线",
    "the role of depressive symptoms, episodic memory, and executive functioning on prospective memory": "抑郁症状、情景记忆和执行功能在前瞻记忆中的作用",
    "cystic fibrosis nutrition": "囊性纤维化营养：回应 2024 年 ESPEN-ESPGHAN-ECFS 指南后的新趋势",
    "growth hormone on adipose tissue": "生长激素在生理和病理水平上对脂肪组织的调节作用及其与肥胖的关系",
    "development and validation of an interpretable machine learning model": "可解释机器学习模型的开发与验证",
    "multimodal machine learning for menopause status prediction": "使用 LLM 提取的超声特征进行绝经状态预测的多模态机器学习",
    "rebalancing health investment across the life course": "在整个生命历程中重新平衡健康投资",
    "implications of autolysosome": "自噬溶酶体-星形胶质细胞相关特征在阿尔茨海默病发病机制中的意义",
    "the auditory trap": "听觉陷阱：早期语义冲突和晚期监控失效驱动认知老化中的错误记忆",
    "artificial intelligence-driven design": "人工智能驱动的多芯和多模光纤设计、优化与控制",
}


def slugify(value):
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value or "").strip("-").lower()
    return value[:70] or "untitled"


def clean_text(value):
    value = re.sub(r"<[^>]+>", " ", str(value or ""))
    value = value.replace("\ufffd", "")
    value = value.replace("鈥", "'").replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", value).strip()


def normalized_title(value):
    return re.sub(r"[^a-z0-9]+", " ", clean_text(value).lower()).strip()


def text_blob(record):
    return clean_text(
        " ".join(
            [
                record.get("title", ""),
                record.get("abstract", ""),
                record.get("page_excerpt", ""),
                record.get("why_candidate", ""),
                record.get("source", ""),
            ]
        )
    ).lower()


def has_word(blob, word):
    return re.search(rf"(?<![a-z0-9]){re.escape(word.lower())}(?![a-z0-9])", blob) is not None


def evidence_text(record):
    why = clean_text(record.get("why_candidate") or "")
    if why.lower().startswith(BAD_EVIDENCE_PREFIXES):
        why = ""
    for key in ("abstract", "page_excerpt"):
        value = clean_text(record.get(key) or "")
        if value and not value.lower().startswith(BAD_EVIDENCE_PREFIXES):
            return value
    if why.lower().startswith("official "):
        return fallback_evidence(record)
    return why or clean_text(record.get("title") or "")


def fallback_evidence(record):
    source = clean_text(record.get("source") or "原始来源")
    source_l = source.lower()
    source_type = record.get("source_type", "")
    if "insilico" in source_l:
        return "该链接指向 Insilico Medicine 官方新闻与管线页面，可用于核对其 AI 药物发现平台、候选药物和临床里程碑。"
    if "life biosciences" in source_l:
        return "该链接指向 Life Biosciences 官方新闻或管线页面，可用于核对其细胞年轻化和年龄相关疾病开发动态。"
    if "bioage" in source_l:
        return "该链接指向 BioAge Labs 官方管线页面，可用于核对其基于衰老生物学的药物开发方向。"
    if "retro" in source_l:
        return "该链接指向 Retro Biosciences 官方页面，可用于核对其细胞重编程、再生医学和长寿平台定位。"
    if "hevolution" in source_l:
        return "该链接指向 Hevolution Foundation 官方新闻页面，可用于核对长寿研究资助、项目和生态建设动态。"
    if "cambrian" in source_l:
        return "该链接指向 Cambrian Bio 官方管线页面，可用于核对其多管线长寿治疗组合。"
    if "newlimit" in source_l or "new limit" in source_l:
        return "该链接指向 NewLimit 官方页面，可用于核对其表观遗传重编程和细胞状态调控平台。"
    if "juvenescence" in source_l:
        return "该链接指向 Juvenescence 官方页面，可用于核对其长寿投资组合与产业布局。"
    if source_type == "official_product_page":
        return f"该链接指向 {source} 官方产品页面，可用于核对其功能描述、数据入口和用户端健康管理体验。"
    if source_type == "regulator":
        return f"该链接指向 {source} 官方监管页面，可用于核对产品开发、合规和审批相关信息。"
    return clean_text(record.get("title") or source)


def trim_sentence(text, max_chars=280):
    text = clean_text(text)
    if len(text) <= max_chars:
        return text
    cut = text[:max_chars].rsplit(" ", 1)[0].rstrip(" ,.;")
    return cut + "..."


def industry_sector_label(record):
    blob = text_blob(record)
    source = clean_text(record.get("source") or "").lower()
    if any(term in blob or term in source for term in ["cosmetic", "skincare", "skin aging", "beauty", "l'oreal", "lauder", "shiseido"]):
        return "\u62a4\u80a4\u6297\u8870/\u7f8e\u5986\u79d1\u6280"
    if any(term in blob or term in source for term in ["functional food", "nutraceutical", "nutrition", "supplement", "nestle", "amway", "haleon", "nutraingredients", "foodnavigator"]):
        return "\u529f\u80fd\u98df\u54c1/\u8425\u517b\u8865\u5145"
    if any(term in blob or term in source for term in ["fda", "ema", "hsa", "nmpa", "regulatory", "approval", "guidance"]):
        return "\u76d1\u7ba1/\u5408\u89c4"
    if any(term in blob or term in source for term in ["medical device", "wearable", "digital health", "device"]):
        return "\u533b\u7597\u5668\u68b0/\u6570\u5b57\u5065\u5eb7"
    if any(term in blob or term in source for term in ["market", "mckinsey", "deloitte", "trend", "consumer"]):
        return "\u5e02\u573a\u8d8b\u52bf/\u5546\u4e1a\u7b56\u7565"
    if any(term in blob or term in source for term in ["biotech", "pipeline", "clinical", "phase", "senolytic", "reprogramming", "bioage", "insilico", "retro", "cambrian", "juvenescence", "newlimit", "life biosciences"]):
        return "\u751f\u7269\u6280\u672f/\u957f\u5bff\u7ba1\u7ebf"
    return "\u4ea7\u4e1a\u52a8\u6001"


def industry_event_label(record):
    blob = text_blob(record)
    source_type = record.get("source_type", "")
    if source_type in {"investor_relations", "sec_filing"} or any(term in blob for term in ["sec filing", "investor relations"]):
        return "\u6295\u8d44\u8005\u5173\u7cfb/\u76d1\u7ba1\u62ab\u9732"
    if any(term in blob for term in ["launch", "new product", "product launch"]):
        return "\u65b0\u54c1\u53d1\u5e03"
    if any(term in blob for term in ["partnership", "collaboration", "collaborates"]):
        return "\u6218\u7565\u5408\u4f5c"
    if any(term in blob for term in ["funding", "financing", "investment", "raises"]):
        return "\u878d\u8d44/\u6295\u8d44"
    if any(term in blob for term in ["acquisition", "merger", "m&a"]):
        return "\u5e76\u8d2d/\u6574\u5408"
    if source_type in {"clinical_trial", "clinical_trial_database"} or any(term in blob for term in ["clinical trial", "phase", "pipeline"]):
        return "\u4e34\u5e8a\u7ba1\u7ebf\u66f4\u65b0"
    if source_type == "regulator" or any(term in blob for term in ["approval", "clearance", "guidance", "regulatory", "fda", "ema", "hsa", "nmpa"]):
        return "\u76d1\u7ba1\u6279\u51c6/\u5408\u89c4\u66f4\u65b0"
    if any(term in blob for term in ["manufacturing", "factory", "production"]):
        return "\u5236\u9020\u521b\u65b0"
    if source_type == "market_research" or any(term in blob for term in ["market", "trend", "consumer"]):
        return "\u5e02\u573a\u8d8b\u52bf"
    if source_type == "conference" or "conference" in blob:
        return "\u4f1a\u8bae\u52a8\u6001"
    if source_type in {"industry_media", "professional_media", "credible_media"}:
        return "\u4ea7\u4e1a\u4e13\u4e1a\u62a5\u9053"
    return "\u516c\u53f8R&D/\u5546\u4e1a\u52a8\u6001"


def field_label(record):
    blob = text_blob(record)
    section = record.get("section", "")
    if section == "industry":
        return industry_sector_label(record)
    if "mitochond" in blob:
        return "线粒体衰老"
    if any(term in blob for term in ["senescence", "senolytic", "sasp"]):
        return "细胞衰老/SASP"
    if any(has_word(blob, term) for term in ["nad", "nmn", "nr"]) or "nicotinamide" in blob:
        return "NAD+代谢"
    if "telomere" in blob:
        return "端粒"
    if any(term in blob for term in ["epigen", "methylation", "clock"]):
        return "表观遗传时钟"
    if "stem cell" in blob:
        return "干细胞衰老"
    if "skin" in blob:
        return "皮肤抗衰"
    if any(term in blob for term in ["microbiome", "gut", "nutrition"]):
        return "肠道菌群/营养"
    if any(term in blob for term in ["wearable", "watch", "oura", "garmin"]):
        return "可穿戴监测"
    if any(term in blob for term in ["clinical", "trial", "phase", "pipeline"]):
        return "临床转化"
    if any(term in blob for term in ["ai", "artificial intelligence", "machine learning", "deep learning"]):
        return "AI健康管理"
    return SECTION_FALLBACK_GROUP.get(section, "抗衰老")


def display_type(record):
    source_type = record.get("source_type", "")
    article_type = record.get("article_type", "")
    blob = text_blob(record)
    if record.get("section") == "industry":
        return industry_event_label(record)
    if article_type == "clinical_trial_record" or source_type == "clinical_trial":
        return "临床试验登记"
    if source_type == "clinical_trial_database":
        return "临床试验数据库"
    if source_type == "preprint":
        return "预印本"
    if source_type == "regulator":
        return "监管信息"
    if source_type in {"company_site", "company_news"}:
        return "公司/产业动态"
    if source_type == "official_product_page":
        return "产品功能更新"
    if "review" in blob:
        return "综述/研究进展"
    if any(term in blob for term in ["randomized", "clinical trial", "phase ", "patients", "cohort", "human"]):
        return "临床/人体研究"
    if any(term in blob for term in ["mouse", "mice", "rat", "murine", "animal"]):
        return "动物研究/临床前"
    if any(term in blob for term in ["clock", "biomarker", "model", "multi-omics", "machine learning"]):
        return "方法学/生物标志物"
    return "机制研究/原创论文"


def direct_title_zh(record):
    title = clean_text(record.get("title", ""))
    title_l = title.lower()
    source = clean_text(record.get("source") or "")
    source_l = source.lower()
    section = record.get("section", "")

    if section == "industry":
        if "life biosciences" in source_l:
            return "Life Biosciences 官方新闻与管线更新"
        if "insilico" in source_l:
            return "Insilico Medicine 官方管线与新闻更新"
        if source_l == "fda":
            return "FDA 与衰老相关产品开发有关的指南和药物批准更新"
        if "bioage" in source_l:
            return "BioAge Labs 官方管线与公司更新"
        if "retro" in source_l:
            return "Retro Biosciences 官方细胞重编程与长寿更新"
        if "hevolution" in source_l:
            return "Hevolution Foundation 官方长寿资助与项目更新"
        if "cambrian" in source_l:
            return "Cambrian Bio 官方长寿治疗管线更新"
        if "newlimit" in source_l or "new limit" in source_l:
            return "NewLimit 官方表观遗传重编程公司更新"
        if "juvenescence" in source_l:
            return "Juvenescence 官方长寿公司与投资组合更新"
        if source:
            return f"{source} 抗衰老产业动态"

    if section == "ai-apps":
        if "oura" in source_l:
            return "Oura 官方心血管年龄与健康功能更新"
        if "insidetracker" in source_l:
            return "InsideTracker 官方 AI 健康平台更新"
        if "function health" in source_l:
            return "Function Health 官方生物标志物平台更新"
        if "apple" in source_l:
            return "Apple Watch 健康功能更新"
        if "garmin" in source_l:
            return "Garmin 官方健康科学与健康功能更新"
        if "zoe" in source_l:
            return "ZOE 官方个性化营养平台更新"
        if "viome" in source_l:
            return "Viome 官方 AI 健康智能平台更新"
        if "levels" in source_l:
            return "Levels 官方代谢健康平台更新"
        if source:
            return f"{source} AI 健康应用更新"

    for needle, cn in TITLE_TRANSLATIONS.items():
        if needle in title_l:
            return cn

    if section == "ai-aging":
        return translate_unknown_title(title, section, record)
    if section == "academic":
        return translate_unknown_title(title, section, record)
    return title[:88].rstrip(" ,.;") + "..." if len(title) > 92 else title


def translate_unknown_title(title, section, record):
    title = clean_text(title)
    if not title:
        return f"{field_label(record)}相关条目"
    return title


def has_chinese_title(record):
    title_cn = direct_title_zh(record)
    title = clean_text(record.get("title") or "")
    if record.get("section") in {"industry", "ai-apps"}:
        return True
    return bool(title_cn and title_cn != title and re.search(r"[\u4e00-\u9fff]", title_cn))


def evidence_stage_sentence(record):
    blob = text_blob(record)
    if "multi-omics" in blob or "proteomic" in blob or "transcriptomic" in blob:
        return "研究主要依托多组学、转录组或蛋白组证据，需要关注样本来源、分析流程和可重复性。"
    if any(term in blob for term in ["patients", "human", "cohort", "clinical"]):
        return "资料来自人体研究、临床登记或人群数据，适合优先提取可量化指标和真实世界验证线索。"
    if any(term in blob for term in ["machine learning", "deep learning", "artificial intelligence"]):
        return "原文使用 machine learning（机器学习）或 AI 模型分析，应重点核对输入数据、性能指标和外部验证。"
    if "mouse" in blob or "mice" in blob:
        return "证据仍处于动物实验阶段，应明确区分机制启发与人体功效结论。"
    return "该条目以原始网页、摘要或官方披露作为证据来源，适合进入候选池后继续人工精读。"


def core_finding_cn(record):
    blob = text_blob(record)
    source = clean_text(record.get("source") or "原始来源")
    if "multi-omics profiling" in blob and "kidney" in blob:
        return "研究显示，senolytic 疗法可在老年肾脏中引发跨细胞类型的分子层面年轻化信号，重点涉及衰老标志物、炎症、纤维化和代谢通路。"
    if "lipidomic" in blob and "cardiac" in blob:
        return "研究把纵向脂质组变化与心脏舒张功能下降及冠心病风险联系起来，提示脂质代谢可作为心脏衰老的早期分子窗口。"
    if "hyperuricemia" in blob or "uric" in blob:
        return "文章梳理高尿酸血症治疗管线，重点呈现不同靶向药物如何影响尿酸生成、排泄和相关代谢风险。"
    if "prospective memory" in blob or "depressive symptoms" in blob:
        return "研究讨论抑郁症状、情景记忆和执行功能与前瞻记忆之间的关系，为老龄化中的认知功能评估提供线索。"
    if "cystic fibrosis nutrition" in blob:
        return "文章围绕囊性纤维化营养管理的新指南展开，讨论治疗进展后营养需求、体重管理和长期健康目标的变化。"
    if "interpretable machine learning" in blob:
        return "研究开发并验证可解释机器学习模型，用于从临床或健康数据中识别风险，重点在于模型输出能否被医生和用户理解。"
    if "multimodal machine learning" in blob or "llm-extracted" in blob:
        return "研究把多模态机器学习与 LLM 特征抽取结合，用于从影像或临床文本中预测健康状态。"
    if "health investment" in blob and "life course" in blob:
        return "文章从生命周期角度重新审视健康投入，强调不同年龄段健康干预的价值排序。"
    if "alzheimer" in blob or "autolysosome" in blob:
        return "研究关注神经退行性疾病中的细胞通路特征，尝试用分子信号解释疾病进展和衰老相关脑健康风险。"
    if "false memories" in blob or "cognitive aging" in blob:
        return "研究分析认知老化中的错误记忆形成机制，重点关注早期语义冲突和后期监控失效。"
    if "insilico" in source.lower():
        return "该官方来源用于核对 Insilico Medicine 的 AI 药物发现平台、候选管线和临床推进动态。"
    if record.get("section") == "industry":
        return f"该官方来源用于核对 {source} 在长寿技术、管线、监管或产业生态中的最新公开信息。"
    if record.get("section") == "ai-apps":
        return f"该官方来源用于核对 {source} 的产品功能、数据入口和用户端健康管理体验。"
    return trim_sentence(evidence_text(record), 150)


def academic_implication(record):
    blob = text_blob(record)
    if "multi-omics" in blob and "kidney" in blob:
        return "这类结果的启发在于把衰老肾脏从单一指标扩展为多组学网络，可用于设计“清除衰老细胞后组织是否真正恢复”的评价框架，并为后续 senolytic 组合干预寻找可量化终点。"
    if "lipidomic" in blob and "cardiac" in blob:
        return "它提示心血管衰老不应只看传统血脂，而可进一步拆分脂质组特征、舒张功能和冠心病风险之间的链条，适合转化为代谢健康或心脏年龄评估中的候选指标。"
    if "mitochond" in blob:
        return "它的意义在于把线粒体质量控制、能量代谢和组织功能衰退连接起来，后续可用于判断原料或干预方案是否真正作用于线粒体靶向通路，而不是只停留在抗氧化叙事。"
    if "senolytic" in blob or "senescence" in blob or "sasp" in blob:
        return "它为细胞衰老干预提供了更具体的观察窗口：哪些细胞群被影响、SASP 是否下降、组织微环境是否改善，后续可作为抗衰机制验证和联合干预设计的参考。"
    if any(term in blob for term in ["epigen", "methylation", "clock"]):
        return "这类研究的价值在于帮助区分“年龄预测”与“可解释的生物老化机制”，可用于优化生物年龄检测报告，避免把时钟读数简单包装成产品功效。"
    if any(term in blob for term in ["nad", "nmn", "nicotinamide riboside"]):
        return "它适合用于重新审视 NAD+ 补充策略：不同前体在组织分布、代谢路径和功能读数上的差异，能帮助研发团队更精细地选择适用场景和评价指标。"
    if "stem cell" in blob:
        return "它把干细胞耗竭、微环境变化和再生能力下降放在同一框架中，后续可启发围绕组织修复、免疫支持或营养干预的机制假设。"
    if "microbiome" in blob or "gut" in blob:
        return "它提示肠道菌群不只是健康背景变量，而可能是连接营养、炎症和衰老表型的调节层，适合转化为益生元、发酵产物或饮食干预的证据线索。"
    if "skin" in blob or "photoaging" in blob or "collagen" in blob:
        return "它对护肤抗衰的启发在于把成分作用落到屏障、胶原、炎症或光老化通路上，便于后续区分可被实验验证的机制与单纯营销概念。"
    if "memory" in blob or "cognitive" in blob or "alzheimer" in blob:
        return "它把认知功能、情绪状态或神经退行风险纳入衰老观察，适合为脑健康评估、生活方式建议和长期随访指标提供更具体的内容素材。"
    if "hyperuricemia" in blob or "uric" in blob:
        return "它提示代谢风险管理可以从单一尿酸控制扩展到炎症、肾脏负担和心代谢联动，适合作为功能食品或营养干预场景的边界参考。"
    if any(term in blob for term in ["machine learning", "deep learning", "artificial intelligence"]):
        return "它的启发在于把复杂数据转化为可解释分层或风险预测，后续可用于评估哪些模型输出能真正进入健康报告、分层管理或干预推荐。"
    return f"它的意义应从原文中的实验对象、关键读数和结论边界中提取：优先沉淀与{field_label(record)}相关的可测指标、可验证通路和适用人群，而不是把研究发现直接改写为产品功效。"


def academic_summary(record):
    field = field_label(record)
    finding = core_finding_cn(record)
    return (
        f"这篇文章围绕{field}提供了新的研究线索。核心内容可概括为：{finding} "
        f"{evidence_stage_sentence(record)} {academic_implication(record)}"
    )


def industry_summary(record):
    source = clean_text(record.get("source") or "原始来源")
    source_l = source.lower()
    evidence = core_finding_cn(record)
    if "insilico" in source_l:
        return (
            f"Insilico Medicine 的官方信息反映 AI 药物发现平台与候选管线的推进，原始页面可核验内容为：{evidence} "
            "这类动态的重点是观察算法能力如何转化为靶点选择、候选分子、适应症和临床里程碑。对无限极而言，它适合作为 AI 研发平台化叙事的参考，而不是被写成单一产品功效。"
        )
    if "life biosciences" in source_l:
        return (
            f"Life Biosciences 的官方信息可用于跟踪细胞年轻化与年龄相关疾病管线，原始页面可核验内容为：{evidence} "
            "它的产业价值在于展示长寿技术公司如何组织平台、管线和融资故事。对产品开发团队而言，可借鉴其把机制方向拆成适应症、临床路径和合作机会的表达方式。"
        )
    if "bioage" in source_l:
        return (
            f"BioAge Labs 的页面聚焦衰老生物学药物开发，原始页面可核验内容为：{evidence} "
            "这类信息适合观察公司如何从人群数据和衰老机制中选择靶点，并推进到适应症和临床终点。它对抗衰老产品开发的启发是：概念必须落到可测指标、清晰人群和验证路径。"
        )
    if "retro" in source_l:
        return (
            f"Retro Biosciences 的页面聚焦细胞重编程、再生医学和长寿平台，原始页面可核验内容为：{evidence} "
            "它更适合作为前沿公司技术组合与长期愿景的产业观察。对无限极而言，可参考其如何把高门槛技术拆成平台、管线和合作叙事，但不宜直接转写成消费级功效承诺。"
        )
    if "hevolution" in source_l:
        return (
            f"Hevolution Foundation 的信息反映长寿研究资助和生态建设方向，原始页面可核验内容为：{evidence} "
            "这类动态有助于判断国际资金正在支持哪些衰老机制、临床转化和公共健康议题。它的机会点在于帮助团队寻找合作网络、会议议题和未来两三年可能升温的研发方向。"
        )
    if "cambrian" in source_l:
        return (
            f"Cambrian Bio 的官方页面用于观察多管线长寿治疗公司的组合式布局，原始页面可核验内容为：{evidence} "
            "它的价值在于展示一个公司如何同时管理不同机制、适应症和开发阶段。对无限极而言，可借鉴其把抗衰老方向拆成多个可验证项目组合，而不是只押注单一成分或单一概念。"
        )
    if "newlimit" in source_l or "new limit" in source_l:
        return (
            f"NewLimit 的官方页面聚焦表观遗传重编程与细胞状态调控，原始页面可核验内容为：{evidence} "
            "这类动态适合用于观察长寿产业如何把基础机制包装成平台型技术。对研发团队的启发是：表观遗传年龄、细胞状态和功能恢复可以被拆解成检测指标、机制验证和长期产品概念。"
        )
    if "juvenescence" in source_l:
        return (
            f"Juvenescence 的官方信息适合跟踪长寿投资组合和商业化方向，原始页面可核验内容为：{evidence} "
            "它的重点不是单篇论文，而是赛道布局：哪些机制被产业资本反复押注，哪些适应症更容易形成临床或消费场景。对企业策略而言，可用于补充竞品地图和潜在合作标的清单。"
        )
    if source_l == "fda":
        return (
            f"FDA 页面属于监管信息源，原始页面可核验内容为：{evidence} "
            "它不代表某个抗衰产品已经获批，而是用于校准功能声称、临床证据和合规边界。对企业而言，价值在于提前识别哪些表达适合科普教育，哪些表述可能接近疾病治疗或药品宣称。"
        )
    return (
        f"{source} 提供了抗衰老产业相关线索，原始页面可核验内容为：{evidence} "
        "正式进入周报前应继续核对发布日期、事件主体和新增进展。它可作为产业观察候选，但不能替代第一方公告或监管披露。"
    )

def ai_aging_implication(record):
    blob = text_blob(record)
    if "interpretable" in blob or "explain" in blob:
        return "它的启发不只是模型准确率，而是如何把黑箱预测拆成可解释变量；如果用于应天系统，更适合作为风险因子解释、医生审核线索或用户报告中的“为什么”模块。"
    if "multimodal" in blob or "llm" in blob or "large language model" in blob:
        return "它说明多模态数据和 LLM 可以承担信息抽取与整合角色，适合启发体检报告、影像、问卷和生活方式文本的统一解析，而关键风险在于证据溯源和输出一致性。"
    if "biological age" in blob or "clock" in blob or "methylation" in blob:
        return "它对系统建设的价值在于提供生物年龄建模思路：不仅要给出年龄分数，还要展示输入变量、误差范围和可干预因素，避免把模型结果变成不可解释的单一数字。"
    if "drug discovery" in blob or "target" in blob or "compound" in blob:
        return "它更适合放在 AI 辅助研发模块中，用来观察模型如何从多组学、靶点网络或化合物空间中提出候选方向，后续需要用实验和临床证据过滤算法假设。"
    if "retinal" in blob or "imaging" in blob or "ultrasound" in blob:
        return "它提示非侵入式影像可成为衰老评估入口，后续可比较采集成本、用户接受度和预测误差，判断是否适合作为低门槛筛查或会员体检模块。"
    if "wearable" in blob or "sensor" in blob:
        return "它的启发在于把连续监测数据转化为衰老趋势，而不是一次性检测结论；若用于产品，需要重点设计长期反馈、异常提示和行为干预闭环。"
    return "它的价值应落在可集成性上：明确数据来源、模型任务、性能指标和输出解释方式，再判断是否能成为应天系统中的评估、分层或干预推荐模块。"


def ai_apps_implication(record):
    blob = text_blob(record)
    source_l = clean_text(record.get("source") or "").lower()
    if "oura" in source_l or "cardiovascular age" in blob:
        return "可借鉴的是把复杂生理信号翻译成用户能持续理解的年龄化指标，并用趋势变化驱动睡眠、运动和恢复建议。"
    if "apple" in source_l:
        return "可借鉴的是低负担、高频率的健康提醒机制，适合思考如何把抗衰建议嵌入日常设备和长期习惯，而不是依赖一次性报告。"
    if "garmin" in source_l:
        return "可借鉴的是把训练、恢复、睡眠和心肺指标串成一个连续健康状态面板，用于设计运动营养干预后的反馈闭环。"
    if "zoe" in source_l or "nutrition" in blob or "microbiome" in blob:
        return "可借鉴的是从个体化饮食反应出发构建营养建议，把微生物组、血糖或饮食记录转化为更细的抗衰营养场景。"
    if "viome" in source_l:
        return "可借鉴的是把检测结果包装成可执行的成分和饮食建议，但需要特别关注证据等级、推荐透明度和用户能否理解原因。"
    if "levels" in source_l or "glucose" in blob:
        return "可借鉴的是用实时反馈改变饮食行为，适合启发代谢健康管理产品中的即时提示、分层目标和复购服务设计。"
    if "insidetracker" in source_l or "function health" in source_l or "biomarker" in blob:
        return "可借鉴的是把大量生物标志物整理为优先级明确的行动清单，适合优化体检报告到个性化干预建议之间的转化路径。"
    if "clinic" in blob or "longevity clinic" in blob:
        return "可借鉴的是检测、解释、干预和随访的一体化服务模型，适合评估线下健康管理和线上报告系统如何衔接。"
    return "可借鉴的是产品如何把数据采集、结果解释、行动建议和复访机制连成闭环；进入正式参考前仍需区分用户体验创新与真实疗效证据。"


def ai_aging_summary(record):
    field = field_label(record)
    evidence = core_finding_cn(record)
    return (
        f"这条信息关注 AI 与{field}的结合，核心内容可概括为：{evidence} "
        f"{ai_aging_implication(record)}"
    )


def ai_apps_summary(record):
    source = clean_text(record.get("source") or "原始来源")
    source_l = source.lower()
    evidence = core_finding_cn(record)
    if "oura" in source_l:
        angle = "把可穿戴数据转化为心血管年龄、睡眠、恢复和长期健康趋势。"
    elif "apple" in source_l:
        angle = "把日常佩戴设备变成健康监测和风险提醒入口。"
    elif "garmin" in source_l:
        angle = "把运动、恢复、睡眠和心肺指标组合成连续健康反馈。"
    elif "zoe" in source_l:
        angle = "把微生物组和代谢反应转化为个性化营养建议。"
    elif "viome" in source_l:
        angle = "把微生物组和分子检测结果转化为 AI 健康建议。"
    elif "levels" in source_l:
        angle = "把连续血糖数据转化为可行动的代谢健康反馈。"
    elif "insidetracker" in source_l or "function health" in source_l:
        angle = "把生物标志物检测转化为面向用户的健康报告和建议。"
    else:
        angle = "把健康数据转化为可读、可追踪、可行动的用户反馈。"
    return (
        f"{source} 展示的是 AI 或数字化健康产品的落地形态，核心信息可概括为：{evidence} "
        f"它的核心产品逻辑是{angle} {ai_apps_implication(record)}"
    )


def narrative_summary(record):
    section = record.get("section", "academic")
    if section == "academic":
        return academic_summary(record)
    if section == "industry":
        return industry_summary(record)
    if section == "ai-aging":
        return ai_aging_summary(record)
    return ai_apps_summary(record)


def opportunity(record):
    section = record.get("section", "academic")
    source_l = clean_text(record.get("source") or "").lower()
    field = field_label(record)
    if section == "academic":
        blob = text_blob(record)
        if "senolytic" in blob or "senescence" in blob:
            return "可把衰老细胞清除后的多组学变化拆成机制指标，用于评估 senolytic 方向是否存在可转化的检测终点或联合干预假设。"
        if "lipid" in blob or "cardiac" in blob:
            return "可提取脂质组和心血管风险相关指标，作为抗衰健康评估中“代谢-心脏年龄”解释模块的参考证据。"
        if "hyperuricemia" in blob or "uric" in blob:
            return "可观察高尿酸与代谢健康、炎症和肾脏风险之间的连接，辅助判断功能食品或营养干预能否进入代谢风险管理场景。"
        if "memory" in blob or "cognitive" in blob:
            return "可把认知功能、情绪状态与老龄化评估连接起来，为健康年龄报告中的脑健康和生活方式建议提供参考。"
        return f"从原文中提取可测指标、实验体系和可验证通路，判断{field}是否能转化为原料筛选、机制验证或检测报告解释。"
    if section == "industry":
        if "insilico" in source_l:
            return "观察 AI 药物发现公司如何把算法能力沉淀为管线资产，反推应天系统需要哪些数据、靶点和验证闭环。"
        if source_l == "fda":
            return "用于校准合规边界：哪些抗衰表达适合科普教育，哪些会接近疾病治疗或药品宣称。"
        if "hevolution" in source_l:
            return "用于寻找国际长寿研究的资金流向和合作网络，辅助判断未来热点主题。"
        if "bioage" in source_l:
            return "学习其从人群数据到靶点、适应症和临床终点的转化路径。"
        if "retro" in source_l:
            return "参考其把高门槛长寿技术拆成平台、管线和长期愿景的表达方式。"
        if "cambrian" in source_l:
            return "参考其多管线组合策略，把抗衰老研发拆成不同机制、证据阶段和商业化路径。"
        if "newlimit" in source_l or "new limit" in source_l:
            return "关注表观遗传重编程如何被转化为可检测指标、细胞功能验证和长期干预概念。"
        if "juvenescence" in source_l:
            return "用于补充长寿产业投资地图，识别资本持续关注的机制方向和合作标的。"
        return "更新竞品/合作标的地图，重点看技术平台、适应症选择、临床阶段和商业化叙事。"
    if section == "ai-aging":
        blob = text_blob(record)
        if "interpretable" in blob or "explain" in blob:
            return "重点借鉴可解释模型输出，把 AI 结果从黑箱分数转化为用户和研发团队都能理解的风险因子与行动建议。"
        if "multimodal" in blob or "llm" in blob:
            return "观察多模态数据和 LLM 抽取能力如何降低人工整理成本，为应天系统的体检报告解析和问答模块提供参考。"
        if "biological age" in blob or "clock" in blob:
            return "提取年龄预测模型的输入变量、误差指标和外部验证方式，评估能否升级为生物年龄解释模块。"
        return "拆解其数据输入、模型输出和解释方式，评估哪些能力可作为应天系统模块参考。"

    if "oura" in source_l:
        return "借鉴其把连续佩戴数据包装成心血管年龄和趋势反馈的方式，用于设计更直观的健康年龄展示。"
    if "insidetracker" in source_l:
        return "参考其把血液生物标志物转译为行动建议的产品链路，优化检测报告到干预方案的衔接。"
    if "function health" in source_l:
        return "观察其大规模检测套餐如何降低用户进入门槛，为体检数据标准化和会员服务设计提供参考。"
    if "zoe" in source_l:
        return "借鉴其把微生物组、血糖反应和饮食建议连接起来的机制，用于营养抗衰内容和个性化推荐。"
    if "viome" in source_l:
        return "关注其从微生物组/分子检测到 AI 建议的表达方式，评估是否可用于肠道菌群与抗衰产品教育。"
    if "garmin" in source_l:
        return "拆解其睡眠、恢复、HRV 和运动指标的组合呈现，作为可穿戴数据进入健康年龄评估的参考。"
    if "apple" in source_l:
        return "参考其把健康监测功能做成低负担提醒的交互方式，帮助减少用户理解和持续使用门槛。"
    if "levels" in source_l:
        return "借鉴连续血糖反馈如何转化为饮食行为改变，用于代谢健康和营养干预产品的用户教育。"
    return "拆解用户入口、数据采集、报告呈现和复购机制，寻找可借鉴的健康评估或个性化干预体验。"


def industry_clinical_trial_publishable(record):
    blob = text_blob(record)
    reject_terms = [
        "coronary artery bypass", "oxygen reserve", "spirometry",
        "mindfulness", "exposure therapy", "present centered therapy",
        "mobility score", "hemodialysis", "vascular access",
        "respiratory complications", "homebound older adults",
    ]
    if any(term in blob for term in reject_terms):
        return False
    required_terms = [
        "senolytic", "senescence", "nad", "nmn", "nicotinamide riboside",
        "biological age", "skin aging", "photoaging", "longevity",
        "healthy aging", "healthspan", "cellular reprogramming",
        "epigenetic reprogramming", "nutraceutical", "supplement",
        "alzheimer", "biomarker-chip", "biomarker chip",
    ]
    business_terms = [
        "phase", "trial", "clinical", "device", "diagnosis", "assay",
        "drug", "intervention", "sponsor", "pipeline", "biomarker",
    ]
    return any(term in blob for term in required_terms) and any(term in blob for term in business_terms)


def display_title_cn(record):
    section = record.get("section", "")
    if section == "ai-apps":
        return ai_apps_title_cn(record)
    if section == "industry":
        return industry_title_cn(record)
    return direct_title_zh(record)


def ai_apps_title_cn(record):
    source = clean_text(record.get("source") or "")
    source_l = source.lower()
    if "oura" in source_l:
        return "Oura 的心血管年龄与可穿戴健康监测功能更新"
    if "insidetracker" in source_l:
        return "InsideTracker 的血液生物标志物健康建议服务更新"
    if "function health" in source_l:
        return "Function Health 的会员制生物标志物检测服务更新"
    if "apple" in source_l:
        return "Apple Watch 的日常健康监测服务更新"
    if "garmin" in source_l:
        return "Garmin 的运动恢复与健康科学监测功能更新"
    if "zoe" in source_l:
        return "ZOE 的个性化营养与肠道健康服务更新"
    if "viome" in source_l:
        return "Viome 的 AI 微生物组健康建议服务更新"
    if "levels" in source_l:
        return "Levels 的连续血糖代谢健康服务更新"
    return f"{source or '该产品'} 的 AI 健康管理服务更新"


def industry_title_cn(record):
    source = clean_text(record.get("source") or "")
    source_l = source.lower()
    title = clean_text(record.get("title") or "")
    if "insilico" in source_l:
        return "Insilico Medicine 的 AI 药物发现管线更新"
    if "life biosciences" in source_l:
        return "Life Biosciences 的细胞年轻化管线更新"
    if "bioage" in source_l:
        return "BioAge Labs 的衰老生物学药物管线更新"
    if "retro" in source_l:
        return "Retro Biosciences 的细胞重编程平台更新"
    if "hevolution" in source_l:
        return "Hevolution Foundation 的长寿研究资助与项目更新"
    if "cambrian" in source_l:
        return "Cambrian Bio 的长寿治疗管线布局更新"
    if "newlimit" in source_l or "new limit" in source_l:
        return "NewLimit 的表观遗传重编程平台更新"
    if "juvenescence" in source_l:
        return "Juvenescence 的长寿投资组合更新"
    if "l'oreal" in source_l or "loreal" in source_l:
        return "L'Oreal 的皮肤抗衰与美妆科技更新"
    if "estee" in source_l or "lauder" in source_l:
        return "雅诗兰黛集团的护肤抗衰产品与研发更新"
    if "shiseido" in source_l:
        return "资生堂的皮肤科学与抗衰产品更新"
    if "nestle" in source_l:
        return "Nestle Health Science 的健康老龄化营养产品更新"
    if "amway" in source_l:
        return "Amway 的营养补充与健康老龄化产品更新"
    if "haleon" in source_l:
        return "Haleon 的消费者健康与营养补充产品更新"
    if source_l == "fda":
        return "FDA 的抗衰相关产品开发与合规信息更新"
    if record.get("source_type") in {"clinical_trial", "clinical_trial_database"}:
        if "alzheimer" in title.lower() and ("biomarker" in title.lower() or "assay" in title.lower()):
            return "阿尔茨海默病生物标志物芯片检测的临床登记更新"
        return f"{source} 中与抗衰管线相关的临床登记更新"
    return f"{source or '相关机构'} 的抗衰产业动态更新"


def display_summary(record):
    section = record.get("section", "")
    if section == "ai-apps":
        return ai_apps_display_summary(record)
    if section == "industry":
        return industry_display_summary(record)
    return narrative_summary(record)


def industry_display_summary(record):
    source = clean_text(record.get("source") or "")
    source_l = source.lower()
    title = clean_text(record.get("title") or "")
    title_l = title.lower()
    if record.get("source_type") in {"clinical_trial", "clinical_trial_database"}:
        if "alzheimer" in title_l and ("biomarker" in title_l or "assay" in title_l):
            return "该 ClinicalTrials.gov 条目登记的是用于阿尔茨海默病诊断的红细胞保存样本 biomarker-chip assay（生物标志物芯片检测）。它的产业意义在于把神经退行性疾病早筛从传统认知量表推进到可检测工具，适合关注诊断器械、伴随检测和老年脑健康管理服务的商业化路径。"
        return "该临床登记只应作为抗衰相关管线线索使用，正式进入产业周报前必须确认干预产品、企业主体、适应症和新增里程碑；若缺少这些信息，不应包装成产业动态。"
    if "insilico" in source_l:
        return "Insilico Medicine 的官方页面用于跟踪其 AI 药物发现平台、候选管线和临床推进。该信息的重点不是单个产品功效，而是观察 AI 如何从靶点发现、候选分子设计走向临床读出，对企业判断 AI 研发平台的转化能力和合作窗口有参考价值。"
    if "life biosciences" in source_l:
        return "Life Biosciences 以细胞年轻化和年龄相关疾病管线为核心。该来源适合观察 longevity biotech 如何组织平台、适应症和临床里程碑，可为抗衰技术商业化叙事、合作标的筛选和研发管线布局提供参考。"
    if "bioage" in source_l:
        return "BioAge Labs 的管线围绕衰老生物学和人体数据驱动的靶点选择展开。它的商业价值在于展示如何把衰老机制转化为明确适应症、临床终点和药物开发路径，可作为从基础机制走向产品验证的案例。"
    if "loreal" in source_l or "lauder" in source_l or "shiseido" in source_l:
        return f"{source} 的信息更适合作为护肤抗衰和美妆科技观察：重点看新品、成分机制、皮肤测量技术和消费者沟通方式。对产品开发而言，可提炼其如何把皮肤屏障、胶原、光老化或细胞修复转化为可理解的功效叙事。"
    if "nestle" in source_l or "amway" in source_l or "haleon" in source_l:
        return f"{source} 的信息适合跟踪健康老龄化、营养补充和功能食品的商业化方向。重点应放在目标人群、核心成分、证据表达和渠道策略，判断哪些营养概念正在从科学线索变成可销售的产品语言。"
    if "fda" in source_l:
        return "FDA 来源用于校准监管边界和产品开发要求。它不代表某个抗衰产品已经获批，而是帮助判断哪些表述属于健康教育，哪些可能接近疾病治疗或药品宣称，对功能食品、护肤和检测服务的合规表达很关键。"
    return f"{source} 可作为抗衰产业观察来源。正式写入周报时，应从原文提取具体事件：哪家公司、哪个产品或管线、发生了什么商业动作、日期和数字是什么，以及它对功能食品、护肤、检测或生物技术研发有什么实际影响。"


def ai_apps_display_summary(record):
    source = clean_text(record.get("source") or "")
    source_l = source.lower()
    if "insidetracker" in source_l:
        return "InsideTracker 提供基于血液 biomarker（生物标志物）和个人数据的健康建议服务。它的产品价值在于把检测结果转化为可执行的营养、运动和生活方式建议；对无限极的启发是，健康年龄或抗衰报告不能只给分数，还要把指标异常、优先级和行动路径讲清楚。"
    if "function health" in source_l:
        return "Function Health 主打会员制的大规模生物标志物检测服务，将多项实验室指标组织成持续健康管理入口。它适合观察体检数据如何被产品化：从一次性检测转为年度订阅、趋势追踪和个性化建议。"
    if "zoe" in source_l:
        return "ZOE 的服务围绕个体化营养，结合肠道微生物组、血糖反应和饮食数据生成饮食建议。它的启发在于把“吃什么”从通用科普变成基于个人代谢反应的推荐，可为营养抗衰内容和会员服务设计提供参考。"
    if "viome" in source_l:
        return "Viome 将微生物组和分子检测结果转化为 AI 健康建议，核心是把复杂检测解释成成分、饮食和生活方式行动。可借鉴的是检测结果到建议生成的产品链路，同时需要关注证据透明度和推荐边界。"
    if "garmin" in source_l:
        return "Garmin 的健康科学功能把运动、睡眠、恢复、心率变异性等可穿戴数据组织成日常健康反馈。它的启发在于用连续数据观察身体状态变化，适合思考抗衰产品如何结合运动营养和长期行为管理。"
    if "oura" in source_l:
        return "Oura 将戒指采集的睡眠、恢复和心血管信号转化为用户可理解的健康趋势，例如心血管年龄。它适合参考如何把复杂传感器数据做成低负担、可持续使用的抗衰健康反馈。"
    if "levels" in source_l:
        return "Levels 通过连续血糖监测帮助用户理解饮食和生活方式对代谢的影响。它的启发在于把实时数据转化为行为反馈，可用于思考代谢健康、营养干预和长期会员服务的闭环设计。"
    return narrative_summary(record)


def display_opportunity(record):
    if record.get("section") == "industry":
        source_type = record.get("source_type")
        if source_type in {"clinical_trial", "clinical_trial_database"}:
            return "仅在确认企业主体、产品/器械、适应症和新增里程碑后，才可作为产业动态；否则应退回待核验。"
    return opportunity(record)


def industry_title_cn(record):
    source = clean_text(record.get("source") or "")
    source_l = source.lower()
    title = clean_text(record.get("title") or "")
    title_l = title.lower()
    if "insilico" in source_l:
        return "Insilico Medicine 的 AI 药物发现管线更新"
    if "life biosciences" in source_l:
        return "Life Biosciences 的细胞年轻化管线更新"
    if "bioage" in source_l:
        return "BioAge Labs 的衰老生物学药物管线更新"
    if "retro" in source_l:
        return "Retro Biosciences 的细胞重编程平台更新"
    if "hevolution" in source_l:
        return "Hevolution Foundation 的长寿研究资助与项目更新"
    if "cambrian" in source_l:
        return "Cambrian Bio 的长寿治疗管线布局更新"
    if "newlimit" in source_l or "new limit" in source_l:
        return "NewLimit 的表观遗传重编程平台更新"
    if "juvenescence" in source_l:
        return "Juvenescence 的长寿投资组合更新"
    if "l'oreal" in source_l or "loreal" in source_l:
        return "L'Oreal 的皮肤抗衰与美妆科技更新"
    if "estee" in source_l or "lauder" in source_l:
        return "雅诗兰黛集团的护肤抗衰产品与研发更新"
    if "shiseido" in source_l:
        return "资生堂的皮肤科学与抗衰产品更新"
    if "nestle" in source_l:
        return "Nestle Health Science 的健康老龄化营养产品更新"
    if "amway" in source_l:
        return "Amway 的营养补充与健康老龄化产品更新"
    if "haleon" in source_l:
        return "Haleon 的消费者健康与营养补充产品更新"
    if source_l == "fda":
        return "FDA 的抗衰相关产品开发与合规信息更新"
    if "fierce biotech" in source_l:
        return "Fierce Biotech 的长寿生物技术融资与管线动态"
    if "endpoints" in source_l:
        return "Endpoints News 的生物技术融资、合作与临床管线动态"
    if "biospace" in source_l:
        return "BioSpace 的抗衰老生物技术公司与市场动态"
    if "stat" in source_l:
        return "STAT 的健康科技与生物技术产业观察"
    if "pharmaceutical technology" in source_l:
        return "Pharmaceutical Technology 的药物管线与医疗技术动态"
    if "cosmeticsdesign" in source_l:
        return "CosmeticsDesign 的护肤抗衰新品与成分创新动态"
    if "nutraingredients" in source_l:
        return "NutraIngredients 的营养补充剂与健康老龄化市场动态"
    if "nutrition insight" in source_l:
        return "Nutrition Insight 的功能营养与健康老龄化产品动态"
    if "foodnavigator" in source_l:
        return "FoodNavigator 的功能食品与健康老龄化市场动态"
    if "longevity.technology" in source_l or "longevity technology" in source_l:
        return "Longevity.Technology 的长寿公司、融资与商业技术动态"
    if "mckinsey" in source_l:
        return "McKinsey 的生命科学与消费者健康市场趋势"
    if "deloitte" in source_l:
        return "Deloitte 的生命科学、健康护理与产业趋势观察"
    if record.get("source_type") in {"clinical_trial", "clinical_trial_database"}:
        if "alzheimer" in title_l and ("biomarker" in title_l or "assay" in title_l):
            return "阿尔茨海默病生物标志物芯片检测的临床登记更新"
        return f"{source} 中与抗衰管线相关的临床登记更新"
    return f"{source or '相关机构'} 的抗衰产业动态更新"


def industry_display_summary(record):
    source = clean_text(record.get("source") or "")
    source_l = source.lower()
    title = clean_text(record.get("title") or "")
    title_l = title.lower()
    if record.get("source_type") in {"clinical_trial", "clinical_trial_database"}:
        if "alzheimer" in title_l and ("biomarker" in title_l or "assay" in title_l):
            return "该 ClinicalTrials.gov 条目登记的是用于阿尔茨海默病诊断的红细胞保存样本 biomarker-chip assay（生物标志物芯片检测）。它的产业意义在于把神经退行性疾病早筛从传统认知量表推进到可检测工具，适合关注诊断器械、伴随检测和老年脑健康管理服务的商业化路径。"
        return "该临床登记只能作为抗衰相关管线线索使用。正式进入产业周报前，必须确认干预产品、企业主体、适应症和新增里程碑；若缺少这些信息，不应包装成产业动态。"
    if "insilico" in source_l:
        return "Insilico Medicine 的官方来源用于跟踪其 AI 药物发现平台、候选管线和临床推进。摘要重点不是单个产品功效，而是观察 AI 如何从靶点发现、候选分子设计走向临床读出，为判断 AI 研发平台的转化能力和合作窗口提供参考。"
    if "life biosciences" in source_l:
        return "Life Biosciences 以细胞年轻化和年龄相关疾病管线为核心。该来源适合观察 longevity biotech 如何组织平台、适应症和临床里程碑，可为抗衰技术商业化叙事、合作标的筛选和研发管线布局提供参考。"
    if "bioage" in source_l:
        return "BioAge Labs 围绕衰老生物学和人体数据驱动靶点选择展开管线。它的商业价值在于展示如何把衰老机制转化为明确适应症、临床终点和药物开发路径，可作为从基础机制走向产品验证的案例。"
    if any(term in source_l for term in ["retro", "cambrian", "newlimit", "juvenescence", "hevolution"]):
        return f"{source} 适合作为长寿生物技术生态观察来源。摘要应提取其平台方向、管线组合、资助或投资布局，并判断这些动作代表哪类机制路线正在被商业化：细胞重编程、senolytic、代谢调控、再生医学或数字化发现平台。"
    if any(term in source_l for term in ["fierce biotech", "endpoints", "biospace", "stat", "pharmaceutical technology"]):
        return f"{source} 属于专业生命科学产业来源，适合追踪抗衰老相关公司的融资、合作、临床管线和监管里程碑。正式写入周报时，应从原文中提取具体公司、资产名称、阶段、金额或合作对象，并判断该事件对长寿生物技术商业化节奏的影响。"
    if any(term in source_l for term in ["cosmeticsdesign", "l'oreal", "loreal", "lauder", "shiseido"]):
        return f"{source} 可用于观察护肤抗衰市场中的新品发布、成分科技、功效验证和消费者沟通方式。摘要应围绕具体品牌、产品线、活性成分或检测技术展开，避免把美妆新闻泛化成生物医药结论。"
    if any(term in source_l for term in ["nutraingredients", "nutrition insight", "foodnavigator", "nestle", "amway", "haleon"]):
        return f"{source} 适合跟踪功能食品、营养补充剂和健康老龄化消费品的商业化方向。摘要重点应写清产品或原料、目标人群、健康声称、证据表达和渠道策略，用来判断哪些营养概念正在形成可销售语言。"
    if any(term in source_l for term in ["mckinsey", "deloitte"]):
        return f"{source} 更适合作为市场趋势和战略背景来源，而不是单篇产品新闻。周报应提取其中关于生命科学、消费者健康、数字健康或供应链变化的结构性判断，帮助团队理解抗衰老产品机会处在什么商业环境中。"
    if "fda" in source_l:
        return "FDA 来源用于校准监管边界和产品开发要求。它不代表某个抗衰产品已经获批，而是帮助判断哪些表述属于健康教育，哪些可能接近疾病治疗或药品宣称，对功能食品、护肤和检测服务的合规表达很关键。"
    if "longevity.technology" in source_l or "longevity technology" in source_l:
        return "Longevity.Technology 是长寿产业垂直来源，适合跟踪公司融资、商业技术、产品化路径和生态变化。摘要应优先说明是哪家公司或技术路线出现新信号，以及它对应药物、诊断、营养、护肤或健康管理中的哪类机会。"
    return f"{source} 可作为抗衰产业观察来源。正式写入周报时，应从原文提取具体事件：哪家公司、哪个产品或管线、发生了什么商业动作、日期和数字是什么，以及它对功能食品、护肤、检测或生物技术研发有什么实际影响。"


def display_opportunity(record):
    if record.get("section") == "industry":
        source = clean_text(record.get("source") or "")
        source_l = source.lower()
        source_type = record.get("source_type")
        if source_type in {"clinical_trial", "clinical_trial_database"}:
            return "仅在确认企业主体、产品/器械、适应症和新增里程碑后，才可作为产业动态；否则应退回待核验。"
        if any(term in source_l for term in ["insilico", "bioage", "life biosciences", "retro", "cambrian", "newlimit", "juvenescence"]):
            return "用于更新长寿生物技术管线地图，重点看靶点、适应症、临床阶段和合作窗口，判断哪些机制方向正在从论文走向资产化。"
        if any(term in source_l for term in ["l'oreal", "loreal", "lauder", "shiseido", "cosmeticsdesign"]):
            return "用于提炼护肤抗衰产品开发灵感：关注成分机制、功效验证读数、皮肤检测技术和消费者可理解的功效表达。"
        if any(term in source_l for term in ["nestle", "amway", "haleon", "nutraingredients", "nutrition insight", "foodnavigator"]):
            return "用于捕捉功能食品和营养补充剂机会：重点看原料、目标人群、健康声称边界、证据表达和渠道打法。"
        if any(term in source_l for term in ["fierce biotech", "endpoints", "biospace", "stat", "pharmaceutical technology", "longevity.technology"]):
            return "用于筛选竞品、合作标的和资本关注方向，帮助判断哪些抗衰技术路线正在获得市场验证。"
        if any(term in source_l for term in ["mckinsey", "deloitte"]):
            return "用于补充市场与战略判断，帮助产品团队把研发主题放进消费者健康、医疗健康和供应链变化的大背景里。"
    return opportunity(record)


def source_allowed_for_section(record):
    section = record.get("section", "")
    source_type = record.get("source_type", "")
    blob = text_blob(record)
    if section == "industry":
        if source_type in {"clinical_trial", "clinical_trial_database"}:
            return industry_clinical_trial_publishable(record)
        allowed = {
            "company_site", "company_news", "investor_relations", "sec_filing",
            "regulator",
            "industry_media", "professional_media", "credible_media",
            "market_research", "conference", "official_product_page",
        }
        sector_signal = any(
            term in blob
            for term in [
                "healthy aging", "healthy ageing", "longevity", "functional food",
                "nutraceutical", "supplement", "cosmetic", "skincare", "skin aging",
                "beauty", "biotech", "medical device", "wearable", "biological age",
                "nad", "nmn", "senolytic", "senescence", "reprogramming",
                "collagen", "microbiome", "menopause", "cognitive health",
                "metabolic health", "anti-aging", "healthspan",
            ]
        )
        return source_type in allowed and (
            sector_signal or source_type in {"company_site", "company_news", "regulator", "investor_relations", "sec_filing", "market_research"}
        )
    if section == "ai-apps":
        return source_type in {"official_product_page", "company_site", "company_news", "regulator"}
    if section == "ai-aging":
        has_ai = any(term in blob for term in ["ai", "artificial intelligence", "machine learning", "deep learning", "model", "llm"])
        has_aging = any(term in blob for term in ["aging", "ageing", "age-related", "longevity", "senescence", "biological age", "alzheimer", "cognitive aging", "menopause"])
        return has_ai and has_aging
    if section == "academic":
        return any(
            term in blob
            for term in [
                "aging", "ageing", "age-related", "longevity", "senescence", "senolytic",
                "mitochond", "nad", "telomere", "epigen", "healthspan", "geroscience",
                "cognitive aging", "cardiac aging",
            ]
        )
    return True


def display_date(record):
    published = clean_text(record.get("published_date") or "")
    if published:
        return published
    if record.get("section") in {"industry", "ai-apps"} and record.get("source_type") in {
        "official_product_page",
        "company_site",
        "company_news",
        "regulator",
        "investor_relations",
        "sec_filing",
        "clinical_trial_database",
    }:
        audited = clean_text(record.get("audited_at") or "")
        if audited:
            return audited[:10]
        return datetime.now(UTC).date().isoformat()
    return "日期待核实"


def to_website_candidate(record, issue="next"):
    title = clean_text(record.get("title", ""))
    return {
        "id": f"{issue}-{record.get('section', 'academic')}-{slugify(title)}",
        "channel": record.get("section", "academic"),
        "group": field_label(record),
        "publishedAt": display_date(record),
        "contentType": "current",
        "title": title,
        "titleCn": display_title_cn(record),
        "summaryDraft": display_summary(record),
        "originalAbstract": evidence_text(record),
        "opportunityDraft": display_opportunity(record),
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

    output = []
    seen = set()
    for item in audited:
        if item.get("audit_status") not in allowed:
            continue
        if not source_allowed_for_section(item):
            continue
        if not has_chinese_title(item):
            continue
        key = normalized_title(item.get("title"))
        if not key or key in seen:
            continue
        seen.add(key)
        output.append(to_website_candidate(item, args.issue))

    package = {
        "generatedAt": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "issue": args.issue,
        "records": output,
    }
    output_path = DATA_DIR / "website_candidates.json"
    output_path.write_text(json.dumps(package, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Publishing Agent wrote {len(output)} website candidate records to {output_path}")


if __name__ == "__main__":
    main()
