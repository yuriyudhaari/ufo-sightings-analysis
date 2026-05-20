"""
Phase A: UFO Sightings cleaning pipeline.
Input:  data_raw.csv (NUFORC scrubbed dataset)
Output: ufo_clean.csv (the main analytical table, Power BI-ready)
        cleaning_audit.txt (log of decisions and row counts)
"""

import html
import re
import pandas as pd
import numpy as np

#Configuration
#Defensible duration bounds. Below 5s = "instant" reports unreliable;
#above 2h = sustained observations are rare and frequently mis-entered.
DURATION_MIN_SEC = 5
DURATION_MAX_SEC = 7200  # 2 hours

#Shape family bucketing. Source values mapped to higher-level families.
SHAPE_FAMILIES = {
    #Lights and luminous objects
    "light": "Light/Orb", "flash": "Light/Orb", "flare": "Light/Orb",
    #Disks and saucers
    "disk": "Disk", "oval": "Disk", "dome": "Disk",
    #Triangles and angular shapes
    "triangle": "Triangle", "chevron": "Triangle", "delta": "Triangle",
    "pyramid": "Triangle",
    #Spheres and round objects
    "sphere": "Sphere/Circle", "circle": "Sphere/Circle", "round": "Sphere/Circle",
    "egg": "Sphere/Circle", "crescent": "Sphere/Circle",
    #Fireballs and bright trails
    "fireball": "Fireball", "teardrop": "Fireball",
    #Cigars and elongated
    "cigar": "Cigar/Cylinder", "cylinder": "Cigar/Cylinder",
    #Geometric/rectangular
    "rectangle": "Rectangle", "diamond": "Rectangle", "cross": "Rectangle",
    "cone": "Rectangle", "hexagon": "Rectangle",
    #Multi-object reports
    "formation": "Formation",
    #Morphing/ambiguous
    "changing": "Changing", "changed": "Changing",
    #Catch-all
    "other": "Other/Unknown", "unknown": "Other/Unknown",
}

#Country bounding boxes for inferring missing country labels from lat/lon.
#Order matters — checked top-to-bottom; first match wins.
#These are rough rectangles, not polygons; acceptable for a coarse fill.
COUNTRY_BOXES = [
    # (name, lat_min, lat_max, lon_min, lon_max)
    ("us", 24.5, 49.4, -125.0, -66.9),    # CONUS
    ("us", 51.0, 71.5, -180.0, -129.0),    # Alaska
    ("us", 18.9, 22.3, -160.5, -154.7),    # Hawaii
    ("ca", 41.7, 83.1, -141.0, -52.6),     # Canada
    ("gb", 49.9, 60.9, -8.6, 1.8),         # UK
    ("au", -43.6, -10.7, 113.0, 153.6),    # Australia
    ("de", 47.3, 55.1, 5.9, 15.0),         # Germany
]


#Helpers
def decode_html_text(s: str) -> str:
    """Decode HTML entities and normalize whitespace."""
    if pd.isna(s):
        return ""
    # NUFORC text has both numeric (&#44;) and named (&amp;) entities.
    s = html.unescape(str(s))
    # Decode any remaining numeric entities not caught by html.unescape
    s = re.sub(r"&#(\d+);", lambda m: chr(int(m.group(1))), s)
    # Collapse whitespace
    s = re.sub(r"\s+", " ", s).strip()
    return s


def infer_country(row) -> str:
    """Use lat/lon to assign a country code when missing."""
    if isinstance(row["country"], str) and row["country"]:
        return row["country"]
    lat, lon = row["latitude"], row["longitude"]
    if pd.isna(lat) or pd.isna(lon):
        return "unknown"
    for name, lat_min, lat_max, lon_min, lon_max in COUNTRY_BOXES:
        if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
            return name
    return "other"


#Pipeline
def load_and_prepare(path: str = "data_raw.csv"):
    audit = []
    log = audit.append

    df = pd.read_csv(path, low_memory=False)
    df.columns = df.columns.str.strip()  # source has 'longitude ' with trailing space
    log(f"rows_loaded: {len(df):,}")

    #1. Drop the row with corrupted latitude.
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    bad_lat = df["latitude"].isna().sum()
    df = df.dropna(subset=["latitude"]).copy()
    log(f"dropped_bad_latitude: {bad_lat}")

    #2. Parse datetime fields.
    df["sighting_dt"] = pd.to_datetime(df["datetime"], errors="coerce")
    df["posted_dt"] = pd.to_datetime(df["date posted"], errors="coerce")

    #3. Time features.
    df["year"] = df["sighting_dt"].dt.year
    df["month"] = df["sighting_dt"].dt.month
    df["day_of_week"] = df["sighting_dt"].dt.day_name()
    df["hour"] = df["sighting_dt"].dt.hour
    df["decade"] = (df["year"] // 10 * 10).astype("Int64")
    df["time_of_day"] = pd.cut(
        df["hour"],
        bins=[-1, 5, 11, 17, 21, 24],
        labels=["Night (0-5)", "Morning (6-11)", "Afternoon (12-17)",
                "Evening (18-21)", "Night (22-23)"],
    )

    #4. Report lag (days between sighting and submission).
    df["report_lag_days"] = (df["posted_dt"] - df["sighting_dt"]).dt.days
    # Some sightings are in the future relative to posting date (data entry error). Clip.
    df["report_lag_days"] = df["report_lag_days"].clip(lower=0)

    #5. Duration cleaning.
    df["duration_sec"] = pd.to_numeric(df["duration (seconds)"], errors="coerce")
    df["duration_reliable"] = (
        df["duration_sec"].between(DURATION_MIN_SEC, DURATION_MAX_SEC)
    ).fillna(False)
    log(f"duration_reliable_count: {df['duration_reliable'].sum():,}")
    log(f"duration_unreliable_count: {(~df['duration_reliable']).sum():,}")

    #6. Shape bucketing.
    df["shape"] = df["shape"].fillna("unknown").str.lower().str.strip()
    df["shape_family"] = df["shape"].map(SHAPE_FAMILIES).fillna("Other/Unknown")
    log(f"shape_families: {sorted(df['shape_family'].unique())}")

    #7. Country inference.
    df["country"] = df["country"].astype(str).str.lower().replace("nan", np.nan)
    df["country_clean"] = df.apply(infer_country, axis=1)
    inferred = ((df["country"].isna()) & (df["country_clean"] != "unknown")).sum()
    log(f"country_inferred_from_latlon: {inferred:,}")
    log(f"final_country_distribution: {dict(df['country_clean'].value_counts())}")

    #8. State cleanup.
    df["state"] = df["state"].astype(str).str.lower().str.strip().replace("nan", np.nan)

    #9. City cleanup.
    df["city"] = df["city"].astype(str).str.lower().str.strip()

    #10. Comment cleanup.
    df["comments_clean"] = df["comments"].apply(decode_html_text)
    df["comment_length"] = df["comments_clean"].str.len()

    #11. NUFORC era flag.
    df["era"] = np.where(df["year"] < 1998, "Pre-NUFORC web (retrospective)",
                          "NUFORC web era (1998+)")

    #12. Final column order — Power BI-friendly.
    cols = [
        "sighting_dt", "posted_dt", "year", "decade", "month", "day_of_week",
        "hour", "time_of_day", "era", "report_lag_days",
        "city", "state", "country_clean", "latitude", "longitude",
        "shape", "shape_family",
        "duration_sec", "duration_reliable",
        "comments_clean", "comment_length",
    ]
    clean = df[cols].rename(columns={"country_clean": "country"})

    log(f"final_rows: {len(clean):,}")
    log(f"final_cols: {clean.shape[1]}")
    log(f"year_range: {int(clean['year'].min())} to {int(clean['year'].max())}")

    return clean, audit


if __name__ == "__main__":
    df, audit = load_and_prepare()
    df.to_csv("ufo_clean.csv", index=False)
    with open("cleaning_audit.txt", "w") as f:
        f.write("\n".join(str(line) for line in audit))
    print("\n=== AUDIT ===")
    print("\n".join(str(line) for line in audit))
    print(f"\nSaved -> ufo_clean.csv ({len(df):,} rows)")