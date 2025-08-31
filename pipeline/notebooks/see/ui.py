from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import json
import joblib
import pandas as pd
import numpy as np
import shap
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# -----------------------------
# CONFIG
# -----------------------------
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

ARTIFACT_DIR = r"/media/jeyanth-s/DevDrive/AI_Workspace/projects/Cognitives---Member-Risk-Stratification-and-Care-Management/pipeline/notebooks/artifacts"
FIG_DIR = os.path.join(ARTIFACT_DIR, "figs")
os.makedirs(FIG_DIR, exist_ok=True)

# Models
xgb30 = joblib.load(os.path.join(ARTIFACT_DIR, "test_xgb_risk30.joblib"))
xgb60 = joblib.load(os.path.join(ARTIFACT_DIR, "test_xgb_risk60.joblib"))
xgb90 = joblib.load(os.path.join(ARTIFACT_DIR, "test_xgb_risk90.joblib"))

# Feature list
with open(os.path.join(ARTIFACT_DIR, "test_features.json"), "r") as f:
    FEATURES = json.load(f)

# Existing patients
DATA_PATH = os.path.join(ARTIFACT_DIR, "../../../beneficiary_with_labels.csv") # os.path.join(ARTIFACT_DIR, ".", "beneficiary_with_labels.csv")
DATA_PATH = os.path.abspath(DATA_PATH)
if os.path.exists(DATA_PATH):
    df_existing = pd.read_csv(DATA_PATH)
else:
    df_existing = pd.DataFrame()

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

FRIENDLY_NAMES = {
    "total_recent_visits": "Frequent visits (last 90 days)",
    "severity_score": "Overall severity of conditions",
    "comorbidity_count_2010": "Number of chronic conditions",
    "visit_ratio_30_to_90": "Concentration of visits (30/90 day ratio)",
    "new_comorbidities_2010": "New diagnoses in 2010",
    "new_comorbidities_2009": "New diagnoses in 2009",
    "persistent_conditions": "Persistent conditions",
    "AGE_2010": "Patient age"
}

def compute_tier(risk30, risk60, risk90):
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

def build_story(shap_values, features, row):
    vals = shap_values.values[0] if hasattr(shap_values, "values") else shap_values[0]
    top_idx = np.argsort(np.abs(vals))[-5:][::-1]
    phrases = []
    for i in top_idx:
        feat = features[i]
        fname = FRIENDLY_NAMES.get(feat, feat.replace("_", " ").title())
        val = row[feat]
        impact = "increases" if vals[i] > 0 else "decreases"
        phrases.append(f"{fname} ({val}) → {impact} risk")
    return "Key drivers: " + "; ".join(phrases)

def compute_story_and_recommendations(X, bene_id, risks, tier):
    explainer = shap.TreeExplainer(xgb30)
    shap_values = explainer(X)

    # Save SHAP bar plot
    shap_img_name = f"{bene_id}_Risk30_shap.png"
    fig, ax = plt.subplots(figsize=(8, 6))
    shap.plots.bar(shap_values, show=False)
    plt.savefig(os.path.join(FIG_DIR, shap_img_name), bbox_inches="tight")
    plt.close(fig)

    story = build_story(shap_values, FEATURES, X.iloc[0])
    return story, TIER_ACTIONS.get(tier, ["Routine care"]), shap_img_name

def get_predictions(features, bene_id="new_patient"):
    X = pd.DataFrame([features], columns=FEATURES)
    risk30 = float(xgb30.predict(X)[0])
    risk60 = float(xgb60.predict(X)[0])
    risk90 = float(xgb90.predict(X)[0])
    tier = compute_tier(risk30, risk60, risk90)

    story, recs, shap_img = compute_story_and_recommendations(X, bene_id, (risk30, risk60, risk90), tier)

    return {
        "DESYNPUF_ID": bene_id,
        "Risk_30": round(risk30, 2),
        "Risk_60": round(risk60, 2),
        "Risk_90": round(risk90, 2),
        "Tier": tier,
        "shap_img": shap_img,
        "story": story,
        "recommended": recs,
    }


@app.route("/predict", methods=["POST"])
def predict():
    global df_existing

    # Existing user
    if request.is_json:
        data = request.get_json()
        if "beneficiary_id" in data:
            bene_id = data["beneficiary_id"]
            row = df_existing[df_existing["DESYNPUF_ID"] == bene_id]
            if row.empty:
                return jsonify({"error": "Beneficiary ID not found"}), 404

            features = {col: row.iloc[0].get(col, 0) for col in FEATURES}
            risks = (
                row.iloc[0].get("Risk_30", 0),
                row.iloc[0].get("Risk_60", 0),
                row.iloc[0].get("Risk_90", 0),
            )
            tier = int(row.iloc[0].get("Tier", compute_tier(*risks)))

            X = pd.DataFrame([features], columns=FEATURES)
            story, recs, shap_img = compute_story_and_recommendations(X, bene_id, risks, tier)

            result = {
                "DESYNPUF_ID": bene_id,
                "Risk_30": risks[0],
                "Risk_60": risks[1],
                "Risk_90": risks[2],
                "Tier": tier,
                "shap_img": shap_img,
                "story": story,
                "recommended": recs,
            }
            return jsonify(result)

    # New user
    if "patient_csv" in request.files:
        try:
            uploaded_file = request.files["patient_csv"]
            df_new = pd.read_csv(uploaded_file)
            df_new = engineer_features(df_new)
            new_row = df_new.iloc[0].to_dict()
            features = {col: new_row.get(col, 0) for col in FEATURES}
            bene_id = new_row.get("DESYNPUF_ID", "new_patient")

            result = get_predictions(features, bene_id)

            df_new_out = pd.DataFrame([{**new_row, **result}])
            if not df_existing.empty and bene_id in df_existing["DESYNPUF_ID"].values:
                df_existing.loc[df_existing["DESYNPUF_ID"] == bene_id] = df_new_out.iloc[0]
            else:
                df_existing = pd.concat([df_existing, df_new_out], ignore_index=True)
            df_existing.to_csv(DATA_PATH, index=False)

            return jsonify(result)
        except Exception as e:
            return jsonify({"error": f"Error processing CSV: {str(e)}"}), 400

    return jsonify({"error": "Invalid request, provide beneficiary_id or patient_csv"}), 400

@app.route("/figs/<filename>")
def send_shap(filename):
    return send_from_directory(FIG_DIR, filename)

@app.route("/recency/<beneficiary_id>", methods=["GET"])
def get_beneficiary_recency(beneficiary_id):
    """
    Returns the row for the given beneficiary_id from beneficiary_with_recency.csv
    """
    recency_path = os.path.join(ARTIFACT_DIR, "../beneficiary_with_recency.csv")
    recency_path = os.path.abspath(recency_path)
    if not os.path.exists(recency_path):
        return jsonify({"error": "beneficiary_with_recency.csv not found"}), 404

    try:
        df_recency = pd.read_csv(recency_path)
        row = df_recency[df_recency["DESYNPUF_ID"] == beneficiary_id]
        print(row)
        if row.empty:
            return jsonify({"error": "Beneficiary ID not found"}), 404
        return jsonify(row.iloc[0].to_dict())
    except Exception as e:
        return jsonify({"error": f"Error reading recency file: {str(e)}"}), 500

# -----------------------------
if __name__ == "__main__":
    app.run(debug=True, port=5000)
