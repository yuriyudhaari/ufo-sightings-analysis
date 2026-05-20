# Methodology

## Data

National UFO Reporting Center (NUFORC) "scrubbed" dataset. 80,332 reports, 1906–2014. Each row is one user-submitted report with timestamp, location, free-text description, self-categorized shape, and duration.

## Cleaning

**Dropped row:** one row had a corrupted latitude value (`33q.200088`). Dropped rather than imputed.

**Datetime parsing:** `datetime` and `date posted` columns parsed cleanly. Reports before 1998 are retrospective; the NUFORC web form did not exist before then.

**HTML entity decoding:** the comments field contained `&#44;` (comma), `&amp;` (ampersand), and similar entities. Decoded with `html.unescape` plus regex for numeric character references.

**Duration cleaning:** reported durations span 0.001 seconds to 97.8 million seconds (3+ years). Kept all values, added a `duration_reliable` flag for the range 5 seconds to 2 hours. 91.1% of reports have reliable durations.

**Shape bucketing:** 29 source shape values reduced to 10 families based on visual similarity:

| Family | Source values |
|---|---|
| Light/Orb | light, flash, flare |
| Disk | disk, oval, dome |
| Triangle | triangle, chevron, delta, pyramid |
| Sphere/Circle | sphere, circle, round, egg, crescent |
| Fireball | fireball, teardrop |
| Cigar/Cylinder | cigar, cylinder |
| Rectangle | rectangle, diamond, cross, cone, hexagon |
| Formation | formation |
| Changing | changing, changed |
| Other/Unknown | other, unknown |

**Country inference:** 9,670 reports (12%) had missing country labels. Used rectangular bounding boxes for US (CONUS + Alaska + Hawaii), Canada, UK, Australia, and Germany to assign a country code from coordinates. Anything outside those boxes is labeled "other" (~3% of total).

Bounding boxes are coarse — a report just south of the US-Mexico border could be misassigned. Acceptable trade-off for filling 12% of the dataset.

**NUFORC era flag:** binary `era` field marks pre-1998 vs 1998+. Used to caveat aggregate findings.

## Biases

**Reporting platform bias.** NUFORC's web form launched in 1998. Pre-web reports required mail or phone; post-web could be submitted online in minutes. Pre-1998 averaged 174 reports/year. Post-1998 averaged ~4,000/year. The 23x jump is a function of platform availability, not phenomenon frequency.

**Language and reach bias.** NUFORC is English-language and US-based. 88.8% of reports are from the US, 4% Canada, 3% UK, 1% Australia. The dataset reflects Anglophone-internet reporting, not global UFO activity.

**Recall bias.** Pre-1998 reports were often submitted years or decades after the alleged event. Memory degrades and reshapes to fit known UFO tropes.

**Self-categorization bias.** "Shape" is whatever the reporter wrote down. Cultural framing affects what people pick — the growth of "Triangle" reports post-1990 may partly reflect the popularization of the "black triangle" trope, not a real change in observed objects.

## Analytical choices

**Per-capita normalization.** US state comparisons use 2010 Census populations. Raw counts track population; per-capita reveals real geographic patterns. 2010 is a snapshot — using a different census year would shift rates slightly but not change rankings.

**LDA topic modeling.** Sample balanced across years (max 500 reports per year) to prevent the 2000s from dominating the topic model. 8 topics chosen after inspection at 6, 8, 10, 12 — 8 produced the most interpretable themes. Custom stopword list removes UFO-corpus terms ("ufo", "object", "sighting", "witness") that otherwise dominate every topic.

## Limitations

The data cannot answer:
- Whether UFOs are real
- Whether actual sighting rates changed over time (only reporting rates did)
- Whether geographic differences reflect real frequency or reporting culture
- Whether shape evolution reflects different objects or different cultural framing
- Whether individual reports describe real anomalies, misidentifications, or hoaxes
