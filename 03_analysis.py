"""
Phase B: Descriptive, temporal, and geographic analysis.
Produces:
- yearly_counts.csv          time series of reports per year
- hour_dow_heatmap.csv       hour-of-day x day-of-week matrix
- shape_by_decade.csv        long-format shape distribution over time
- state_rates.csv            US state-level counts + per-capita rates
- top_cities.csv             top reporting cities (US, normalized by reports)
- report_lag_summary.csv     distribution of submission lag
"""

import pandas as pd
import numpy as np

df = pd.read_csv("ufo_clean.csv", low_memory=False, parse_dates=["sighting_dt", "posted_dt"])
pop = pd.read_csv("state_populations.csv")
pop["state_code"] = pop["state_code"].str.lower()

print(f"Loaded {len(df):,} cleaned reports.\n")

#1. Yearly time series
yearly = (
    df.dropna(subset=["year"])
    .groupby("year")
    .size()
    .reset_index(name="reports")
    .astype({"year": int})
)
yearly["era"] = np.where(yearly["year"] < 1998,
                          "Pre-NUFORC web", "NUFORC web era")
yearly.to_csv("powerbi_data/yearly_counts.csv", index=False)
print(f"yearly_counts: {len(yearly)} years")
print(f"  1997 reports: {yearly[yearly['year']==1997]['reports'].values[0]:,}")
print(f"  1998 reports: {yearly[yearly['year']==1998]['reports'].values[0]:,}")
print(f"  Peak year: {yearly.loc[yearly['reports'].idxmax(), 'year']} "
      f"({yearly['reports'].max():,} reports)\n")

#2. Hour x Day-of-week heatmap
dow_order = ["Monday", "Tuesday", "Wednesday", "Thursday",
             "Friday", "Saturday", "Sunday"]
heat = (
    df.dropna(subset=["hour", "day_of_week"])
    .groupby(["day_of_week", "hour"])
    .size()
    .reset_index(name="reports")
)
heat["hour"] = heat["hour"].astype(int)
heat.to_csv("powerbi_data/hour_dow_heatmap.csv", index=False)

#Quick peek: which hour dominates?
hour_totals = df.groupby("hour").size().sort_values(ascending=False)
print(f"Top 5 hours by reports:")
for h, c in hour_totals.head(5).items():
    print(f"  {int(h):02d}:00 -> {c:,}")
print()

#3. Shape distribution by decade
shape_decade = (
    df.dropna(subset=["decade"])
    .groupby(["decade", "shape_family"])
    .size()
    .reset_index(name="reports")
)
#Add normalized share within decade
shape_decade["decade_total"] = shape_decade.groupby("decade")["reports"].transform("sum")
shape_decade["share"] = shape_decade["reports"] / shape_decade["decade_total"]
shape_decade["decade"] = shape_decade["decade"].astype(int)
shape_decade.to_csv("powerbi_data/shape_by_decade.csv", index=False)
print(f"shape_by_decade rows: {len(shape_decade)}")
#Show 2000s shape mix
mix_2000 = shape_decade[shape_decade["decade"] == 2000].sort_values("share", ascending=False)
print("2000s shape mix (top 5):")
for _, r in mix_2000.head(5).iterrows():
    print(f"  {r['shape_family']:18s} {r['share']:.1%}")
print()

#4. State-level analysis (US only)
us = df[df["country"] == "us"].copy()
state_counts = us.groupby("state").size().reset_index(name="reports")
state_counts = state_counts.merge(pop, left_on="state", right_on="state_code", how="left")
state_counts = state_counts.dropna(subset=["population_2010"])
state_counts["reports_per_100k"] = (
    state_counts["reports"] / state_counts["population_2010"] * 100000
)
state_counts = state_counts.sort_values("reports_per_100k", ascending=False)
state_counts.to_csv("powerbi_data/state_rates.csv", index=False)
print(f"state_rates: {len(state_counts)} states")
print("Top 5 states per 100k:")
for _, r in state_counts.head(5).iterrows():
    print(f"  {r['state_name']:22s} {r['reports_per_100k']:6.1f}/100k  "
          f"({int(r['reports']):,} reports)")
print("Bottom 5 states per 100k:")
for _, r in state_counts.tail(5).iterrows():
    print(f"  {r['state_name']:22s} {r['reports_per_100k']:6.1f}/100k  "
          f"({int(r['reports']):,} reports)")
print()

#5. Top cities
city_counts = (
    us.groupby(["city", "state"])
    .size()
    .reset_index(name="reports")
    .sort_values("reports", ascending=False)
)
#Add latitude/longitude (median for the city)
city_geo = us.groupby(["city", "state"])[["latitude", "longitude"]].median().reset_index()
city_counts = city_counts.merge(city_geo, on=["city", "state"])
city_counts.head(500).to_csv("powerbi_data/top_cities.csv", index=False)
print(f"Top 10 US cities by report count:")
for _, r in city_counts.head(10).iterrows():
    print(f"  {r['city']:25s} {r['state'].upper()}  {int(r['reports']):,}")
print()

#6. Report lag
lag = df["report_lag_days"].dropna()
lag_buckets = pd.cut(
    lag,
    bins=[-1, 7, 30, 365, 365*5, 365*20, 365*200],
    labels=["≤1 week", "1 week–1 month", "1 month–1 year",
            "1–5 years", "5–20 years", "20+ years"],
)
lag_summary = lag_buckets.value_counts().sort_index().reset_index()
lag_summary.columns = ["lag_bucket", "reports"]
lag_summary["share"] = lag_summary["reports"] / lag_summary["reports"].sum()
lag_summary.to_csv("powerbi_data/report_lag_summary.csv", index=False)
print(f"\nReport-lag distribution (how long between sighting and submission):")
for _, r in lag_summary.iterrows():
    print(f"  {r['lag_bucket']:22s} {int(r['reports']):>7,}  ({r['share']:.1%})")

#7. Country summary for side panel
country = (
    df.groupby("country")
    .size()
    .reset_index(name="reports")
    .sort_values("reports", ascending=False)
)
country["share"] = country["reports"] / country["reports"].sum()
country.to_csv("powerbi_data/country_summary.csv", index=False)
print(f"\nGlobal country summary:")
for _, r in country.iterrows():
    print(f"  {r['country'].upper():6s} {int(r['reports']):>7,}  ({r['share']:.1%})")

print("\nAll Phase B outputs saved to powerbi_data/")