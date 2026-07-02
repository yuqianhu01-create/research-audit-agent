# Weekly Briefing Generation Instructions

## Priority Rule

The four real briefing files from 2026-06-04 are canonical examples for content selection, taxonomy, title style, and writing depth. They are examples of what researchers want to read, not source documents to show on the website:

- `briefing1_academic_2026-06-04.md`
- `briefing2_industry_2026-06-04.md`
- `briefing3_AI_aging_2026-06-04.md`
- `briefing4_ai_apps_2026-06-04.md`

If the DOCX generation logic conflicts with these four examples, follow the four examples.

Do not generate a Markdown briefing first and then treat that file as the article source. The website must be generated directly from structured article/event records collected from the web.

## Automation Schedule

The production workflow should run automatically every Monday at 09:00 Beijing time (UTC+8). No person should need to manually trigger generation.

For GitHub Actions, schedule this as Monday 01:00 UTC:

```yaml
on:
  schedule:
    - cron: "0 1 * * 1"
```

The automated job should complete the full pipeline:

1. collect candidate items from the web;
2. verify dates, sources, stages, numbers, and claims;
3. write structured website records directly;
4. generate `data.js`;
5. deploy the site;
6. send the new weekly link to Feishu.

## Required Content Shape

Future weekly briefings must keep the same four top-level sections:

1. Academic Frontier
2. Industry Watch
3. AI x Longevity
4. AI in Practice

四份周报的设计遵循"互补不重叠"原则：学术前沿关注基础研究突破，产业进展关注商业化与市场动态，AI 交叉聚焦人工智能与衰老科学的融合创新，应用落地关注可部署的实际产品与工具。四者共同构成从实验室到市场的全景式抗衰老信息监控体系。

Section boundaries are mandatory:

- Academic Frontier: basic biology, mechanisms, translational research, clinical/scientific reviews, biomarkers, and intervention studies where the primary value is scientific evidence. Use papers, DOI/PubMed/PMC, preprints, journal pages, universities, research institutes, government agencies, and international organizations.
- Industry Watch: commercialization, financing, partnerships, licensing, acquisitions, regulatory milestones, clinical-trial business progress, company pipeline moves, market access, and product/category strategy. Use company releases, investor pages, trial registries, regulators, and professional industry media.
- AI x Longevity: AI methods applied to aging science, including AI drug discovery for aging-related diseases, AI aging biomarkers, biological-age clocks, multimodal omics models, target discovery, and computational geroscience. The AI method and aging-science question must both be explicit.
- AI in Practice: deployable products, services, tools, diagnostics, wearables, software workflows, decision-support systems, and clinical/consumer applications that users or institutions can actually adopt. The focus is practical implementation, not only research novelty.

When one candidate could fit multiple sections, assign it to the single section where its primary value is strongest. Do not duplicate the same article, trial, report, source URL, DOI, PMID, NCT number, arXiv ID, or substantially identical title within the same issue. Do not repeat articles from prior issues; maintain `published-article-registry.json` with canonical article keys when past issues are archived.

Within each section, preserve the category logic used by the matching example file. For example, AI x Longevity should keep categories such as AI drug discovery, AI aging biomarkers, ML aging clocks, and AI health management.

Titles should be direct briefing titles, not media-style hooks or questions. Example:

`Insilico Medicine: AI-driven senolytic drug INS018_055 enters Phase IIb clinical trial`

Do not rewrite this into a click-oriented title.

## Four Briefing Specifications

The full system consists of four independent weekly briefings. Each briefing may be rendered as Markdown, website cards, Feishu posts, and structured records, but the structured record is the source of truth. Published files follow `briefing{number}_{topic}_{YYYY-MM-DD}_v{major.minor}.md`.

### Briefing 1: Anti-Aging Academic Frontier

- File name: `briefing1_academic_YYYY-MM-DD.md`.
- Trigger: Monday 08:00 China Standard Time, cron `0 8 * * 1`.
- Readers: R&D teams and academic collaborators.
- Positioning: a research radar for anti-aging basic science. It should help R&D readers scan the weekly scientific pulse quickly. Prefer broad coverage over missing an important direction.
- Target output: 8-12 papers for the full Markdown briefing, about 8000 Chinese characters. Website digest views may show a smaller curated subset, but they must link back to the structured record.
- Search scope: PubMed, Crossref, DOI.org, journal pages, preprint servers, universities, research institutes, and official scientific reports. Search recent two-week publications first. If there are too few qualified current items, add clearly marked reference content from important studies within the past three years or evergreen frameworks. Reference content must show the original date and must not be presented as a current weekly item.
- Required metadata: DOI/PMID, article type, publication status, study organism or population, sample size, source URL, evidence stage, and publication date.
- Theme blocks: mitochondrial aging; telomeres; cellular senescence and SASP; epigenetic clocks; aging interventions; stem-cell aging.
- Screening priority: CNS main journals and major subjournals; field-leading journals such as Nature Aging and Cell Metabolism; application-oriented basic research relevant to Infinitus interests such as botanical actives and anti-aging mechanisms; methodology innovation such as aging clocks and evaluation tools. Clinical or translational potential upgrades an item; purely theoretical mechanism papers are downgraded when short-term application value is limited.
- Summary style: 100-200 Chinese characters using "research finding -> method -> significance". State the core finding first, then the experimental system or key technology, then the value for aging research or anti-aging product development. Keep key English terms with Chinese explanation. Use affirmative language for human clinical evidence and clearly mark animal-only or preclinical findings.
- Markdown format: H1 briefing title, H2 date and compiler, H3 theme block, H4 bold paper title, summary body, source link, key points, and disclaimer. Separate theme blocks with `---`.

### Briefing 2: Anti-Aging Industry Progress

- File name: `briefing2_industry_YYYY-MM-DD.md`.
- Trigger: Tuesday 08:00 China Standard Time, cron `0 8 * * 2`.
- Readers: R&D management and business strategy teams.
- Positioning: a business intelligence digest answering "what is happening commercially in anti-aging?" Focus on movement from laboratory to shelf: financing, launches, regulatory shifts, trials, competitors, and market data.
- Target output: 8-12 industry signals for the full Markdown briefing, readable in about 10 minutes.
- Search scope: company releases, investor relations pages, regulatory filings, deal documents, ClinicalTrials.gov, Chinese and international trial registries, FDA/EMA/NMPA/SAMR/EFSA pages, and high-credibility industry media for cross-checking. Search recent one-to-two-week dynamics first. If too few qualified items exist, add important nodes from the last 12 months or decision-relevant clinical/regulatory references from the past three years. Older reference items must show original dates and cannot be written as this week's events.
- Theme blocks: clinical trial progress; financing and M&A; regulatory policy; supplements and functional-food launches; skincare anti-aging launches; market trends.
- Screening priority: direct relevance to Infinitus business such as NMN/NAD+, botanical anti-aging, functional foods, and supplements; signal strength such as FDA approval, large financing above USD 100 million, and China regulatory shifts; first-mover window for competitor moves, especially China-market launches; clear commercial pathway.
- Summary style: 100-150 Chinese characters using "event -> data -> impact". State what happened, include key numbers such as financing amount, trial size, product pricing, approval or launch status, then explain concrete relevance to Infinitus or the China anti-aging industry. Add category tags such as `senolytic clinical trial` or `regulatory policy change`. Avoid long background explanations.
- Markdown format: same hierarchy as Briefing 1, but each item title uses "number + bold title + category tag"; add `**分类**: category` below the title.

### Briefing 3: AI x Anti-Aging

- File name: `briefing3_AI_aging_YYYY-MM-DD.md`.
- Trigger: Wednesday 08:00 China Standard Time, cron `0 8 * * 3`.
- Readers: Yingtian system development team and AI technical leads.
- Positioning: a technical radar for AI and aging science. Each item should help answer whether a technology is relevant to aging assessment, intervention recommendation, biomarkers, clocks, or AI-enabled R&D.
- Search scope: PubMed, arXiv, bioRxiv, medRxiv, AI conference papers, journal articles, model documentation, official technical blogs, company updates, and credible biotech/technology reporting. Search recent one-to-two-week breakthroughs first. If insufficient, add reference content from the past three years in AI drug discovery, biological age, aging clocks, and digital health. Major foundational technology can exceed the time window only when clearly marked as reference content.
- PubMed/search terms: artificial intelligence aging; machine learning biological age; deep learning senescence; AI drug discovery longevity; digital twin aging; aging clock deep learning.
- Theme blocks: AI drug discovery for aging targets; AI aging biomarkers; ML aging clocks; AI health management.
- Screening priority: usefulness for the Yingtian system, decomposed into technical maturity beyond PoC, reproducible result or accessible API, integration compatibility with existing architecture, standard data formats, open-source or accessible model status, and first-mover advantage. Pure theoretical AI research is excluded when short-term application is implausible.
- Summary style: 100-200 Chinese characters and must include four elements: AI method, performance metric such as MAE/AUC/R2 when available, improvement over previous method/product, and potential value for the Yingtian system. Use a visible `启示` field rather than overclaiming direct business outcomes. Keep English technical terms and add Chinese explanation for cross-disciplinary readers.
- Commentary: end the full briefing with a 200-300 Chinese character integrated comment using "trend summary + priority suggestion"; this is unique to Briefing 3.
- Markdown format: use light emoji markers for visual recognition. Item titles use "number + bold description + institution/country". Separate the four technology blocks with `---`; include contact, next issue preview, and archive path.

### Briefing 4: AI Application Landing x Anti-Aging

- File name: `briefing4_ai_apps_YYYY-MM-DD.md`.
- Trigger: Thursday 08:00 China Standard Time, cron `0 8 * * 4`.
- Readers: product teams and business strategy teams.
- Positioning: a product radar asking "can users use this AI anti-aging product today?" It scans the current market, not early research or financing-only signals.
- Search scope: official product pages, release notes, app/store pages, regulatory approvals, help centers, credible product reviews, clinical evidence pages, company pages, and professional product/industry reporting. Search recent one-to-two-week feature, regulatory, and commercial updates first. If insufficient, add representative products from the past three years that are still available and in use. Reference cases must link to official product/regulatory pages, show first release or update date, and state that they are not efficacy validation.
- Theme blocks: AI health assessment products; digital therapeutics; wearable devices plus AI aging monitoring; personalized nutrition AI; longevity clinic AI applications; AI-assisted anti-aging product development.
- Screening priority: product availability today, at least public beta or regulatory approval; China accessibility or cross-border channel availability; user scale above 100,000 where known; direct competitive or collaborative relationship with Infinitus product lines. Concept products and unlaunched startups are excluded.
- Summary style: 100-150 Chinese characters using "product description + key data + competitive/cooperation analysis". State what the product does, how it works, who uses it, include hard numbers such as users, financing, price, or performance indicators when available, then mark whether it is a competitive threat, technical reference, or potential cooperation direction. Add category and headquarters country/region.
- Markdown format: same hierarchy as Briefings 1 and 2. Item titles use "number + product name + core function + country/region". End with a two-to-three-sentence trend summary and implication for Infinitus.

## Search Logic To Replicate

Use the example files to infer what researchers need to know, then update with current sources:

- Academic frontier: PubMed, journal pages, research institute or university pages.
- Industry watch: company releases, ClinicalTrials.gov or CDE registrations, FDA/EFSA/SAMR and other regulator pages, credible industry media.
- AI x Longevity: PubMed, AI conference or journal papers, AI drug discovery company updates, official model or platform documentation.
- AI in Practice: product official pages, regulatory approvals, credible product or industry reporting, clinical evidence when available.

The agent should actively use web search rather than waiting for a pre-written briefing. Search engines or search APIs are acceptable, including Google Search / Google Programmable Search, Bing Web Search, SerpAPI, Tavily, or another company-approved search provider. Use the search engine for discovery only; the published source URL must be the direct article, journal, trial registry, regulatory page, company release, product page, or credible report URL.

Recommended search pattern:

1. Search broad recent queries for each category, such as `senolytic clinical trial aging latest`, `NAD+ precursor clinical trial older adults`, `AI biological age biomarker`, `longevity clinic AI product`, and Chinese equivalents when relevant.
2. Once a candidate is selected, search the exact English title in quotes. For papers, also search title fragments in PubMed, Crossref, DOI.org, Google Scholar, and the journal site. For trials, search the intervention and disease in ClinicalTrials.gov or CDE. For companies and products, search the company newsroom, investor-relations page, product page, and regulator pages.
3. Open the candidate result page, not only the search snippet.
4. Extract the exact title, publication or announcement date, source name, and source URL.
5. Cross-check high-risk claims with at least one stronger source such as PubMed, ClinicalTrials.gov, regulator pages, company investor/news pages, or journal pages.
6. Store only the direct source URL in `sources[].url`; do not store Google/Bing search-result URLs as article links.

The v3 generation logic must be reflected in every run:

- Search first in PubMed, Crossref, DOI.org, journal official sites, ClinicalTrials.gov, CDE/FDA/EFSA/SAMR and other regulators, company newsroom/investor pages, product pages, arXiv/bioRxiv/medRxiv, university/institute pages, and professional industry sources.
- Core academic keywords include `aging`, `senescence`, `longevity`, `healthspan`, `mitochondrial aging`, `telomere`, `epigenetic clock`, `senolytic`, `NAD+`, `caloric restriction`, and `stem cell aging`. Combine them with field terms such as metabolism, inflammation, microbiome, skin aging, immune aging, frailty, sarcopenia, cognitive aging, and clinical trial.
- AI keywords include AI drug discovery, foundation model, multimodal model, machine learning, deep learning, biological age, aging clock, biomarker, target discovery, virtual screening, generative AI, omics, digital health, wearable, diagnostic, decision support, and longevity clinic.
- Candidate screening priority is: direct/openable source; within the 12-month window; strongest fit to one section; relevance to anti-aging, healthspan, nutrition, metabolism, skin, gut, plant actives, NAD+, mitochondrial function, inflammation, or AI-enabled discovery; evidence strength; novelty; value for R&D, product concept, science communication, market education, or business monitoring.
- If a section has too few strong candidates, broaden source types before weakening source quality: use credible journals beyond PubMed/Cell/Nature, preprints with clear provenance, official reports, registries, professional industry media, and product/regulatory pages. Do not use news, Wikipedia, blogs, forums, public accounts, or user-generated content as academic article sources.

Do not force academic content to come only from PubMed, Cell, Nature, or other top journals. Regular peer-reviewed journals, DOI pages, PubMed/PMC, preprint servers, universities, research institutes, government agencies, and international organizations can be used when the source is credible and traceable. For academic article cards, do not use news reports, Wikipedia, personal blogs, forums, social platforms, public accounts, or other user-generated content as the article source.

Do not use Wikipedia or other open-edit encyclopedias as factual sources. Search snippets and social posts can only be discovery leads.

## Operational Generation Logic

The weekly site is a topic-screening product, not a systematic literature review. The goal is to give R&D and strategy readers enough high-quality leads to decide what deserves deeper follow-up. Do not over-filter until only PubMed, Cell, Nature, or other top-journal links remain.

For each section, generate more candidates than the final site needs:

1. Academic Frontier: collect 20-30 candidates, publish 6-12. Accept original papers, review articles, preprints with clear provenance, and official university/institute/government/organization reports. Prefer PubMed/DOI/journal pages when available. Every displayed academic article must be within the past 12 months, have a verified publication or online-publication date, and include a visible source link. News, Wikipedia, blogs, public accounts, forums, and user-generated pages can be discovery leads only; they cannot be the displayed article source.
2. Industry Watch: collect 20-30 candidates, publish 8-12. Accept company press releases, investor relations pages, clinical trial registries, regulator pages, professional media such as FierceBiotech/Endpoints/Modern Retina/NutraIngredients/CosmeticsDesign, and dated market reports. A company homepage is not enough for an event item; use a specific news/product/trial/report page.
3. AI x Longevity: collect 15-25 candidates, publish 6-10. Accept AI conference papers, arXiv/bioRxiv/medRxiv, journal articles, model documentation, company technical blogs, institution news, and credible tech/biotech reporting.
4. AI in Practice: collect 15-25 candidates, publish 6-10. Accept product help pages, product release notes, regulator approvals, credible product reviews, clinical evidence pages, and professional reporting. The source must show the actual product/feature, not only the brand homepage.

Use a two-tier evidence label:

- `A | direct/original source`: article DOI/PubMed/journal page, trial registry, regulator document, company press release, investor release, official product/help page.
- `B | credible secondary source`: named professional media, industry media, university/institute news, dated market report, review article, or expert interview that directly covers the topic.

Both A and B can be published. B-level items must avoid strong causal, clinical, or market-size claims unless those claims are directly supported on the page. If the item is mainly a trend signal, write it as a trend signal.

When an old prototype title cannot be verified, do not keep the title and attach an unrelated source. Instead:

1. search for the closest real article/event;
2. if a real source exists, rewrite the title, summary, date, and source fields around that source;
3. if no real source exists, remove the item from the public set and replace it with another on-theme candidate.

## Review Standard

Every generated item should preserve the example style first, then verify:

- date
- institution or company
- research stage or clinical phase
- sample size and numeric claims
- product availability
- source type
- exact source URL that readers can open
- whether the wording overstates the evidence

Date precision must follow this order:

1. exact date in `YYYY-MM-DD` when the source provides a day;
2. month in `YYYY-MM` when only month is visible;
3. quarter in `YYYY-Q1` / `YYYY-Q2` / `YYYY-Q3` / `YYYY-Q4` when only quarter is visible;
4. year in `YYYY` only when no more specific date is available.

Do not publish placeholder dates such as `按本周检索结果填写`, `待填写`, or `原始日期见来源`. If a source lacks a date, either find a better source or use the least-specific defensible date level.

For Academic Frontier, the date gate is stricter: the publication date must fall within the 12 months before the current generation date. A year-only date is not enough to publish an academic item as a latest article. If a paper page was updated or re-indexed recently but the paper itself is older than 12 months, exclude it from the public latest-article list.

Treat every metadata edit as a linked update. If `sources`, `titleEn`, `sourceName`, `publishedAt`, `displayType`, or `summary` changes, re-check the other fields in the same record. For example, changing a source URL may require updating the title, date, source name, evidence level, and summary language.

If a claim cannot be verified, keep the topic only if it is central to the example logic, but rewrite the claim conservatively and mark it for review instead of silently replacing it with an unrelated article.

Article-summary writing is a hard quality gate, but the structure is different by briefing:

- Academic Frontier: 100-200 Chinese characters, "research finding -> method -> significance".
- Industry Watch: 100-150 Chinese characters, "event -> data -> impact".
- AI x Longevity: 100-200 Chinese characters, including AI method, performance metric, improvement over previous method/product, and Yingtian-system value.
- AI in Practice: 100-150 Chinese characters, "product description + key data + competitive/cooperation analysis".

All summaries are written in Chinese. Keep professional English terms such as `NAD+`, `senolytic`, `epigenetic clock`, `foundation model`, and `ClinicalTrials.gov` in English and add Chinese explanation when needed. Avoid overusing weak speculation such as "可能" and "也许". Use affirmative language for conclusions supported by human clinical data or official company/regulatory disclosures; clearly label animal-only, preclinical, beta-product, or reference-case evidence.

Fully automated publication rule: an item may be published automatically only when every factual claim has a direct, openable source URL. Items with missing direct URLs, unclear dates, unsupported clinical phases, or suspicious numbers must be excluded from the public weekly page or placed in a separate internal review queue.

If the exact direct URL cannot be found for a prototype/sample item, do not show a search-engine URL. Show the English title and the expected source website/database instead, optionally with the Chinese title as a reference translation. This is a fallback display only; it is not sufficient for fully automated publication.

Source quality priority:

1. Exact original article, DOI, PubMed page, NCT trial page, regulator document, company news release, or official product page that directly supports the item.
2. Official organization page that establishes the product/company/platform, only when the exact announcement page cannot be found and the item is clearly marked as not fully verified.
3. Credible media/reporting page with named source and date.
4. Search engine result pages are never acceptable as a displayed source.

The source selected for `sources[].url` should be the best available source, not merely a page where a human can continue searching.

## Data Governance And Dynamic Knowledge Platform

The weekly briefing is a published view, not the only data carrier. The system must first create structured evidence records, then render Markdown, website, Feishu, and dashboard views from those records.

### Source Tiers

- A-level first-party/original evidence: journal article and DOI, PubMed/Crossref metadata, ClinicalTrials.gov/WHO ICTRP/Chinese trial registry, FDA/EMA/NMPA/SAMR/EFSA announcement, regulatory filing, official company release, official product page. Use this tier for factual confirmation, key numbers, clinical/regulatory conclusions, and publication metadata.
- B-level high-credibility independent secondary source: Reuters, Bloomberg, FT, and professional media with editorial review. Use this tier for cross-checking, industry background, and independent perspective.
- C-level discovery lead: search snippets, aggregators, social posts, conference previews, vendor marketing pages, personal accounts, forums, and public accounts. Use only for discovery. An item cannot enter formal content until it is traced back to A/B-level evidence.

### Verification Rules

- Every record must contain at least one accessible A-level source.
- Clinical, regulatory, safety, efficacy, and financing amount claims require double-source verification: A-level original source plus independent A/B source. If only one official source exists, mark `single_source_pending_crosscheck`.
- Paper metadata must verify title, author, journal, date, DOI/PMID, article type, organism/population, sample size, and publication status. Preprints must be labeled `not peer reviewed`.
- Evidence stage must be explicit: in vitro, animal, observational, randomized trial, registry update, regulatory approval, product release, market report, or reference case. Do not turn mechanism signals into human efficacy claims or correlations into causality.
- All numbers must keep unit, denominator, time window, comparator, and source location. The agent must not infer key numbers from charts without context.
- If retrieval fails, retry with exponential backoff, switch to backup official source/database, then publish a data-incomplete warning. Do not use training knowledge or search snippets to invent current facts.

### Record Lifecycle

1. Capture search query, execution time, source URL, access time, response status, raw metadata, and `agent_run_id`.
2. Standardize DOI, PMID, NCT/ChiCTR, company, product, country/region, date, currency, and taxonomy.
3. Deduplicate by DOI, registry ID, announcement ID, canonical URL, and title similarity plus organization plus date.
4. Extract claims and bind each claim to source quote, source location, source URL, and evidence tier.
5. Run rule checks for future dates, number conflicts, missing primary source, wrong evidence stage, retraction/correction, broken link, and cross-week duplicate.
6. Human review high-impact information and all Infinitus/Yingtian implications; store reviewer name, time, and comment.
7. Publish only `verified` records. `pending_verification` and `conflict` records stay in an internal review queue.

### Verification Status

- `verified`: primary source is valid, key fields are complete, claims match evidence. Can publish.
- `single_source`: only one first-party source exists and no independent cross-check yet. Internal publication only, with visible label; high-impact claims are not broadly published by default.
- `pending_verification`: lead exists but primary source or key field is missing. Review queue only.
- `conflict`: sources disagree on date, amount, sample size, or conclusion. Pause publication and keep conflict note.
- `corrected_or_retracted`: source published a correction, retraction, or status change. Update history and notify subscribers.

### Archive Model

- Structured record layer: one paper/event/product per record; claims, evidence, tags, review status, and lifecycle are stored as fields. Controlled updates are allowed with change history.
- Raw evidence layer: API metadata, public webpage snapshot/summary, file hash, and crawl logs. Keep read-only. Do not copy paid or copyright-restricted full text into the database; store legal metadata, necessary short excerpts, and links.
- Publication snapshot layer: each Markdown/PDF/web/Feishu version, publication date, reviewer, template version, and edition ID. Published snapshots are immutable; corrections create a new version.

Minimum fields: `record_id`, `briefing_type`, `title`, `event_date`, `first_seen_at`, `updated_at`, `topic`, `entity`, `product_or_intervention`, `country`, `research_stage`, `tags`, `source_tier`, `source_title`, `publisher`, `canonical_url`, `DOI_PMID_registry_id`, `published_at`, `accessed_at`, `evidence_quote`, `evidence_location`, `content_hash`, `claim`, `summary`, `key_metrics`, `Infinitus_relevance`, `limitations`, `verification_status`, `reviewer`, `reviewed_at`, `risk_level`, `conflict_note`, `template_version`, `agent_run_id`, `edition_id`, `supersedes_id`, `correction_reason`, `retention_class`, and `access_level`.

### Time Window And Evergreen Pool

The four briefings must remain readable every week. Prefer high-quality signals from the last three months. If quantity is insufficient, add items from the current calendar year that still have decision value. If still insufficient, use verified evergreen reference items such as foundational frameworks, key studies, clinical trials, regulatory nodes, or representative products still in use. Evergreen items have no hard year limit, but must remain valid, show original publication/release date, and be clearly labeled `reference content`. Time windows may be relaxed; A-level evidence, evidence stage, link reachability, and verification status may not be relaxed.

### End-To-End Flow

1. Define the issue scope from the last successful run and each briefing's topic lexicon.
2. Run multi-source retrieval through official APIs, site search, and approved web search; log queries and result cursors.
3. Write candidates to staging first, not directly to the public briefing.
4. Standardize and deduplicate unique IDs, entities, dates, stages, and metrics.
5. Verify evidence tier, double-source rules, number consistency, corrections/retractions, and link reachability.
6. Score relevance, signal strength, novelty, translatability, and evidence quality. Evidence quality is a hard gate.
7. Generate summaries only from evidence-bound fields.
8. Route high-risk items and Infinitus/Yingtian implications to human review.
9. Publish structured records, immutable snapshots, Feishu posts, website views, and archive indexes.
10. Monitor coverage, failed sources, verification pass rate, human edit rate, reading data, and reader feedback.

### Quality Metrics

- Primary-source coverage: 100% of formal items have A-level source.
- High-impact double-source rate: 100% for clinical, regulatory, efficacy, safety, and major transaction claims.
- Traceability: 100% of factual sentences trace back to claim and evidence location.
- On-time release: at least 95% when external sources are healthy.
- Correction response: fix confirmed factual errors and notify subscribers within one business day.
- Duplicate rate: cross-week repeats without new information below 5%.
- Human substantive edit rate: track continuously; reduction must not sacrifice verification quality.

### Pre-Publication Checklist

- Does every item have accessible primary source, publication/event date, and access date?
- Are high-impact claims double-checked and are numbers consistent with the original source?
- Is evidence stage clearly separated: in vitro, animal, observational, clinical trial, regulatory approval, product release, or reference case?
- Are there any unsupported facts from search snippets, training knowledge, or inaccessible pages? Delete or move them to review.
- Has the item been deduplicated against history and does it state the true new development?
- Are `agent_run_id`, template version, reviewer, and publication snapshot saved?
- Are restricted, copyrighted, or commercially sensitive items assigned the correct access level?
- Do website, Feishu notification, and dashboard links point to the same structured record rather than copied independent content?

## Title-Source Consistency Gate

Every public item must pass a title-source consistency check before publication:

1. If `sources[].url` is a PubMed, DOI, journal, registry, regulator, company, or product URL, opening that URL must show the same article/event/product title or an unambiguous official page for that exact item.
2. If the page does not contain the exact English title, the validator must confirm a high-confidence match through DOI, PMID, NCT number, company announcement title, regulator document title, or product page name.
3. A reader must be able to copy the displayed English title and find the same item on the displayed source website/database. If that title cannot be found, do not label it as an original title.
4. `citation_to_verify`, homepage-only links, search-result pages, and broad database landing pages are not publishable public sources.
5. Items that fail this gate must be excluded from the public site or moved to an internal review queue with a visible "待核验" status.

## Website Record Fields

Each website item should be created directly with article-level metadata:

- `publishedAt`: the article, trial, product, regulatory, or company-announcement date.
- `sourceName`: the journal, trial registry, regulator, company, institution, product site, or credible media outlet.
- `displayType`: article type such as academic paper, clinical trial update, funding/M&A, regulatory policy, product release, AI model/tool, or market trend.
- `sources`: one or more direct URLs to the original article, trial registration, regulatory page, company release, product page, or credible report.
- `titleEn`: required fallback field when the exact direct URL is not yet found; use the original English title if available, otherwise a precise English search title.
- `summary`: 100-200 Chinese characters using the finding -> method -> significance structure.
- `keyPoints`: three source-backed bullets that include exact dates, stage/status, key data, or why the item was selected.
- `insight`: a concise reason for inclusion. Do not claim what the item will do for Infinitus or any internal system unless the source directly supports that conclusion.

Never display the generated briefing file name as `sourceName`, `publication`, `出处`, or source link.

Never display search engine result pages as source links. If only a search result is available, the item is not ready for automatic publication.
