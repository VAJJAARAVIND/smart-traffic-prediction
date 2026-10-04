
from pathlib import Path
import json

import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

# Project paths
ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "processed" / "traffic_clean.csv"
MODEL_DIR = ROOT / "models"

MODEL_DIR.mkdir(parents=True, exist_ok=True)

# Load cleaned dataset
df = pd.read_csv(DATA_FILE)

# Input features and prediction target
features = [
    "Vehicle_Count",
    "Average_Speed",
    "Hour",
    "Location",
    "Weather",
    "Road_Condition",
]

target = "Traffic_Level"

X = df[features]
y = df[target].str.title()

# Separate numerical and categorical columns
numeric_features = [
    "Vehicle_Count",
    "Average_Speed",
    "Hour",
]

categorical_features = [
    "Location",
    "Weather",
    "Road_Condition",
]

# Preprocess numerical and categorical features
numeric_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="median"))
])

categorical_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="most_frequent")),
    ("encoder", OneHotEncoder(handle_unknown="ignore"))
])

preprocessor = ColumnTransformer([
    ("numeric", numeric_pipeline, numeric_features),
    ("categorical", categorical_pipeline, categorical_features),
])

# Create machine learning pipeline
model = Pipeline([
    ("preprocessor", preprocessor),
    ("classifier", RandomForestClassifier(
        n_estimators=150,
        random_state=42,
        class_weight="balanced"
    )),
])

# Split data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y,
)

# Train model
print("Training traffic prediction model...")
model.fit(X_train, y_train)

# Evaluate model
predictions = model.predict(X_test)

accuracy = accuracy_score(y_test, predictions)

print("\nMODEL TRAINING COMPLETED")
print(f"Training records: {len(X_train)}")
print(f"Testing records: {len(X_test)}")
print(f"Accuracy: {accuracy:.4f} ({accuracy * 100:.2f}%)")

print("\nCLASSIFICATION REPORT")
print(classification_report(y_test, predictions))

# Save trained model
model_path = MODEL_DIR / "traffic_model.joblib"
joblib.dump(model, model_path)

# Save evaluation results
results = {
    "model": "Random Forest Classifier",
    "accuracy": round(float(accuracy), 4),
    "training_records": int(len(X_train)),
    "testing_records": int(len(X_test)),
    "classes": sorted(y.unique().tolist()),
}

with open(MODEL_DIR / "model_metrics.json", "w") as file:
    json.dump(results, file, indent=4)

print("Model saved to:", model_path)
print("Metrics saved to:", MODEL_DIR / "model_metrics.json")