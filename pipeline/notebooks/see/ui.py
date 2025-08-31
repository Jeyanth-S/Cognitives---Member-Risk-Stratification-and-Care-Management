from flask import Flask, render_template, request, send_from_directory
import os
import json
import joblib
import pandas as pd
import numpy as np
import shap
import matplotlib
import duckdb
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# -----------------------------
# CONFIG
# -----------------------------
app = Flask(__name__)

ARTIFACT_DIR = r"C:\Users\kesh2\OneDrive\Documents\Cognitives---Member-Risk-Stratification-and-Care-Management\pipeline\notebooks\artifacts"
FIG_DIR = os.path.join(ARTIFACT_DIR, "figs_test")
os.makedirs(FIG_DIR, exist_ok=True)

# Load models
xgb30 = joblib.load(os.path.join(ARTIFACT_DIR, "test_xgb_risk30.joblib"))
xgb60 = joblib.load(os.path.join(ARTIFACT_DIR, "test_xgb_risk60.joblib"))
xgb90 = joblib.load(os.path.join(ARTIFACT_DIR, "test_xgb_risk90.joblib"))

# Features
with open(os.path.join(ARTIFACT_DIR, "test_features.json"), "r") as f:
    FEATURES = json.load(f)

# DuckDB path
DB_PATH = r"C:\Users\kesh2\OneDrive\Documents\Cognitives---Member-Risk-Stratification-and-Care-Management\pipeline\db\synpuf.duckdb"

# -----------------------------
# HELPERS
# -----------------------------
TIER_ACTIONS = {
    0: ["Routine screening", "Preventive reminders"],
    1: ["Preventive care follow-up", "Lifestyle coaching"],
    2: ["Outpatient follow-up", "Chronic disease coaching"],
    3: ["Care coordinator assignment", "Follow-up in 7 days", "Medication review"],
    4: ["Immediate intensive case management", "Specialist referral", "Home health assessment"],
}

def compute_tier(risk30, risk60, risk90):
    """5-level stratification."""
    avg_risk = (risk30 + risk60 + risk90) / 3
    if avg_risk <= 20:
        return 0
    elif avg_risk <= 40:
        return 1
    elif avg_risk <= 60:
        return 2
    elif avg_risk <= 80:
        return 3
    else:
        return 4

def engineer_features(df_raw):
    """Feature engineering from uploaded CSV."""
    disease_cols = [col for col in df_raw.columns if "SP_" in col]
    for col in disease_cols:
        df_raw[col] = df_raw[col].apply(lambda x: 1 if x == 1 else 0)

    disease_cols_2010 = [c for c in disease_cols if "_2010" in c]
    df_raw["comorbidity_count_2010"] = df_raw[disease_cols_2010].sum(axis=1) if disease_cols_2010 else 0

    disease_cols_2009 = [c for c in disease_cols if "_2009" in c]
    disease_cols_2008 = [c.replace("2009", "2008") for c in disease_cols_2009]
    if disease_cols_2009 and all(col in df_raw.columns for col in disease_cols_2008):
        diff_2009 = df_raw[disease_cols_2009].values - df_raw[disease_cols_2008].values
        df_raw["new_comorbidities_2009"] = np.clip(diff_2009, 0, None).sum(axis=1)
    else:
        df_raw["new_comorbidities_2009"] = 0

    if disease_cols_2010 and disease_cols_2009:
        diff_2010 = df_raw[disease_cols_2010].values - df_raw[disease_cols_2009].values
        df_raw["new_comorbidities_2010"] = np.clip(diff_2010, 0, None).sum(axis=1)
    else:
        df_raw["new_comorbidities_2010"] = 0

    if disease_cols_2009 and disease_cols_2010:
        df_raw["persistent_conditions"] = (
            (df_raw[disease_cols_2009].values + df_raw[disease_cols_2010].values) == 2
        ).sum(axis=1)
    else:
        df_raw["persistent_conditions"] = 0

    weights = {
        "SP_CHF_2010": 3, "SP_COPD_2010": 2, "SP_DIABETES_2010": 2,
        "SP_CNCR_2010": 2, "SP_DEPRESSN_2010": 1, "SP_STRKETIA_2010": 2,
        "SP_ALZHDMTA_2010": 2, "SP_CHRNKIDN_2010": 3
    }
    df_raw["severity_score"] = 0
    for col, w in weights.items():
        if col in df_raw.columns:
            df_raw["severity_score"] += df_raw[col] * w

    for v in ["recent_visits_30","recent_visits_60","recent_visits_90"]:
        if v not in df_raw.columns:
            df_raw[v] = 0

    df_raw["total_recent_visits"] = (
        df_raw["recent_visits_30"] + df_raw["recent_visits_60"] + df_raw["recent_visits_90"]
    )

    df_raw["visit_ratio_30_to_90"] = df_raw.apply(
        lambda x: x["recent_visits_30"] / x["recent_visits_90"] if x["recent_visits_90"] > 0 else 0,
        axis=1
    )

    return df_raw

def build_shap_story(shap_values, features, row, horizon_label):
    FRIENDLY = {
        "total_recent_visits": "Frequent visits (last 90 days)",
        "severity_score": "Overall severity of conditions",
        "comorbidity_count_2010": "Number of chronic conditions",
        "visit_ratio_30_to_90": "Concentration of visits (30/90 day ratio)",
        "new_comorbidities_2010": "New diagnoses in 2010",
        "new_comorbidities_2009": "New diagnoses in 2009",
        "persistent_conditions": "Persistent conditions",
        "AGE_2010": "Patient age"
    }

    vals = shap_values.values[0] if hasattr(shap_values, "values") else shap_values[0]
    top_idx = np.argsort(np.abs(vals))[-5:][::-1]

    phrases = []
    for i in top_idx:
        feat = features[i]
        fname = FRIENDLY.get(feat, feat.replace("_", " ").title())
        val = row[feat]
        if isinstance(val, float):
            val = round(val, 2)
        impact = "increases" if vals[i] > 0 else "decreases"
        phrases.append(f"{fname}: {val} → {impact} risk")

    return f"For {horizon_label}, main drivers are: " + "; ".join(phrases) + "."

def get_predictions(features, beneficiary_id=None, use_model=True):
    if use_model:
        X = pd.DataFrame([features], columns=FEATURES)
        risk30 = float(xgb30.predict(X)[0])
        risk60 = float(xgb60.predict(X)[0])
        risk90 = float(xgb90.predict(X)[0])
        tier = compute_tier(risk30, risk60, risk90)

        explainer = shap.TreeExplainer(xgb30)
        shap_values = explainer(X)
        story = build_shap_story(shap_values, FEATURES, X.iloc[0], "30-day risk")

        recommended = TIER_ACTIONS.get(tier, ["Routine care"])

        fig, ax = plt.subplots(figsize=(8, 6))
        shap.plots.bar(shap_values, show=False)
        shap_img_name = f"{beneficiary_id if beneficiary_id else 'new_patient'}_Risk30_shap.png"
        plt.savefig(os.path.join(FIG_DIR, shap_img_name), bbox_inches="tight")
        plt.close(fig)

    else:
        risk30 = features.get("Risk_30", 0)
        risk60 = features.get("Risk_60", 0)
        risk90 = features.get("Risk_90", 0)
        tier = features.get("Tier", compute_tier(risk30, risk60, risk90))

        X = pd.DataFrame([features], columns=FEATURES)
        explainer = shap.TreeExplainer(xgb30)
        shap_values = explainer(X)
        story = build_shap_story(shap_values, FEATURES, X.iloc[0], "30-day risk")

        recommended = TIER_ACTIONS.get(tier, ["Routine care"])

        shap_img_name = f"{features['DESYNPUF_ID']}_Risk30_shap.png"
        fig, ax = plt.subplots(figsize=(8, 6))
        shap.plots.bar(shap_values, show=False)
        plt.savefig(os.path.join(FIG_DIR, shap_img_name), bbox_inches="tight")
        plt.close(fig)

    return {
        "Risk_30": round(risk30, 2),
        "Risk_60": round(risk60, 2),
        "Risk_90": round(risk90, 2),
        "Tier": tier,
        "shap_img": shap_img_name,
        "story": story,
        "recommended": recommended,
    }

# -----------------------------
# ROUTES
# -----------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        mode = request.form.get("mode")

        with duckdb.connect(DB_PATH) as con:
            if mode == "existing":
                beneficiary_id = request.form.get("beneficiary_id")
                row = con.execute(f"SELECT * FROM beneficiary_with_labels WHERE DESYNPUF_ID='{beneficiary_id}'").df()
                if row.empty:
                    return render_template("index.html", error="Beneficiary ID not found")
                features = row.iloc[0].to_dict()
                result = get_predictions(features, beneficiary_id, use_model=False)

            else:  # new patient
                uploaded_file = request.files.get("patient_csv")
                if not uploaded_file:
                    return render_template("index.html", error="Please upload a CSV file with patient data")
                try:
                    df_new = pd.read_csv(uploaded_file)
                    bene_id = df_new["DESYNPUF_ID"].iloc[0]

                    # ✅ If ID already exists in labels → skip re-insert
                    check = con.execute(f"SELECT * FROM beneficiary_with_labels WHERE DESYNPUF_ID='{bene_id}'").df()
                    if not check.empty:
                        return render_template("index.html", error=f"User {bene_id} already exists in database")

                    # Engineer features + predict
                    df_new = engineer_features(df_new)
                    new_row = df_new.iloc[0].to_dict()
                    features = {col: new_row.get(col, 0) for col in FEATURES}
                    result = get_predictions(features, beneficiary_id=None, use_model=True)

                    # ✅ Insert only engineered + predicted row into labels
                    out_df = pd.DataFrame([{**new_row, **result, "DESYNPUF_ID": bene_id}])
                    con.register("out_df", out_df)
                    con.execute("INSERT INTO beneficiary_with_labels SELECT * FROM out_df")

                except Exception as e:
                    return render_template("index.html", error=f"Error processing file: {str(e)}")

        return render_template("result.html", result=result)

    return render_template("index.html")

@app.route("/figs/<filename>")
def send_shap(filename):
    return send_from_directory(FIG_DIR, filename)

# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)
