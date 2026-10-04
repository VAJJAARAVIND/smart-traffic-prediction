
from pathlib import Path
import json
import math
import os
import sqlite3
from datetime import datetime, timezone

import joblib
import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS


# =========================================================
# 1. PROJECT CONFIGURATION
# =========================================================

ROOT = Path(__file__).resolve().parent

MODEL_PATH = ROOT / "models" / "traffic_model.joblib"
DATA_DIR = ROOT / "data" / "processed"
METRICS_PATH = ROOT / "models" / "model_metrics.json"

# Set DB_PATH to a persistent disk path on Render if needed.
# Example: /var/data/traffic_history.db
DB_PATH = Path(
    os.environ.get(
        "DB_PATH",
        str(ROOT / "traffic_history.db")
    )
)

DB_PATH.parent.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
CORS(app)


# =========================================================
# 2. LOAD TRAINED MACHINE LEARNING MODEL
# =========================================================

if not MODEL_PATH.exists():
    raise FileNotFoundError(
        f"Trained model not found: {MODEL_PATH}"
    )

model = joblib.load(MODEL_PATH)


# =========================================================
# 3. DATABASE INITIALIZATION
# =========================================================

def init_db():
    """Create the prediction history table."""

    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS prediction_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_count REAL NOT NULL,
                average_speed REAL NOT NULL,
                hour INTEGER NOT NULL,
                location TEXT NOT NULL,
                weather TEXT NOT NULL,
                road_condition TEXT NOT NULL,
                predicted_traffic_level TEXT NOT NULL,
                confidence_percent REAL NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        connection.commit()


init_db()


# =========================================================
# 4. HOME API
# =========================================================

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "project": "Smart Traffic Prediction and Monitoring System",
        "status": "success",
        "message": "Flask API is running"
    })


# =========================================================
# 5. DASHBOARD SUMMARY API
# =========================================================

@app.route("/api/summary", methods=["GET"])
def summary():
    file_path = DATA_DIR / "dashboard_summary.json"

    if not file_path.exists():
        return jsonify({
            "error": "Dashboard summary file not found"
        }), 404

    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    return jsonify(data)


# =========================================================
# 6. ROAD ANALYTICS API
# =========================================================

@app.route("/api/roads", methods=["GET"])
def roads():
    file_path = DATA_DIR / "road_summary.csv"

    if not file_path.exists():
        return jsonify({
            "error": "Road summary file not found"
        }), 404

    df = pd.read_csv(file_path)

    return jsonify(df.to_dict(orient="records"))


# =========================================================
# 7. HOURLY TRAFFIC API
# =========================================================

@app.route("/api/hourly", methods=["GET"])
def hourly():
    file_path = DATA_DIR / "hourly_summary.csv"

    if not file_path.exists():
        return jsonify({
            "error": "Hourly summary file not found"
        }), 404

    df = pd.read_csv(file_path)

    return jsonify(df.to_dict(orient="records"))


# =========================================================
# 8. MACHINE LEARNING METRICS API
# =========================================================

@app.route("/api/model-metrics", methods=["GET"])
def model_metrics():
    if not METRICS_PATH.exists():
        return jsonify({
            "error": "Model metrics file not found"
        }), 404

    with open(METRICS_PATH, "r", encoding="utf-8") as file:
        metrics = json.load(file)

    return jsonify(metrics)


# =========================================================
# 9. TRAFFIC PREDICTION API
# =========================================================

@app.route("/api/predict", methods=["POST"])
def predict():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "error": "Please send a valid JSON object"
        }), 400

    required_fields = [
        "Vehicle_Count",
        "Average_Speed",
        "Hour",
        "Location",
        "Weather",
        "Road_Condition"
    ]

    missing_fields = [
        field for field in required_fields
        if field not in data
    ]

    if missing_fields:
        return jsonify({
            "error": "Missing required fields",
            "fields": missing_fields
        }), 400

    try:
        # Validate numeric input
        vehicle_count = float(data["Vehicle_Count"])
        average_speed = float(data["Average_Speed"])
        hour_value = float(data["Hour"])

        numeric_values = [
            vehicle_count,
            average_speed,
            hour_value
        ]

        if not all(math.isfinite(value) for value in numeric_values):
            raise ValueError("Numeric values must be finite")

        if not 0 <= vehicle_count <= 100000:
            raise ValueError(
                "Vehicle count must be between 0 and 100000"
            )

        if not 0 <= average_speed <= 200:
            raise ValueError(
                "Average speed must be between 0 and 200 km/h"
            )

        if not hour_value.is_integer() or not 0 <= hour_value <= 23:
            raise ValueError(
                "Hour must be a whole number between 0 and 23"
            )

        hour = int(hour_value)

        # Validate categorical input
        location = str(data["Location"]).strip()
        weather = str(data["Weather"]).strip()
        road_condition = str(data["Road_Condition"]).strip()

        if not location or not weather or not road_condition:
            raise ValueError(
                "Location, weather, and road condition are required"
            )

        # Prepare features in the same format used during training
        features = pd.DataFrame([{
            "Vehicle_Count": vehicle_count,
            "Average_Speed": average_speed,
            "Hour": hour,
            "Location": location,
            "Weather": weather,
            "Road_Condition": road_condition
        }])

        # Generate traffic prediction
        prediction = str(model.predict(features)[0])

        # Calculate predicted class probabilities
        probabilities = model.predict_proba(features)[0]
        classes = model.named_steps["classifier"].classes_

        confidence = float(max(probabilities)) * 100

        probability_details = {
            str(label): round(float(probability) * 100, 2)
            for label, probability in zip(classes, probabilities)
        }

        timestamp = datetime.now(timezone.utc).isoformat()

        # Save prediction to SQLite
        with sqlite3.connect(DB_PATH) as connection:
            connection.execute("""
                INSERT INTO prediction_history (
                    vehicle_count,
                    average_speed,
                    hour,
                    location,
                    weather,
                    road_condition,
                    predicted_traffic_level,
                    confidence_percent,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                vehicle_count,
                average_speed,
                hour,
                location,
                weather,
                road_condition,
                prediction,
                round(confidence, 2),
                timestamp
            ))

            connection.commit()

        # Return prediction to the frontend
        return jsonify({
            "status": "success",
            "predicted_traffic_level": prediction,
            "confidence_percent": round(confidence, 2),
            "probabilities": probability_details,
            "input": {
                "Vehicle_Count": vehicle_count,
                "Average_Speed": average_speed,
                "Hour": hour,
                "Location": location,
                "Weather": weather,
                "Road_Condition": road_condition
            },
            "created_at": timestamp
        })

    except (ValueError, TypeError, OverflowError) as error:
        return jsonify({
            "error": str(error)
        }), 400

    except Exception:
        app.logger.exception("Traffic prediction failed")

        return jsonify({
            "error": "An internal error occurred during prediction"
        }), 500


# =========================================================
# 10. PREDICTION HISTORY API
# =========================================================

@app.route("/api/predictions", methods=["GET"])
def prediction_history():
    limit = request.args.get("limit", default=100, type=int)

    if limit is None or not 1 <= limit <= 500:
        return jsonify({
            "error": "Limit must be between 1 and 500"
        }), 400

    try:
        with sqlite3.connect(DB_PATH) as connection:
            connection.row_factory = sqlite3.Row

            rows = connection.execute("""
                SELECT
                    id,
                    vehicle_count,
                    average_speed,
                    hour,
                    location,
                    weather,
                    road_condition,
                    predicted_traffic_level,
                    confidence_percent,
                    created_at
                FROM prediction_history
                ORDER BY id DESC
                LIMIT ?
            """, (limit,)).fetchall()

        return jsonify({
            "status": "success",
            "count": len(rows),
            "predictions": [
                dict(row) for row in rows
            ]
        })

    except sqlite3.Error:
        app.logger.exception(
            "Could not retrieve prediction history"
        )

        return jsonify({
            "error": "Unable to retrieve prediction history"
        }), 500


# =========================================================
# 11. RUN APPLICATION
# =========================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )