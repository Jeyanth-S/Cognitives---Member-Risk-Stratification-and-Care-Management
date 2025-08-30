import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

# -------------------------------
# Step 1. Load dataset
# -------------------------------
file_path = r"C:\Users\kesh2\OneDrive\Documents\Cognitives---Member-Risk-Stratification-and-Care-Management\pipeline\notebooks\beneficiary_with_recency.csv"
df = pd.read_csv(file_path)

# -------------------------------
# Step 2. Feature Engineering
# -------------------------------
# Disease columns (1 = has disease, 2 = no disease)
disease_cols = [col for col in df.columns if "SP_" in col]

# Convert {1 = disease, 2 = no disease} → binary {1, 0}
for col in disease_cols:
    df[col] = df[col].apply(lambda x: 1 if x == 1 else 0)

# Chronic disease burden in 2010
disease_cols_2010 = [c for c in disease_cols if "_2010" in c]
df["comorbidity_count_2010"] = df[disease_cols_2010].sum(axis=1)

# New comorbidities in 2009 vs 2008
disease_cols_2009 = [c for c in disease_cols if "_2009" in c]
disease_cols_2008 = [c.replace("2009", "2008") for c in disease_cols_2009]

diff_2009 = df[disease_cols_2009].values - df[disease_cols_2008].values
df["new_comorbidities_2009"] = np.clip(diff_2009, a_min=0, a_max=None).sum(axis=1)

# New comorbidities in 2010 vs 2009
diff_2010 = df[disease_cols_2010].values - df[disease_cols_2009].values
df["new_comorbidities_2010"] = np.clip(diff_2010, a_min=0, a_max=None).sum(axis=1)

# Persistent conditions (if condition persists across 2009 and 2010)
df["persistent_conditions"] = ((df[disease_cols_2009].values + df[disease_cols_2010].values) == 2).sum(axis=1)

# Severity score (weighted like Charlson Index)
weights = {
    "SP_CHF_2010": 3,
    "SP_COPD_2010": 2,
    "SP_DIABETES_2010": 2,
    "SP_CNCR_2010": 2,
    "SP_DEPRESSN_2010": 1,
    "SP_STRKETIA_2010": 2,
    "SP_ALZHDMTA_2010": 2,
    "SP_CHRNKIDN_2010": 3
}
df["severity_score"] = 0
for col, w in weights.items():
    if col in df.columns:
        df["severity_score"] += df[col] * w

# Total visits in last 90 days
df["total_recent_visits"] = df["recent_visits_30"] + df["recent_visits_60"] + df["recent_visits_90"]

# Visit ratio
df["visit_ratio_30_to_90"] = df.apply(
    lambda x: x["recent_visits_30"] / x["recent_visits_90"] if x["recent_visits_90"] > 0 else 0,
    axis=1
)

# -------------------------------
# Step 3. Proxy Risk Scores (30/60/90)
# -------------------------------
df["Risk_30"] = (0.5 * df["recent_visits_30"] +
                 0.3 * df["severity_score"] +
                 0.2 * df["comorbidity_count_2010"])

df["Risk_60"] = (0.4 * df["recent_visits_60"] +
                 0.3 * df["severity_score"] +
                 0.3 * df["comorbidity_count_2010"])

df["Risk_90"] = (0.3 * df["recent_visits_90"] +
                 0.3 * df["severity_score"] +
                 0.4 * df["comorbidity_count_2010"])

# Normalize scores 0–100
for col in ["Risk_30", "Risk_60", "Risk_90"]:
    df[col] = 100 * (df[col] - df[col].min()) / (df[col].max() - df[col].min())

# -------------------------------
# Step 4. Tier Stratification (KMeans clustering)
# -------------------------------
risk_features = df[["Risk_30", "Risk_60", "Risk_90"]]

kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
df["Tier"] = kmeans.fit_predict(risk_features)

# Map clusters → ordered tiers (0=Low, 4=High)
tier_order = df.groupby("Tier")[["Risk_30", "Risk_60", "Risk_90"]].mean().mean(axis=1).sort_values().index
tier_map = {old: new for new, old in enumerate(tier_order)}
df["Tier"] = df["Tier"].map(tier_map)

# -------------------------------
# Step 5. Export Final Output
# -------------------------------
output = df[[
    "DESYNPUF_ID", "Risk_30", "Risk_60", "Risk_90", "Tier",
    "comorbidity_count_2010", "new_comorbidities_2009", "new_comorbidities_2010",
    "persistent_conditions", "severity_score", "total_recent_visits", "visit_ratio_30_to_90"
]]

output.to_csv("beneficiary_with_labels.csv", index=False)
print("✅ Final file saved: beneficiary_with_labels.csv")
