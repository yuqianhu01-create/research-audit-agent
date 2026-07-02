# Anti-Aging Research + Audit Agent Starter

This is a proof-of-concept agent workflow for anti-aging weekly briefing generation.

It now has three small agents:

1. Research Agent: collects candidates from multiple sources.
2. Audit Agent: validates source quality, date, duplicates, link health, paywall/dead-page signals, and basic topic fit.
3. Publishing Agent: converts passed or reviewable records into website candidate JSON.

The goal is to prove the pipeline before designing the enterprise solution.

## File Structure

```text
instructions/
  general_instructions.md
  briefing_rules.md
data/
  published_registry.json
  candidates.json
  audit_report.json
  website_candidates.json
scripts/
  research_agent.py
  audit_agent.py
  publish_agent.py
.github/workflows/
  weekly_agent.yml
```

## Sources Covered

Academic:

- PubMed
- Crossref

Industry:

- ClinicalTrials.gov
- official company/regulatory watchlist

AI x Longevity:

- PubMed
- Crossref
- arXiv

AI in Practice:

- ClinicalTrials.gov
- arXiv
- official product/company watchlist

## Audit Checks

The Audit Agent checks:

- URL is accessible
- URL is not from disallowed user-generated sources
- source type is direct and publishable
- page does not look dead, discontinued, 404-like, or paywalled
- page text roughly matches title/source topic
- publication date exists where required
- future dates are blocked
- prior-issue duplicates are blocked via `published_registry.json`
- low-topic-relevance candidates are blocked

Official product/company watchlist pages without exact article dates are marked `needs_review`, not automatically published.

## Automatic GitHub Workflow

The workflow file is:

```text
.github/workflows/weekly_agent.yml
```

It has two trigger modes:

1. Manual test: click `Actions` -> `Weekly Research Audit Agent` -> `Run workflow`.
2. Automatic schedule: runs every Monday 09:00 Beijing time.

No extra tool is needed to start the automatic workflow. GitHub Actions starts it from the `schedule` cron.

## Outputs

After each run, download the `agent-output` artifact:

```text
data/candidates.json
data/audit_report.json
data/website_candidates.json
data/published_registry.json
```

Use `audit_report.json` for review.
Use `website_candidates.json` as the handoff to Feishu Bitable or the anti-aging briefing website.

## Local Commands

Run all four sections:

```bash
python scripts/research_agent.py --section all --limit 8
python scripts/audit_agent.py --input data/candidates.json
python scripts/publish_agent.py --input data/audit_report.json --issue next --include-needs-review
```

Run one section:

```bash
python scripts/research_agent.py --section academic --limit 8
```

## Enterprise Version Direction

Recommended production flow:

```text
Research Agent
  -> Audit Agent
  -> Feishu Bitable review table
  -> Human approval
  -> Publishing Agent
  -> anti-aging briefing website + Feishu post
```

The starter does not yet write directly into Feishu or deploy the public site. That should be added after the audit quality is acceptable.
