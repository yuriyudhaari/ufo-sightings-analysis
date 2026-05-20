# UFO Sightings Analysis

NUFORC sighting reports, 1906–2014. Python pipeline for cleaning, geographic analysis, and LDA topic modeling on 80,332 reports. Power BI dashboard for the interactive layer.

## Findings

1. The 1998 NUFORC web form launch is the largest variable in the dataset. Pre-1998 reports averaged 174/year; post-1998 averaged ~4,000/year. The 23x increase is a reporting platform effect, not a UFO surge.

2. Sightings peak at 9–10 PM, with a Friday/Saturday bias. People file reports when they are outside in the dark.

3. Pacific Northwest dominates per-capita rates. Washington: 63 reports per 100k residents. Louisiana: 13. The top of the list is PNW + Mountain West + Northern New England; the bottom is the Deep South.

4. The "disk era" is over. Disk/saucer reports peaked at ~40% of all shapes in the 1950s–70s and are now ~11%. Light/Orb is the modern dominant shape at 24%.

5. TF-IDF analysis of Light/Orb reports surfaces "iss" and "hbccufo" as distinctive terms. A meaningful share of modern "light" reports are likely International Space Station passes.

6. LDA topic modeling identifies an "orange triangle formation" topic that rises sharply post-1990, consistent with the proliferation of consumer sky lanterns and drones.

## Pipeline

```
data_raw.csv
    │
    ├── prep.py          →  ufo_clean.csv (80,331 rows, 21 columns)
    ├── state_pop.py     →  state_populations.csv
    ├── analysis.py      →  powerbi_data/*.csv  (8 aggregation tables)
    ├── text_mining.py   →  powerbi_data/*.csv  (5 NLP tables)
    └── preview.py       →  figures/*.png       (preview charts)
            │
            └── Power BI Desktop  →  ufo_dashboard.pbix
```

Three dashboard pages:
- **Map** — state choropleth (per-capita), top-city bubbles, slicers
- **Timeline** — yearly bars with NUFORC era split, hour×DOW heatmap, shape evolution, report lag
- **Phenomenon** — shape treemap, TF-IDF matrix, LDA topic terms, topic prevalence over time

## How to reproduce

The raw data is not in this repo. Download `scrubbed.csv` from the NUFORC dataset on Kaggle and save it to the project root as `data_raw.csv`.

```bash
pip install -r requirements.txt
python prep.py
python state_pop.py
python analysis.py
python text_mining.py
python preview.py
```

Then open `ufo_dashboard.pbix` in Power BI Desktop, or follow `powerbi_build_guide.md` to rebuild the dashboard from the generated CSVs.

## Files

| File | Purpose |
|---|---|
| `01_notebook.ipynb` | Analysis notebook with cleaning, EDA, NLP, LDA |
| `methodology.md` | Cleaning decisions, biases, limitations |
| `powerbi_build_guide.md` | Step-by-step dashboard build |
| `prep.py` | Cleaning pipeline |
| `state_pop.py` | 2010 Census state population table |
| `analysis.py` | Descriptive and geographic analysis |
| `text_mining.py` | Word frequencies, TF-IDF, LDA |
| `preview.py` | Preview charts for the README |
| `requirements.txt` | Python dependencies |
| `ufo_dashboard.pbix` | Power BI file |
| `figures/` | Charts and dashboard screenshots |

## Stack

Python (pandas, scikit-learn, matplotlib, seaborn) for the data pipeline. Power BI Desktop for the dashboard.

## Notes

The dataset measures UFO **reports**, not sightings - submissions to NUFORC's reporting system over 108 years. Reports before 1998 are retrospective recall; reports after 1998 are near-real-time submissions through the NUFORC web form. The two are not directly comparable.

The dataset is 88% US, 4% Canada, 3% UK, 1% Australia. Geographic findings should not be generalized outside Anglophone countries.
