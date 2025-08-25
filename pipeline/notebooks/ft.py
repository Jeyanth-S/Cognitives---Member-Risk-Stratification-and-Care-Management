
# train_risk_models.py
import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, accuracy_score
from lightgbm import LGBMClassifier

# ------------------ Paths ------------------
FEATURES_PATH = "combined_features_2010.parquet"
LABELS_PATH   = "risk_tiers_consistent.csv"
MODEL_30D = "model_30d.pkl"
MODEL_60D = "model_60d.pkl"
MODEL_90D = "model_90d.pkl"

# ------------------ Load Data ------------------
features = pd.read_parquet(FEATURES_PATH)
labels   = pd.read_csv(LABELS_PATH)

# Merge on DESYNPUF_ID
df = pd.merge(features, labels, on="DESYNPUF_ID", how="inner")

# ------------------ Feature Preprocessing ------------------
drop_cols = [
    "DESYNPUF_ID",
    "score_30d","tier_30d",
    "score_60d","tier_60d",
    "score_90d","tier_90d"
]
X = df.drop(columns=drop_cols)

# Convert categorical / object dtypes → numeric
for col in X.columns:
    if X[col].dtype == "object":
        # If binary values like Y/N or 0/1
        if set(X[col].unique()) <= {"Y", "N"}:
            X[col] = X[col].map({"Y": 1, "N": 0}).astype(int)
        else:
            # Multi-class categorical: use LabelEncoder
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col].astype(str))

# Ensure all features are numeric
X = X.apply(pd.to_numeric, errors="coerce").fillna(0.0)

# Labels
y30 = df["tier_30d"]
y60 = df["tier_60d"]
y90 = df["tier_90d"]

# ------------------ Function to Train ------------------
def train_and_save(X, y, model_path, window_name):
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    model = LGBMClassifier(
        n_estimators=500,
        learning_rate=0.05,
        max_depth=-1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42
    )

    model.fit(X_train, y_train)
    preds = model.predict(X_test)

    print(f"\n📊 {window_name} Classification Report")
    print(classification_report(y_test, preds))
    print("Accuracy:", accuracy_score(y_test, preds))

    joblib.dump(model, model_path)
    print(f"✅ Saved model to {model_path}")

# ------------------ Train Models ------------------
train_and_save(X, y30, MODEL_30D, "30-day")
train_and_save(X, y60, MODEL_60D, "60-day")
train_and_save(X, y90, MODEL_90D, "90-day")
