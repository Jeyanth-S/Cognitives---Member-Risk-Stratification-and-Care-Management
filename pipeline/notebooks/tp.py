import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier

# ---- Paths ----
FEATURES_PATH = "combined_features_2010.parquet"
LABELS_PATH   = "risk_tiers_consistent.csv"

# ---- Load data ----
features_df = pd.read_parquet(FEATURES_PATH)
labels_df   = pd.read_csv(LABELS_PATH)

# Merge on patient ID
df = features_df.merge(labels_df, on="DESYNPUF_ID", how="inner")

# ---- Parse AGE from BENE_BIRTH_DT ----
def parse_birth_dt_to_age(birth_col, asof_year=2010):
    s = birth_col.copy()
    if np.issubdtype(s.dtype, np.number):  
        s = s.astype("Int64").astype(str).str.zfill(8)
    s = pd.to_datetime(s, format="%Y%m%d", errors="coerce")
    ref = pd.Timestamp(f"{asof_year}-12-31")
    return ((ref - s).dt.days // 365).astype("float")

if "AGE" not in df.columns:
    df["AGE"] = parse_birth_dt_to_age(df["BENE_BIRTH_DT"])

df["AGE"] = df["AGE"].fillna(df["AGE"].median())

# ---- Create derived features ----
df["chronic_trend"] = df["chronic_count_2010"] - df["chronic_count_2008"]
df["chronic_sum"]   = df[["chronic_count_2008","chronic_count_2009","chronic_count_2010"]].sum(axis=1)
df["spend_per_visit"] = df["total_amount"] / df["total_visits"].replace(0, 1)
df["log_total_amount"] = np.log1p(df["total_amount"])
df["log_avg_claim"] = np.log1p(df["avg_claim_amount"])
df["visits_per_chronic"] = df["total_visits"] / (1+df["chronic_count_2010"])

# ---- Map tiers to numeric ----
tier_map = {"Very Low":0, "Low":1, "Medium":2, "High":3, "Very High":4}
df["tier_30d_num"] = df["tier_30d"].map(tier_map)
df["tier_60d_num"] = df["tier_60d"].map(tier_map)
df["tier_90d_num"] = df["tier_90d"].map(tier_map)

# ---- Features (must match risk_tiers_consistent.py) ----
features_30 = ["AGE","chronic_count_2010","chronic_trend","total_visits","spend_per_visit","log_avg_claim"]
features_60 = ["AGE","chronic_count_2010","chronic_sum","total_visits","log_total_amount","log_avg_claim","visits_per_chronic"]
features_90 = ["AGE","chronic_sum","total_visits","log_total_amount","spend_per_visit"]

# ---- Train RandomForest models ----
clf_30 = RandomForestClassifier(n_estimators=200, random_state=42).fit(df[features_30], df["tier_30d_num"])
clf_60 = RandomForestClassifier(n_estimators=200, random_state=42).fit(df[features_60], df["tier_60d_num"])
clf_90 = RandomForestClassifier(n_estimators=200, random_state=42).fit(df[features_90], df["tier_90d_num"])

# ---- Save models ----
joblib.dump(clf_30, "model_30d.pkl")
joblib.dump(clf_60, "model_60d.pkl")
joblib.dump(clf_90, "model_90d.pkl")

print("✅ Models trained and saved: model_30d.pkl, model_60d.pkl, model_90d.pkl")
