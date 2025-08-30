import os
import json
import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
import shap
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score, accuracy_score, f1_score
from sklearn.cluster import KMeans   # ✅ added for clustering

# -----------------------------
# CONFIG
# -----------------------------
DATA_PATH = r"C:\Users\kesh2\OneDrive\Documents\Cognitives---Member-Risk-Stratification-and-Care-Management\pipeline\notebooks\beneficiary_with_recency.csv"

# ✅ Define an artifacts folder (not a CSV file!)
ARTIFACT_DIR = r"C:\Users\kesh2\OneDrive\Documents\Cognitives---Member-Risk-Stratification-and-Care-Management\pipeline\notebooks\artifacts"
os.makedirs(ARTIFACT_DIR, exist_ok=True)

# ✅ Figures folder inside artifacts
FIG_DIR = os.path.join(ARTIFACT_DIR, "figs_test")
os.makedirs(FIG_DIR, exist_ok=True)

RANDOM_STATE = 42

# Disease weights used to build severity_score from raw flags (1=disease, 2=no disease in raw file)
SEVERITY_WEIGHTS_2010 = {
    "SP_CHF_2010": 3,
    "SP_CHRNKIDN_2010": 3,
    "SP_COPD_2010": 2,
    "SP_DIABETES_2010": 2,
    "SP_CNCR_2010": 2,
    "SP_STRKETIA_2010": 2,
    "SP_ALZHDMTA_2010": 2,
    "SP_DEPRESSN_2010": 1,
}

# Friendly feature names for stories
FRIENDLY = {
    "comorbidity_count_2010": "Comorbidity count (2010)",
    "new_comorbidities_2009": "New diagnoses in 2009",
    "new_comorbidities_2010": "New diagnoses in 2010",
    "persistent_conditions": "Persistent conditions",
    "severity_score": "Severity score",
    "total_recent_visits": "Total recent visits (90d)",
    "visit_ratio_30_to_90": "Visit ratio (30d/90d)",
    "AGE_2010": "Age",
}

# Tier -> recommended actions mapping (customize to your org)
TIER_ACTIONS = {
    4: ["Immediate intensive case management", "Home health assessment", "Medication reconciliation", "Specialist referral"],
    3: ["Assign care coordinator", "PCP follow-up within 7 days", "Medication review", "Telehealth check-in"],
    2: ["Outpatient follow-up", "Chronic disease coaching", "Adherence monitoring"],
    1: ["Preventive care reminders", "Routine wellness"],
    0: ["Routine screening", "Low-touch outreach"],
}

# -----------------------------
# HELPERS
# -----------------------------
def ensure_binary_flags(df, disease_cols):
    for c in disease_cols:
        if df[c].dropna().isin([1,2]).all():
            df[c] = df[c].apply(lambda v: 1 if v == 1 else 0)
    return df

def compute_engineered_features(df):
    disease_cols = [c for c in df.columns if c.startswith("SP_")]
    if disease_cols:
        df = ensure_binary_flags(df, disease_cols)
    cols_2008 = [c for c in disease_cols if c.endswith("_2008")]
    cols_2009 = [c for c in disease_cols if c.endswith("_2009")]
    cols_2010 = [c for c in disease_cols if c.endswith("_2010")]

    if "comorbidity_count_2010" not in df.columns:
        if cols_2010:
            df["comorbidity_count_2010"] = df[cols_2010].sum(axis=1)
        else:
            df["comorbidity_count_2010"] = 0

    if "new_comorbidities_2009" not in df.columns:
        if cols_2009 and cols_2008:
            diff_2009 = df[cols_2009].values - df[[c.replace("2009","2008") for c in cols_2009]].values
            df["new_comorbidities_2009"] = np.clip(diff_2009, a_min=0, a_max=None).sum(axis=1)
        else:
            df["new_comorbidities_2009"] = 0

    if "new_comorbidities_2010" not in df.columns:
        if cols_2010 and cols_2009:
            diff_2010 = df[cols_2010].values - df[cols_2009].values
            df["new_comorbidities_2010"] = np.clip(diff_2010, a_min=0, a_max=None).sum(axis=1)
        else:
            df["new_comorbidities_2010"] = 0

    if "persistent_conditions" not in df.columns:
        if cols_2009 and cols_2010:
            df["persistent_conditions"] = ((df[cols_2009].values + df[cols_2010].values) == 2).sum(axis=1)
        else:
            df["persistent_conditions"] = 0

    if "severity_score" not in df.columns:
        sev = np.zeros(len(df))
        for col, w in SEVERITY_WEIGHTS_2010.items():
            if col in df.columns:
                sev += df[col].values * w
        df["severity_score"] = sev

    for rv in ["recent_visits_30", "recent_visits_60", "recent_visits_90"]:
        if rv not in df.columns:
            df[rv] = 0.0
    if "total_recent_visits" not in df.columns:
        df["total_recent_visits"] = df["recent_visits_30"] + df["recent_visits_60"] + df["recent_visits_90"]

    if "visit_ratio_30_to_90" not in df.columns:
        denom = df["recent_visits_90"].copy().replace(0, np.nan)
        ratio = df["recent_visits_30"] / denom
        df["visit_ratio_30_to_90"] = ratio.fillna(0.0)

    return df

def maybe_build_proxy_risks(df):
    for col in ["Risk_30", "Risk_60", "Risk_90"]:
        if col not in df.columns:
            if col == "Risk_30":
                raw = (0.5*df["recent_visits_30"] + 0.3*df["severity_score"] + 0.2*df["comorbidity_count_2010"])
            elif col == "Risk_60":
                raw = (0.4*df["recent_visits_60"] + 0.3*df["severity_score"] + 0.3*df["comorbidity_count_2010"])
            else:
                raw = (0.3*df["recent_visits_90"] + 0.3*df["severity_score"] + 0.4*df["comorbidity_count_2010"])
            mn, mx = raw.min(), raw.max()
            df[col] = 100.0*(raw - mn)/(mx - mn) if mx > mn else 0.0
    return df

# ✅ UPDATED: KMeans-based tiering
def maybe_build_tier(df):
    if "Tier" not in df.columns:
        # Cluster using 30/60/90-day risks
        risk_features = df[["Risk_30","Risk_60","Risk_90"]]

        kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
        df["Tier"] = kmeans.fit_predict(risk_features)

        # Rank clusters by mean risk
        cluster_means = df.groupby("Tier")[["Risk_30","Risk_60","Risk_90"]].mean().mean(axis=1)
        sorted_clusters = cluster_means.sort_values().index
        tier_map = {old: new for new, old in enumerate(sorted_clusters)}
        df["Tier"] = df["Tier"].map(tier_map)
    return df

def friendly_feature_name(feat):
    return FRIENDLY.get(feat, feat.replace("_"," "))


def top_shap_phrases(shap_vals, features, x_row, k=5):
    """
    shap_vals: SHAP values for a single instance (array-like or Explanation)
    features: list of feature names
    x_row: pandas Series with feature values for the instance
    """
    # ✅ Convert Explanation to numpy
    vals = shap_vals.values if hasattr(shap_vals, "values") else np.array(shap_vals)
    sv = pd.Series(vals, index=features)

    top = sv.abs().sort_values(ascending=False).head(k)
    phrases = []
    for f in top.index:
        direction = "increases" if sv[f] > 0 else "decreases"
        fname = friendly_feature_name(f)
        val = x_row[f]
        if "visit" in f:
            phrases.append(f"{fname} = {val:.0f} ({direction} risk)")
        elif "comorbidity" in f or "persistent" in f:
            phrases.append(f"{fname} = {int(val)} ({direction} risk)")
        elif "severity" in f:
            phrases.append(f"{fname} = {val:.0f} ({direction} risk)")
        else:
            phrases.append(f"{fname} = {val} ({direction} risk)")
    return phrases


def build_shap_story(shap_vals, features, x_row, horizon_label):
    phrases = top_shap_phrases(shap_vals, features, x_row, k=5)
    # check new comorbidities specifically to mention
    new_2010 = int(x_row.get("new_comorbidities_2010", 0))
    new_phrase = ""
    if new_2010 > 0:
        new_phrase = f"Notably, the patient has {new_2010} new diagnosis(es) in 2010 which raises near-term risk. "
    # combine into a readable sentence
    sentence = (f"For the {horizon_label} window, the model predicts risk primarily driven by: "
                + "; ".join(phrases) + ". " + new_phrase)
    return sentence.strip()

def make_waterfall(shap_values_row, bene_id, label_name):
    """Save a SHAP waterfall plot for one patient and one label (returns path)."""
    try:
        shap.plots.waterfall(shap_values_row, max_display=10, show=False)
        out = os.path.join(FIG_DIR, f"{bene_id}_{label_name}_waterfall.png")
        plt.tight_layout()
        plt.savefig(out, dpi=150, bbox_inches="tight")
        plt.close()
        return out
    except Exception:
        vals = shap_values_row.values if hasattr(shap_values_row, "values") else np.array(shap_values_row)
        idx = np.argsort(np.abs(vals))[-10:][::-1]
        labels = [FRIENDLY.get(feat, feat) for feat in FEATURES][idx]
        plt.figure(figsize=(6,4))
        plt.barh(labels[::-1], vals[idx][::-1])
        plt.title(f"Top SHAP - {bene_id} - {label_name}")
        out = os.path.join(FIG_DIR, f"{bene_id}_{label_name}_bar.png")
        plt.tight_layout()
        plt.savefig(out, dpi=150, bbox_inches="tight")
        plt.close()
        return out

# -----------------------------
# LOAD + PREP
# -----------------------------
df = pd.read_csv(DATA_PATH)
df = compute_engineered_features(df)
df = maybe_build_proxy_risks(df)
df = maybe_build_tier(df)

FEATURES = [
    "comorbidity_count_2010",
    "new_comorbidities_2009",
    "new_comorbidities_2010",
    "persistent_conditions",
    "severity_score",
    "total_recent_visits",
    "visit_ratio_30_to_90",
]
if "AGE_2010" in df.columns:
    FEATURES.append("AGE_2010")

ID_COL = "DESYNPUF_ID"

y30 = df["Risk_30"].astype(float)
y60 = df["Risk_60"].astype(float)
y90 = df["Risk_90"].astype(float)
y_tier = df["Tier"].astype(int)

X = df[FEATURES].copy()

# train/test
X_train, X_test, y30_train, y30_test = train_test_split(X, y30, test_size=0.2, random_state=RANDOM_STATE)
_,      _,      y60_train, y60_test = train_test_split(X, y60, test_size=0.2, random_state=RANDOM_STATE)
_,      _,      y90_train, y90_test = train_test_split(X, y90, test_size=0.2, random_state=RANDOM_STATE)
Xc_train, Xc_test, yc_train, yc_test = train_test_split(X, y_tier, test_size=0.2, random_state=RANDOM_STATE, stratify=y_tier)

# -----------------------------
# TRAIN MODELS
# -----------------------------
reg_params = dict(
    n_estimators=200,   # ↓ fewer trees
    max_depth=3,        # ↓ shallower
    learning_rate=0.1,  
    subsample=0.7,      # more randomness
    colsample_bytree=0.7,
    reg_lambda=2.0,     # stronger regularization
    n_jobs=-1,
    random_state=RANDOM_STATE
)

clf_params = dict(
    n_estimators=200,
    max_depth=3,
    learning_rate=0.1,
    subsample=0.7,
    colsample_bytree=0.7,
    reg_lambda=2.0,
    objective="multi:softprob",
    num_class=5,
    n_jobs=-1,
    random_state=RANDOM_STATE
)



xgb30 = xgb.XGBRegressor(**reg_params)
xgb60 = xgb.XGBRegressor(**reg_params)
xgb90 = xgb.XGBRegressor(**reg_params)
xgbTier = xgb.XGBClassifier(**clf_params)

xgb30.fit(X_train, y30_train)
xgb60.fit(X_train, y60_train)
xgb90.fit(X_train, y90_train)
xgbTier.fit(Xc_train, yc_train)

# evaluate
def eval_reg(name, model, X_te, y_te):
    pred = model.predict(X_te)
    print(f"[{name}] MSE={mean_squared_error(y_te, pred):.4f} MAE={mean_absolute_error(y_te, pred):.4f} R2={r2_score(y_te, pred):.4f}")

eval_reg("Risk_30", xgb30, X_test, y30_test)
eval_reg("Risk_60", xgb60, X_test, y60_test)
eval_reg("Risk_90", xgb90, X_test, y90_test)

tier_pred = xgbTier.predict(Xc_test)
print(f"[Tier] ACC={accuracy_score(yc_test, tier_pred):.4f} F1(macro)={f1_score(yc_test, tier_pred, average='macro'):.4f}")

# -----------------------------
# SHAP EXPLAINERS & GLOBAL PLOTS
# -----------------------------
shap_explainer_30 = shap.TreeExplainer(xgb30)
shap_explainer_60 = shap.TreeExplainer(xgb60)
shap_explainer_90 = shap.TreeExplainer(xgb90)

def global_beeswarm(model_name, explainer, X_te):
    sv = explainer(X_te, check_additivity=False)
    plt.figure(figsize=(8,6))
    shap.summary_plot(sv, X_te, show=False)
    out = os.path.join(FIG_DIR, f"global_{model_name}_beeswarm.png")
    plt.tight_layout()
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    return out

bees30 = global_beeswarm("Risk_30", shap_explainer_30, X_test)
bees60 = global_beeswarm("Risk_60", shap_explainer_60, X_test)
bees90 = global_beeswarm("Risk_90", shap_explainer_90, X_test)
print("Saved global SHAP beeswarm plots:", bees30, bees60, bees90)

# -----------------------------
# PREDICT & EXPLAIN BY ID
# -----------------------------
def predict_and_explain_by_id(bene_id: str):
    row = df[df[ID_COL] == bene_id]
    if row.empty:
        raise ValueError(f"Beneficiary {bene_id} not found.")
    X_row = row[FEATURES]
    p30 = float(xgb30.predict(X_row)[0])
    p60 = float(xgb60.predict(X_row)[0])
    p90 = float(xgb90.predict(X_row)[0])
    ptier = int(xgbTier.predict(X_row)[0])

    sv30 = shap_explainer_30(X_row, check_additivity=False)[0]
    sv60 = shap_explainer_60(X_row, check_additivity=False)[0]
    sv90 = shap_explainer_90(X_row, check_additivity=False)[0]

    story30 = build_shap_story(sv30, FEATURES, X_row.iloc[0], "30-day")
    story60 = build_shap_story(sv60, FEATURES, X_row.iloc[0], "60-day")
    story90 = build_shap_story(sv90, FEATURES, X_row.iloc[0], "90-day")

    wf30 = make_waterfall(sv30, bene_id, "Risk_30")
    wf60 = make_waterfall(sv60, bene_id, "Risk_60")
    wf90 = make_waterfall(sv90, bene_id, "Risk_90")

    recommended = "; ".join(TIER_ACTIONS.get(ptier, TIER_ACTIONS[0]))

    result = {
        "Beneficiary_ID": bene_id,
        "Pred_Risk_30": round(p30,2),
        "Pred_Risk_60": round(p60,2),
        "Pred_Risk_90": round(p90,2),
        "Pred_Tier": int(ptier),
        "Top_Drivers_Risk30": " | ".join(top_shap_phrases(sv30.values if hasattr(sv30, "values") else sv30, FEATURES, X_row.iloc[0], k=5)),
        "Top_Drivers_Risk60": " | ".join(top_shap_phrases(sv60.values if hasattr(sv60, "values") else sv60, FEATURES, X_row.iloc[0], k=5)),
        "Top_Drivers_Risk90": " | ".join(top_shap_phrases(sv90.values if hasattr(sv90, "values") else sv90, FEATURES, X_row.iloc[0], k=5)),
        "SHAP_Story_Risk30": story30,
        "SHAP_Story_Risk60": story60,
        "SHAP_Story_Risk90": story90,
        "Waterfall_Risk30_Path": wf30,
        "Waterfall_Risk60_Path": wf60,
        "Waterfall_Risk90_Path": wf90,
        "Recommended_Action": recommended
    }
    return result

# -----------------------------
# NEW PATIENT HELPERS
# -----------------------------
def build_features_for_new_patient(age: float, recent_visits_30: float, recent_visits_60: float, recent_visits_90: float, conditions_2010: dict):
    comorbidity_count_2010 = int(np.sum(list(conditions_2010.values())))
    new_comorbidities_2009 = 0
    new_comorbidities_2010 = 0
    persistent_conditions = 0
    sev = 0
    for k, v in conditions_2010.items():
        if v and k in SEVERITY_WEIGHTS_2010:
            sev += SEVERITY_WEIGHTS_2010[k]
    total_recent_visits = float(recent_visits_30 + recent_visits_60 + recent_visits_90)
    visit_ratio_30_to_90 = float(recent_visits_30 / recent_visits_90) if recent_visits_90 > 0 else 0.0
    feat = {
        "comorbidity_count_2010": comorbidity_count_2010,
        "new_comorbidities_2009": new_comorbidities_2009,
        "new_comorbidities_2010": new_comorbidities_2010,
        "persistent_conditions": persistent_conditions,
        "severity_score": sev,
        "total_recent_visits": total_recent_visits,
        "visit_ratio_30_to_90": visit_ratio_30_to_90,
    }
    if "AGE_2010" in FEATURES:
        feat["AGE_2010"] = age
    return pd.DataFrame([feat])[FEATURES]

def predict_for_new_patient(new_feat_df: pd.DataFrame):
    X_row = new_feat_df
    p30 = float(xgb30.predict(X_row)[0])
    p60 = float(xgb60.predict(X_row)[0])
    p90 = float(xgb90.predict(X_row)[0])
    ptier = int(xgbTier.predict(X_row)[0])

    sv30 = shap_explainer_30(X_row, check_additivity=False)[0]
    sv60 = shap_explainer_60(X_row, check_additivity=False)[0]
    sv90 = shap_explainer_90(X_row, check_additivity=False)[0]

    story30 = build_shap_story(sv30, FEATURES, X_row.iloc[0], "30-day")
    story60 = build_shap_story(sv60, FEATURES, X_row.iloc[0], "60-day")
    story90 = build_shap_story(sv90, FEATURES, X_row.iloc[0], "90-day")

    wf30 = make_waterfall(sv30, "NEWPATIENT", "Risk_30")
    wf60 = make_waterfall(sv60, "NEWPATIENT", "Risk_60")
    wf90 = make_waterfall(sv90, "NEWPATIENT", "Risk_90")

    recommended = "; ".join(TIER_ACTIONS.get(ptier, TIER_ACTIONS[0]))

    return {
        "Pred_Risk_30": round(p30,2),
        "Pred_Risk_60": round(p60,2),
        "Pred_Risk_90": round(p90,2),
        "Pred_Tier": int(ptier),
        "Top_Drivers_Risk30": " | ".join(top_shap_phrases(sv30.values if hasattr(sv30, "values") else sv30, FEATURES, X_row.iloc[0], k=5)),
        "Top_Drivers_Risk60": " | ".join(top_shap_phrases(sv60.values if hasattr(sv60, "values") else sv60, FEATURES, X_row.iloc[0], k=5)),
        "Top_Drivers_Risk90": " | ".join(top_shap_phrases(sv90.values if hasattr(sv90, "values") else sv90, FEATURES, X_row.iloc[0], k=5)),
        "SHAP_Story_Risk30": story30,
        "SHAP_Story_Risk60": story60,
        "SHAP_Story_Risk90": story90,
        "Waterfall_Risk30_Path": wf30,
        "Waterfall_Risk60_Path": wf60,
        "Waterfall_Risk90_Path": wf90,
        "Recommended_Action": recommended
    }

# -----------------------------
# SAVE MODELS & FEATURES
# -----------------------------
# -----------------------------
# SAVE MODELS & FEATURES (TEST MODELS)
# -----------------------------
joblib.dump(xgb30, os.path.join(ARTIFACT_DIR, "test_xgb_risk30.joblib"))
joblib.dump(xgb60, os.path.join(ARTIFACT_DIR, "test_xgb_risk60.joblib"))
joblib.dump(xgb90, os.path.join(ARTIFACT_DIR, "test_xgb_risk90.joblib"))
joblib.dump(xgbTier, os.path.join(ARTIFACT_DIR, "test_xgb_tier.joblib"))

with open(os.path.join(ARTIFACT_DIR, "test_features.json"), "w") as f:
    json.dump(FEATURES, f, indent=2)

print("✅ Saved TEST models and feature list to:", ARTIFACT_DIR)


# -----------------------------
# BATCH PREDICT & EXPORT
# -----------------------------
def batch_predict_export():
    preds = []
    for _, row in df.iterrows():
        bene = row[ID_COL]
        res = predict_and_explain_by_id(bene)
        preds.append(res)
    out_df = pd.DataFrame(preds)
    out_csv = os.path.join(ARTIFACT_DIR, "predictions_with_shap.csv")
    out_df.to_csv(out_csv, index=False)
    print("Saved:", out_csv)
    return out_csv

preds_path = batch_predict_export()

# -----------------------------
# DEMO: explain one known & a new patient
# -----------------------------
some_id = df[ID_COL].iloc[0]
demo = predict_and_explain_by_id(some_id)
print("Demo known member:", json.dumps(demo, indent=2))

new_features = build_features_for_new_patient(
    age=72,
    recent_visits_30=3,
    recent_visits_60=5,
    recent_visits_90=7,
    conditions_2010={
        "SP_CHF_2010": True,
        "SP_CHRNKIDN_2010": False,
        "SP_COPD_2010": True,
        "SP_DIABETES_2010": True,
        "SP_CNCR_2010": False,
        "SP_STRKETIA_2010": False,
        "SP_ALZHDMTA_2010": False,
        "SP_DEPRESSN_2010": True,
    }
)
new_pred = predict_for_new_patient(new_features)
print("Demo new patient:", json.dumps(new_pred, indent=2))
