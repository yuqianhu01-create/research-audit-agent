import html
import json
from collections import defaultdict
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


def render_record(record, index):
    source = (record.get("sources") or [{}])[0]
    original = record.get("originalAbstract") or "暂无原文摘要。"
    return f"""
    <article class="story">
      <div class="story-number">{index:02d}</div>
      <div class="meta-grid" aria-label="文章信息">
        <div><span>日期</span><strong>{esc(record.get('publishedAt'))}</strong></div>
        <div><span>出处</span><strong>{esc(record.get('sourceName'))}</strong></div>
        <div><span>类型</span><strong>{esc(record.get('displayType'))}</strong></div>
        <div><span>领域</span><strong>{esc(record.get('group'))}</strong></div>
      </div>
      <h2>{esc(record.get('title'))}</h2>
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

    html_text = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Infinitus Anti-aging Weekly Briefing</title>
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
    body {{
      margin:0;
      background:var(--paper);
      color:var(--ink);
      font-family:"Noto Sans SC","Microsoft YaHei",Arial,sans-serif;
    }}
    .shell {{ max-width:1280px; margin:0 auto; padding:0 30px 90px; }}
    header {{ padding:52px 0 26px; border-bottom:1px solid var(--line); }}
    .eyebrow {{ color:var(--green); font-size:13px; font-weight:900; letter-spacing:.16em; text-transform:uppercase; }}
    header h1 {{
      margin:14px 0 10px;
      font-family:Georgia,"Noto Serif SC",serif;
      font-size:clamp(42px,7vw,92px);
      line-height:1.02;
      letter-spacing:0;
    }}
    .subtitle {{ max-width:760px; color:var(--muted); font-size:18px; line-height:1.75; }}
    .topbar {{
      position:sticky;
      top:0;
      z-index:5;
      margin:0 -30px;
      padding:0 30px;
      background:rgba(251,250,244,.94);
      border-bottom:1px solid var(--line);
      backdrop-filter:blur(10px);
    }}
    .nav-row {{ display:flex; align-items:center; gap:28px; overflow-x:auto; min-height:70px; }}
    .nav-tab {{
      flex:0 0 auto;
      border:0;
      border-bottom:5px solid transparent;
      background:transparent;
      color:var(--muted);
      padding:22px 2px 18px;
      font-weight:900;
      font-size:16px;
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
      padding:9px 15px;
      font-weight:900;
      font-size:14px;
    }}
    .archive-note {{
      display:none;
      margin:24px 0 0;
      padding:18px 20px;
      background:var(--soft);
      border-left:6px solid var(--green);
      color:#31443a;
      line-height:1.7;
    }}
    .briefing-section {{ display:none; padding-top:92px; }}
    .briefing-section.active {{ display:block; }}
    .section-title {{
      display:inline-flex;
      align-items:center;
      min-height:74px;
      margin:0 0 64px;
      padding:12px 34px 18px;
      background:var(--ink);
      color:white;
      border-radius:8px;
      box-shadow:inset 0 -8px 0 var(--green);
      font-family:Georgia,"Noto Serif SC",serif;
      font-size:clamp(34px,5vw,58px);
      font-weight:900;
      line-height:1.05;
      letter-spacing:0;
    }}
    .story {{ padding:0 0 84px; margin-bottom:78px; border-bottom:2px solid var(--ink); }}
    .story-number {{
      margin-bottom:18px;
      color:var(--green);
      font-family:Georgia,serif;
      font-size:28px;
      font-weight:900;
    }}
    .meta-grid {{
      display:grid;
      grid-template-columns:repeat(4,minmax(0,1fr));
      border-top:2px solid var(--ink);
      border-bottom:1px solid var(--line);
    }}
    .meta-grid div {{
      min-height:86px;
      padding:20px 20px 18px 0;
      border-right:1px solid var(--line);
    }}
    .meta-grid div:last-child {{ border-right:0; }}
    .meta-grid span {{
      display:block;
      margin-bottom:7px;
      color:var(--muted);
      font-size:13px;
      font-weight:900;
    }}
    .meta-grid strong {{
      display:block;
      font-size:20px;
      line-height:1.35;
      overflow-wrap:anywhere;
    }}
    h2 {{
      max-width:1120px;
      margin:56px 0 34px;
      font-family:Georgia,"Noto Serif SC",serif;
      font-size:clamp(40px,6vw,78px);
      line-height:1.15;
      letter-spacing:0;
    }}
    .summary-cn {{
      max-width:980px;
      margin:0 0 52px;
      color:#2f4339;
      font-size:24px;
      line-height:2.05;
    }}
    .insight-row {{
      display:grid;
      grid-template-columns:150px minmax(0,1fr);
      gap:26px;
      align-items:start;
      max-width:1030px;
      padding:24px 0;
      border-top:1px solid var(--line);
      border-bottom:1px solid var(--line);
    }}
    .insight-row b {{
      color:var(--green);
      font-size:22px;
      line-height:1.6;
    }}
    .insight-row span {{
      color:#26392f;
      font-size:22px;
      line-height:1.85;
    }}
    .story-actions {{ display:flex; flex-wrap:wrap; gap:14px; margin-top:34px; }}
    .source-link, .ghost-button {{
      display:inline-flex;
      align-items:center;
      justify-content:center;
      min-height:48px;
      border-radius:999px;
      padding:11px 20px;
      font-size:17px;
      font-weight:900;
      text-decoration:none;
      cursor:pointer;
    }}
    .source-link {{ background:var(--green); color:white; border:1px solid var(--green); }}
    .ghost-button {{ background:transparent; color:var(--green); border:1px solid var(--green); }}
    .original-abstract {{
      max-width:980px;
      margin:24px 0 0;
      padding:22px 24px;
      background:var(--white);
      border:1px solid var(--line);
      color:#33443c;
      font-size:17px;
      line-height:1.85;
    }}
    .empty-state {{ color:var(--muted); font-size:22px; line-height:1.8; }}
    @media (max-width:760px) {{
      .shell {{ padding:0 18px 70px; }}
      .topbar {{ margin:0 -18px; padding:0 18px; }}
      .meta-grid {{ grid-template-columns:1fr 1fr; }}
      .meta-grid div {{ min-height:76px; }}
      .summary-cn, .insight-row span {{ font-size:19px; line-height:1.85; }}
      .insight-row {{ grid-template-columns:1fr; gap:6px; }}
      .archive-link {{ margin-left:0; }}
    }}
  </style>
</head>
<body>
  <div class="shell">
    <header>
      <div class="eyebrow">Weekly Briefing Candidate Site</div>
      <h1>Infinitus Anti-aging Briefing</h1>
      <p class="subtitle">本页展示本期自动检索后的候选内容，保留日期、来源、类型、领域、摘要、机会点和原始链接，方便快速浏览与后续人工复核。</p>
      <div class="archive-note" id="archiveNote">过往周报入口会连接到历史 edition 快照；当前 starter 先生成本期候选页，后续可由 publishing agent 自动写入 editions 并部署为固定链接。</div>
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
