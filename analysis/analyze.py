
import json
from pathlib import Path

import pandas as pd

# Project paths
ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "traffic.csv"
OUTPUT_DIR = ROOT / "data" / "processed"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 1. Load dataset
df = pd.read_csv(DATA_FILE)

print("Original dataset shape:", df.shape)

# 2. Remove duplicate records
df = df.drop_duplicates()

# 3. Convert columns to correct data types
df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
df["Vehicle_Count"] = pd.to_numeric(
    df["Vehicle_Count"], errors="coerce"
)
df["Average_Speed"] = pd.to_numeric(
    df["Average_Speed"], errors="coerce"
)

# 4. Remove records without essential information
df = df.dropna(
    subset=["Date", "Time", "Location", "Vehicle_Count", "Average_Speed"]
)

# Remove impossible values
df = df[
    (df["Vehicle_Count"] >= 0)
    & (df["Average_Speed"] >= 0)
    & (df["Average_Speed"] <= 200)
].copy()

# 5. Fill missing categorical values
for column in ["Weather", "Road_Condition", "Traffic_Level"]:
    if df[column].isna().any():
        df[column] = df[column].fillna(
            df[column].mode().iloc[0]
        )

# 6. Create useful time features
df["Hour"] = pd.to_datetime(
    df["Time"], format="%H:%M", errors="coerce"
).dt.hour

df["Day"] = df["Date"].dt.day_name()

df = df.dropna(subset=["Hour"]).copy()
df["Hour"] = df["Hour"].astype(int)

# 7. Save cleaned dataset
df.to_csv(OUTPUT_DIR / "traffic_clean.csv", index=False)

# 8. Analyze each road
road_summary = (
    df.groupby("Location")
    .agg(
        Total_Vehicles=("Vehicle_Count", "sum"),
        Average_Vehicles=("Vehicle_Count", "mean"),
        Average_Speed=("Average_Speed", "mean"),
        Records=("Location", "size")
    )
    .round(2)
    .reset_index()
)

road_summary.to_csv(OUTPUT_DIR / "road_summary.csv", index=False)

# 9. Analyze traffic by hour
hourly_summary = (
    df.groupby("Hour")
    .agg(
        Average_Vehicles=("Vehicle_Count", "mean"),
        Average_Speed=("Average_Speed", "mean")
    )
    .round(2)
    .reset_index()
)

hourly_summary.to_csv(
    OUTPUT_DIR / "hourly_summary.csv", index=False
)

# 10. Count traffic categories
traffic_counts = (
    df["Traffic_Level"]
    .str.title()
    .value_counts()
    .to_dict()
)

# 11. Identify busiest hour and road
busiest_hour = int(
    hourly_summary.loc[
        hourly_summary["Average_Vehicles"].idxmax(), "Hour"
    ]
)

busiest_road = road_summary.loc[
    road_summary["Total_Vehicles"].idxmax(), "Location"
]

# 12. Save a summary for the future dashboard
summary = {
    "total_records": int(len(df)),
    "total_vehicles": int(df["Vehicle_Count"].sum()),
    "average_speed": round(float(df["Average_Speed"].mean()), 2),
    "busiest_hour": busiest_hour,
    "busiest_road": str(busiest_road),
    "traffic_distribution": {
        str(key): int(value)
        for key, value in traffic_counts.items()
    }
}

with open(OUTPUT_DIR / "dashboard_summary.json", "w") as file:
    json.dump(summary, file, indent=4)

# 13. Display results
print("\nPREPROCESSING COMPLETED")
print("Cleaned dataset shape:", df.shape)

print("\nROAD SUMMARY")
print(road_summary.to_string(index=False))

print("\nHOURLY TRAFFIC SUMMARY")
print(hourly_summary.to_string(index=False))

print("\nTRAFFIC DISTRIBUTION")
print(traffic_counts)

print("\nDASHBOARD SUMMARY")
print(json.dumps(summary, indent=4))

print("\nOutput files saved in:", OUTPUT_DIR)