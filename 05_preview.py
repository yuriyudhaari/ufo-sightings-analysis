"""
Preview charts - sanity check the analysis before handing off to Power BI.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_style("whitegrid")
plt.rcParams["figure.dpi"] = 110
plt.rcParams["savefig.dpi"] = 140
plt.rcParams["font.size"] = 10

import os
os.makedirs("figures", exist_ok=True)

#1. The platform-effect story: reports per year
yearly = pd.read_csv("powerbi_data/yearly_counts.csv")
yearly = yearly[yearly["year"] >= 1940]

fig, ax = plt.subplots(figsize=(11, 4.5))
ax.bar(yearly["year"], yearly["reports"], color="#2c3e50", width=0.85)
ax.axvline(1997.5, color="#c0392b", linestyle="--", linewidth=2,
           label="NUFORC launches web reporting (1998)")
ax.set_xlabel("Year")
ax.set_ylabel("Reports")
ax.set_title("UFO reports by year — the 1998 reporting platform effect")
ax.legend(loc="upper left")
ax.set_xlim(1940, 2015)
#Annotations
ax.annotate("Peak: 2012\n(7,356 reports)", xy=(2012, 7356), xytext=(2007, 7800),
            fontsize=9, arrowprops=dict(arrowstyle="->", color="grey"))
plt.tight_layout()
plt.savefig("figures/01_yearly_reports.png")
plt.close()

#2. Hour-of-day heatmap
heat = pd.read_csv("powerbi_data/hour_dow_heatmap.csv")
dow_order = ["Monday", "Tuesday", "Wednesday", "Thursday",
             "Friday", "Saturday", "Sunday"]
pivot = heat.pivot(index="day_of_week", columns="hour", values="reports").reindex(dow_order)

fig, ax = plt.subplots(figsize=(12, 4))
sns.heatmap(pivot, cmap="YlOrRd", cbar_kws={"label": "Reports"}, ax=ax,
            linewidths=0.3, linecolor="white")
ax.set_xlabel("Hour of day")
ax.set_ylabel("")
ax.set_title("When people see UFOs — hour × day-of-week\n"
             "Peak: 9–10 PM, with a weekend bias (Fri/Sat)")
plt.tight_layout()
plt.savefig("figures/02_hour_dow_heatmap.png")
plt.close()

#3. State per-capita choropleth-style horizontal bar
states = pd.read_csv("powerbi_data/state_rates.csv").sort_values("reports_per_100k", ascending=True)

fig, ax = plt.subplots(figsize=(8, 11))
colors = ["#c0392b" if x >= 40 else "#34495e" if x >= 25 else "#7f8c8d"
          for x in states["reports_per_100k"]]
ax.barh(states["state_name"], states["reports_per_100k"], color=colors)
ax.set_xlabel("Reports per 100,000 residents (2010 pop)")
ax.set_title("UFO reports per capita by US state\n"
             "Pacific Northwest dominates; Deep South under-reports")
plt.tight_layout()
plt.savefig("figures/03_state_per_capita.png")
plt.close()

#4. Shape evolution over decades
shape_dec = pd.read_csv("powerbi_data/shape_by_decade.csv")
shape_dec = shape_dec[shape_dec["decade"] >= 1950]
pivot = shape_dec.pivot(index="decade", columns="shape_family", values="share").fillna(0)

#Order columns by recency relevance
col_order = ["Light/Orb", "Sphere/Circle", "Triangle", "Disk", "Fireball",
             "Cigar/Cylinder", "Formation", "Rectangle", "Changing", "Other/Unknown"]
pivot = pivot[[c for c in col_order if c in pivot.columns]]

palette = ["#f1c40f", "#3498db", "#e74c3c", "#9b59b6", "#e67e22",
           "#1abc9c", "#34495e", "#95a5a6", "#7f8c8d", "#bdc3c7"]

fig, ax = plt.subplots(figsize=(11, 5))
pivot.plot.area(ax=ax, color=palette[:len(pivot.columns)], alpha=0.85, stacked=True)
ax.set_xlabel("Decade")
ax.set_ylabel("Share of reports")
ax.set_title("Shape families over time — the disk era gives way to lights/orbs")
ax.set_ylim(0, 1)
ax.legend(loc="center left", bbox_to_anchor=(1.0, 0.5), fontsize=9)
plt.tight_layout()
plt.savefig("figures/04_shape_evolution.png")
plt.close()

#5. Report lag distribution
lag = pd.read_csv("powerbi_data/report_lag_summary.csv")
fig, ax = plt.subplots(figsize=(8, 4))
bars = ax.bar(lag["lag_bucket"], lag["reports"], color="#2c3e50")
for b, n, s in zip(bars, lag["reports"], lag["share"]):
    ax.text(b.get_x() + b.get_width()/2, n + 400, f"{s:.1%}",
            ha="center", fontsize=9)
ax.set_xlabel("Time between sighting and submission")
ax.set_ylabel("Reports")
ax.set_title("Report lag — 1 in 5 reports describes a sighting more than a year old")
plt.xticks(rotation=20, ha="right")
plt.tight_layout()
plt.savefig("figures/05_report_lag.png")
plt.close()

#6. Top cities
cities = pd.read_csv("powerbi_data/top_cities.csv").head(15)
cities["label"] = cities["city"].str.title() + ", " + cities["state"].str.upper()

fig, ax = plt.subplots(figsize=(8, 5))
ax.barh(cities["label"][::-1], cities["reports"][::-1], color="#34495e")
ax.set_xlabel("Reports")
ax.set_title("Top 15 US cities by raw report count")
plt.tight_layout()
plt.savefig("figures/06_top_cities.png")
plt.close()

#7. LDA topic prevalence over time
topic_dec = pd.read_csv("powerbi_data/topic_by_decade.csv")
topic_dec = topic_dec[topic_dec["decade"] >= 1970]
topic_terms = pd.read_csv("powerbi_data/topic_terms.csv")

#Build topic labels from top 3 words
topic_labels = {}
for tid in topic_terms["topic_id"].unique():
    top3 = topic_terms[topic_terms["topic_id"] == tid].head(3)["word"].tolist()
    topic_labels[tid] = f"T{tid}: {', '.join(top3)}"

topic_dec["topic_label"] = topic_dec["dominant_topic"].map(topic_labels)
pivot = topic_dec.pivot(index="decade", columns="topic_label", values="share").fillna(0)

fig, ax = plt.subplots(figsize=(11, 5))
pivot.plot(ax=ax, marker="o", linewidth=1.5, alpha=0.85)
ax.set_xlabel("Decade")
ax.set_ylabel("Share of reports")
ax.set_title("LDA topic prevalence by decade")
ax.legend(loc="center left", bbox_to_anchor=(1.0, 0.5), fontsize=8)
plt.tight_layout()
plt.savefig("figures/07_topics_over_time.png")
plt.close()

print("All preview charts saved to figures/")