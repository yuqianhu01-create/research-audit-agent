# Briefing Rules for Demo Agent

## Four Sections

1. Academic Frontier
   - Purpose: basic research, mechanisms, biomarkers, intervention studies, scientific reviews.
   - Sources: PubMed, DOI, journal pages, preprints, universities, research institutes, official scientific reports.
   - Demo status: implemented first.

2. Industry Watch
   - Purpose: commercialization, funding, partnerships, clinical pipeline progress, regulatory milestones, market movement.
   - Sources: company official releases, regulator pages, clinical trial registries, credible professional industry media.
   - Demo status: not implemented in first version.

3. AI x Longevity
   - Purpose: AI methods applied to aging science.
   - Sources: PubMed, arXiv, bioRxiv, medRxiv, journal pages, research institution pages.
   - Demo status: not implemented in first version.

4. AI in Practice
   - Purpose: deployable products, services, tools, diagnostics, wearables, clinical or consumer applications.
   - Sources: product official pages, regulator pages, clinical trial pages, credible professional sources.
   - Demo status: not implemented in first version.

## Demo Search Terms

For `academic`:

```text
(aging OR longevity OR healthspan OR senescence OR "mitochondrial aging" OR "epigenetic clock" OR senolytic OR NAD OR "stem cell aging")
```

## Hard Rules

- Every candidate must have a title.
- Every candidate must have a source URL.
- Every candidate must have a publication date.
- Do not use Wikipedia, blogs, forums, social media, or user-generated content as formal sources.
- Do not publish an item if the link is broken.
- Do not repeat items already present in `data/published_registry.json`.

## Audit Checks

The Audit Agent checks:

1. link opens;
2. publication date exists;
3. date is within the configured window;
4. title/source fields are not empty;
5. candidate is not duplicated in the registry.

## Output Status

- `passed`: can enter human review.
- `needs_review`: not enough metadata or weak source.
- `failed`: broken link, duplicate, missing date, or disallowed source.
