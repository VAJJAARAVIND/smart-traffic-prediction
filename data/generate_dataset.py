import pandas as pd
import numpy as np
from datetime import datetime, timedelta

np.random.seed(42)

locations = ["Road A", "Road B", "Road C", "Road D", "Road E"]
weather_conditions = ["Clear", "Cloudy", "Rain"]
road_conditions = ["Good", "Normal", "Poor"]

data = []

start_date = datetime(2026, 1, 1)

for day in range(120):
    current_date = start_date + timedelta(days=day)

    for hour in range(6, 23):
        for location in locations:

            # Generate more vehicles during peak hours
            if hour in [8, 9, 18, 19]:
                base_vehicles = np.random.randint(450, 750)
            elif hour in [10, 11, 17, 20]:
                base_vehicles = np.random.randint(300, 550)
            else:
                base_vehicles = np.random.randint(100, 350)

            location_factor = {
                "Road A": 1.15,
                "Road B": 0.95,
                "Road C": 0.75,
                "Road D": 1.05,
                "Road E": 0.85
            }

            vehicle_count = int(
                base_vehicles * location_factor[location]
            )

            vehicle_count += np.random.randint(-30, 31)

            # Higher traffic generally means lower speed
            average_speed = max(
                8,
                60 - (vehicle_count / 14) + np.random.randint(-5, 6)
            )

            weather = np.random.choice(
                weather_conditions,
                p=[0.65, 0.25, 0.10]
            )

            road_condition = np.random.choice(
                road_conditions,
                p=[0.60, 0.30, 0.10]
            )

            # Generate traffic category
            if vehicle_count >= 500 or average_speed < 20:
                traffic_level = "High"
            elif vehicle_count >= 300 or average_speed < 35:
                traffic_level = "Medium"
            else:
                traffic_level = "Low"

            data.append([
                current_date.strftime("%Y-%m-%d"),
                f"{hour:02d}:00",
                location,
                vehicle_count,
                round(average_speed, 2),
                weather,
                road_condition,
                traffic_level
            ])

columns = [
    "Date",
    "Time",
    "Location",
    "Vehicle_Count",
    "Average_Speed",
    "Weather",
    "Road_Condition",
    "Traffic_Level"
]

df = pd.DataFrame(data, columns=columns)

df.to_csv("data/traffic.csv", index=False)

print("Traffic dataset created successfully!")
print(f"Total records: {len(df)}")
print("\nFirst 10 records:")
print(df.head(10))