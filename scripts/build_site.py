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


def render_record(record):
    raw = record.get("rawCandidate", {})
    source = (record.get("sources") or [{}])[0]
    return f"""
    <article class="story">
      <div class="meta">
        <span><b>日期</b>{esc(record.get('publishedAt'))}</span>
        <span><b>出处</b>{esc(record.get('sourceName'))}</span>
        <span><b>类型</b>{esc(record.get('displayType'))}</span>
        <span><b>状态</b>{esc(record.get('auditStatus'))}</span>
      </div>
      <h2>{esc(record.get('title'))}</h2>
      <p>{esc(raw.get('abstract') or raw.get('why_candidate') or '待人工补写中文摘要。')}</p>
      <div class="opportunity"><b>机会点</b><span>待人工根据原文补写：产品开发、研发指标、内容教育或市场观察可从该条提炼什么启发。</span></div>
      <a class="source" href="{esc(source.get('url'))}" target="_blank" rel="noopener noreferrer">打开原始来源</a>
    </article>
    """


def main():
    package = json.loads((DATA_DIR / "website_candidates.json").read_text(encoding="utf-8"))
    grouped = defaultdict(list)
    for record in package.get("records", []):
        grouped[record.get("channel", "academic")].append(record)

    sections = []
    for section, label in SECTION_LABELS.items():
        records = grouped.get(section, [])
        stories = "\n".join(render_record(record) for record in records)
        sections.append(f"""
        <section>
          <h1>{label}</h1>
          {stories or '<p class="empty">本轮未达到发布门槛。</p>'}
        </section>
        """)

    html_text = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Anti-aging Weekly Briefing Candidate Site</title>
  <style>
    :root {{ --paper:#faf8f0; --ink:#12251c; --muted:#5c6b63; --line:#d5d2c8; --green:#286b50; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:var(--paper); color:var(--ink); font-family:"Noto Sans SC", Arial, sans-serif; }}
    header {{ padding:48px 6vw 30px; border-bottom:1px solid var(--line); }}
    header small {{ color:var(--green); font-weight:900; letter-spacing:.14em; }}
    header h1 {{ margin:10px 0 0; font-family:Georgia, serif; font-size:clamp(38px,6vw,76px); line-height:1.05; }}
    main {{ max-width:1180px; margin:0 auto; padding:34px 24px 80px; }}
    section {{ margin:54px 0 72px; }}
    section>h1 {{ display:inline-block; margin:0 0 28px; padding:10px 16px 13px; color:#fff; background:var(--ink); border-radius:8px; box-shadow:inset 0 -5px 0 var(--green); font-size:30px; }}
    .story {{ padding:34px 0 48px; border-top:1px solid var(--line); }}
    .meta {{ display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); border-top:1px solid var(--ink); border-bottom:1px solid var(--line); }}
    .meta span {{ padding:12px 12px 14px 0; border-right:1px solid var(--line); font-weight:900; overflow-wrap:anywhere; }}
    .meta span:last-child {{ border-right:0; }}
    .meta b {{ display:block; margin-bottom:5px; color:var(--muted); font-size:11px; }}
    h2 {{ max-width:980px; margin:30px 0 18px; font-family:Georgia, "Noto Serif SC", serif; font-size:clamp(28px,4vw,52px); line-height:1.22; }}
    p {{ max-width:850px; color:#304038; font-size:18px; line-height:1.9; }}
    .opportunity {{ display:grid; grid-template-columns:90px 1fr; gap:16px; max-width:900px; margin:26px 0; padding:16px 0; border-top:1px solid var(--line); border-bottom:1px solid var(--line); }}
    .opportunity b {{ color:var(--green); }}
    .opportunity span {{ line-height:1.8; color:#304038; }}
    .source {{ display:inline-flex; padding:10px 16px; border-radius:999px; background:var(--green); color:#fff; text-decoration:none; font-weight:900; }}
    .empty {{ color:var(--muted); }}
    @media (max-width:720px) {{ .meta {{ grid-template-columns:repeat(2,1fr); }} .opportunity {{ grid-template-columns:1fr; }} }}
  </style>
</head>
<body>
  <header>
    <small>NEXT ISSUE CANDIDATES</small>
    <h1>Anti-aging Weekly Briefing</h1>
  </header>
  <main>
    {''.join(sections)}
  </main>
</body>
</html>"""

    SITE_DIR.mkdir(parents=True, exist_ok=True)
    (SITE_DIR / "index.html").write_text(html_text, encoding="utf-8")
    print(f"Built site preview at {SITE_DIR / 'index.html'}")


if __name__ == "__main__":
    main()
