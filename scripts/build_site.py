import html
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
SITE_DIR = ROOT / "site"

SECTION_LABELS = {
    "academic": "01 学术前沿",
    "industry": "02 产业动态",
    "ai-aging": "03 AI × 抗衰老",
    "ai-apps": "04 AI 应用落地",
}


def esc(value):
    return html.escape(str(value or ""))


def generated_date(package):
    value = package.get("generatedAt", "")
    if value:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).date().isoformat()
        except ValueError:
            pass
    return datetime.now().date().isoformat()


def issue_label(package):
    issue = str(package.get("issue") or "候选").strip()
    if issue.isdigit():
        return f"第 {issue} 期"
    if issue.lower() in {"next", "local-test"}:
        return "新一期候选"
    return f"{issue} 期"


def render_record(record, index):
    source = (record.get("sources") or [{}])[0]
    original = record.get("originalAbstract") or "暂无原文摘要。"
    title_cn = record.get("titleCn") or record.get("title")
    title_en = record.get("title")
    title_en_html = ""
    if title_en and title_en != title_cn:
        title_en_html = f'<p class="title-en">{esc(title_en)}</p>'
    return f"""
    <article class="story">
      <div class="story-number">{index:02d}</div>
      <div class="meta-grid" aria-label="文章信息">
        <div><span>日期</span><strong>{esc(record.get('publishedAt'))}</strong></div>
        <div><span>出处</span><strong>{esc(record.get('sourceName'))}</strong></div>
        <div><span>类型</span><strong>{esc(record.get('displayType'))}</strong></div>
        <div><span>领域</span><strong>{esc(record.get('group'))}</strong></div>
      </div>
      <h2>{esc(title_cn)}</h2>
      {title_en_html}
      <p class="summary-cn">{esc(record.get('summaryDraft'))}</p>
      <div class="insight-row">
        <b>机会点</b>
        <span>{esc(record.get('opportunityDraft'))}</span>
      </div>
      <div class="story-actions">
        <a class="source-link" href="{esc(source.get('url'))}" target="_blank" rel="noopener noreferrer">打开原始来源</a>
        <button class="ghost-button" type="button" data-toggle-original>查看原文摘要</button>
      </div>
      <p class="original-abstract" hidden>{esc(original)}</p>
    </article>
    """


def render_section(section, records):
    stories = "\n".join(render_record(record, index + 1) for index, record in enumerate(records))
    if not stories:
        stories = """
        <div class="empty-state">
          <p>本轮候选不足，已进入补检队列。</p>
        </div>
        """
    return f"""
    <section class="briefing-section" id="section-{section}" data-section="{section}">
      <div class="section-title">{esc(SECTION_LABELS[section])}</div>
      {stories}
      <button class="back-top" type="button" data-back-top>回到顶部</button>
    </section>
    """


def main():
    package = json.loads((DATA_DIR / "website_candidates.json").read_text(encoding="utf-8"))
    grouped = defaultdict(list)
    for record in package.get("records", []):
        grouped[record.get("channel", "academic")].append(record)

    sections_html = "\n".join(render_section(section, grouped.get(section, [])) for section in SECTION_LABELS)
    nav_html = "\n".join(
        f'<button class="nav-tab" type="button" data-target="{esc(section)}">{esc(label)}</button>'
        for section, label in SECTION_LABELS.items()
    )
    eyebrow = f"{issue_label(package)} · 生成日期 {generated_date(package)}"

    html_text = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Infinitus Anti-aging Weekly Briefings</title>
  <style>
    :root {{
      --paper:#fbfaf4;
      --ink:#10231a;
      --green:#287355;
      --soft:#eaf2e8;
      --muted:#637168;
      --line:#d8d4c8;
      --white:#fffdf7;
    }}
    * {{ box-sizing:border-box; }}
    html {{ scroll-behavior:smooth; }}
    body {{
      margin:0;
      background:var(--paper);
      color:var(--ink);
      font-family:"Noto Sans SC","Microsoft YaHei",Arial,sans-serif;
    }}
    .shell {{ max-width:1180px; margin:0 auto; padding:0 28px 76px; }}
    header {{ padding:34px 0 20px; border-bottom:1px solid var(--line); }}
    .eyebrow {{ color:var(--green); font-size:13px; font-weight:900; letter-spacing:.12em; text-transform:uppercase; }}
    header h1 {{
      margin:12px 0 8px;
      font-family:Georgia,"Noto Serif SC",serif;
      font-size:clamp(34px,5vw,58px);
      line-height:1.08;
      letter-spacing:0;
    }}
    header h1 span {{ display:block; }}
    header h1 .cn {{ font-family:"Noto Serif SC","Microsoft YaHei",serif; }}
    header h1 .en {{ font-size:.72em; margin-top:8px; }}
    .subtitle {{ max-width:780px; color:var(--muted); font-size:15px; line-height:1.7; }}
    .topbar {{
      position:sticky;
      top:0;
      z-index:5;
      margin:0 -28px;
      padding:0 28px;
      background:rgba(251,250,244,.95);
      border-bottom:1px solid var(--line);
      backdrop-filter:blur(10px);
    }}
    .nav-row {{ display:flex; align-items:center; gap:28px; overflow-x:auto; min-height:58px; }}
    .nav-tab {{
      flex:0 0 auto;
      border:0;
      border-bottom:4px solid transparent;
      background:transparent;
      color:var(--muted);
      padding:17px 0 14px;
      font-weight:900;
      font-size:15px;
      cursor:pointer;
      letter-spacing:0;
    }}
    .nav-tab.active {{ color:var(--ink); border-color:var(--green); }}
    .archive-link {{
      margin-left:auto;
      white-space:nowrap;
      border:1px solid var(--line);
      border-radius:999px;
      background:var(--white);
      color:var(--ink);
      padding:8px 14px;
      font-weight:900;
      font-size:14px;
    }}
    .archive-note {{
      display:none;
      margin:18px 0 0;
      padding:14px 16px;
      background:var(--soft);
      border-left:5px solid var(--green);
      color:#31443a;
      font-size:14px;
      line-height:1.7;
    }}
    .briefing-section {{ display:none; padding-top:58px; }}
    .briefing-section.active {{ display:block; }}
    .section-title {{
      display:inline-flex;
      align-items:center;
      min-height:58px;
      margin:0 0 42px;
      padding:10px 26px 14px;
      background:var(--ink);
      color:white;
      border-radius:8px;
      box-shadow:inset 0 -7px 0 var(--green);
      font-family:Georgia,"Noto Serif SC",serif;
      font-size:clamp(28px,4vw,44px);
      font-weight:900;
      line-height:1.05;
      letter-spacing:0;
    }}
    .story {{ padding:0 0 54px; margin-bottom:54px; border-bottom:2px solid var(--ink); }}
    .story-number {{
      margin-bottom:14px;
      color:var(--green);
      font-family:Georgia,serif;
      font-size:24px;
      font-weight:900;
    }}
    .meta-grid {{
      display:grid;
      grid-template-columns:repeat(4,minmax(0,1fr));
      border-top:2px solid var(--ink);
      border-bottom:1px solid var(--line);
    }}
    .meta-grid div {{
      min-height:70px;
      padding:14px 16px 12px 0;
      border-right:1px solid var(--line);
    }}
    .meta-grid div:last-child {{ border-right:0; }}
    .meta-grid span {{
      display:block;
      margin-bottom:5px;
      color:var(--muted);
      font-size:12px;
      font-weight:900;
    }}
    .meta-grid strong {{
      display:block;
      font-size:17px;
      line-height:1.32;
      overflow-wrap:anywhere;
    }}
    h2 {{
      max-width:960px;
      margin:34px 0 10px;
      font-family:Georgia,"Noto Serif SC",serif;
      font-size:clamp(30px,4.2vw,46px);
      line-height:1.22;
      letter-spacing:0;
    }}
    .title-en {{
      max-width:880px;
      margin:0 0 22px;
      color:var(--muted);
      font-size:15px;
      line-height:1.55;
    }}
    .summary-cn {{
      max-width:900px;
      margin:0 0 30px;
      color:#2f4339;
      font-size:18px;
      line-height:1.85;
    }}
    .insight-row {{
      display:grid;
      grid-template-columns:108px minmax(0,1fr);
      gap:20px;
      align-items:start;
      max-width:930px;
      padding:16px 0;
      border-top:1px solid var(--line);
      border-bottom:1px solid var(--line);
    }}
    .insight-row b {{
      color:var(--green);
      font-size:18px;
      line-height:1.6;
    }}
    .insight-row span {{
      color:#26392f;
      font-size:18px;
      line-height:1.75;
    }}
    .story-actions {{ display:flex; flex-wrap:wrap; gap:12px; margin-top:24px; }}
    .source-link, .ghost-button, .back-top {{
      display:inline-flex;
      align-items:center;
      justify-content:center;
      min-height:42px;
      border-radius:999px;
      padding:9px 17px;
      font-size:15px;
      font-weight:900;
      text-decoration:none;
      cursor:pointer;
    }}
    .source-link {{ background:var(--green); color:white; border:1px solid var(--green); }}
    .ghost-button, .back-top {{ background:transparent; color:var(--green); border:1px solid var(--green); }}
    .back-top {{ margin:2px 0 0; }}
    .original-abstract {{
      max-width:900px;
      margin:20px 0 0;
      padding:18px 20px;
      background:var(--white);
      border:1px solid var(--line);
      color:#33443c;
      font-size:15px;
      line-height:1.75;
    }}
    .empty-state {{ color:var(--muted); font-size:18px; line-height:1.8; }}
    @media (max-width:760px) {{
      .shell {{ padding:0 18px 60px; }}
      .topbar {{ margin:0 -18px; padding:0 18px; }}
      .meta-grid {{ grid-template-columns:1fr 1fr; }}
      .meta-grid div {{ min-height:68px; }}
      .summary-cn, .insight-row span {{ font-size:16px; line-height:1.75; }}
      .insight-row {{ grid-template-columns:1fr; gap:4px; }}
      .archive-link {{ margin-left:0; }}
    }}
  </style>
</head>
<body>
  <div class="shell" id="top">
    <header>
      <div class="eyebrow">{esc(eyebrow)}</div>
      <h1><span class="cn">无限极抗衰老周报</span><span class="en">Infinitus Anti-aging Weekly Briefings</span></h1>
      <p class="subtitle">本页汇总本期经自动检索、来源核验与去重后的抗衰老信息，保留发布日期、出处、类型、领域、原始链接与可转化机会点，便于团队快速阅读与追溯。</p>
      <div class="archive-note" id="archiveNote">过往周报入口将连接到历史 edition 快照；后续 publishing agent 会按期写入 editions，并部署为可分享的固定链接。</div>
    </header>
    <div class="topbar">
      <nav class="nav-row" aria-label="简报板块">
        {nav_html}
        <button class="archive-link" type="button" id="archiveButton">过往周报</button>
      </nav>
    </div>
    <main>
      {sections_html}
    </main>
  </div>
  <script>
    const tabs = [...document.querySelectorAll('.nav-tab')];
    const sections = [...document.querySelectorAll('.briefing-section')];
    function showSection(name) {{
      const target = name || 'academic';
      tabs.forEach(tab => tab.classList.toggle('active', tab.dataset.target === target));
      sections.forEach(section => section.classList.toggle('active', section.dataset.section === target));
      if (location.hash !== '#section=' + target) location.hash = 'section=' + target;
      window.scrollTo({{ top: 0, behavior: 'smooth' }});
    }}
    tabs.forEach(tab => tab.addEventListener('click', () => showSection(tab.dataset.target)));
    document.querySelectorAll('[data-toggle-original]').forEach(button => {{
      button.addEventListener('click', () => {{
        const story = button.closest('.story');
        const original = story.querySelector('.original-abstract');
        const hidden = original.hasAttribute('hidden');
        if (hidden) {{
          original.removeAttribute('hidden');
          button.textContent = '收起原文摘要';
        }} else {{
          original.setAttribute('hidden', '');
          button.textContent = '查看原文摘要';
        }}
      }});
    }});
    document.querySelectorAll('[data-back-top]').forEach(button => {{
      button.addEventListener('click', () => window.scrollTo({{ top: 0, behavior: 'smooth' }}));
    }});
    document.getElementById('archiveButton').addEventListener('click', () => {{
      const note = document.getElementById('archiveNote');
      note.style.display = note.style.display === 'block' ? 'none' : 'block';
    }});
    const match = location.hash.match(/section=([^&]+)/);
    showSection(match ? match[1] : 'academic');
  </script>
</body>
</html>"""

    SITE_DIR.mkdir(parents=True, exist_ok=True)
    (SITE_DIR / "index.html").write_text(html_text, encoding="utf-8")
    print(f"Built site preview at {SITE_DIR / 'index.html'}")


if __name__ == "__main__":
    main()
