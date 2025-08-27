from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np
import joblib
import traceback
import shap
import os

# ------------------- CONFIG -------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SCALER_PATH = os.path.join(BASE_DIR, 'pipeline/models/scaler.pkl')
PCA_PATH = os.path.join(BASE_DIR, 'pipeline/models/pca.pkl')
EXPLAINER_PATH = os.path.join(BASE_DIR, 'pipeline/models/shap_explainer.pkl')
MODEL_30D_PATH = os.path.join(BASE_DIR, 'pipeline/models/kmeans_30d.pkl')
MODEL_60D_PATH = os.path.join(BASE_DIR, 'pipeline/models/kmeans_60d.pkl')
MODEL_90D_PATH = os.path.join(BASE_DIR, 'pipeline/models/kmeans_90d.pkl')

# ------------------- LOAD MODELS -------------------
scaler = joblib.load(SCALER_PATH)
pca = joblib.load(PCA_PATH)
explainer = joblib.load(EXPLAINER_PATH)
model_30d = joblib.load(MODEL_30D_PATH)
model_60d = joblib.load(MODEL_60D_PATH)
model_90d = joblib.load(MODEL_90D_PATH)

# Define Flask app
app = Flask(__name__)
CORS(app)

# ------------------- HELPER FUNCTIONS -------------------
def generate_member_risk_json(
    member_index: int,
    member_row: pd.Series,
    scaler,
    pca_model,
    shap_explainer,
    cluster_models: dict,
    cluster_features: dict
) -> dict:
    """
    Generates a risk JSON for a single member using clustering + SHAP.
    """
    # Step 1: PCA input
    features_pca = scaler.feature_names_in_.tolist()
    X_pca_input = pd.DataFrame([member_row])[features_pca].fillna(0)
    X_scaled = scaler.transform(X_pca_input)
    X_pca = pca_model.transform(X_scaled)

    # Step 2: Main 90-day cluster
    features_90d = cluster_features['90_day']
    X_90d_input = pd.DataFrame([member_row])[features_90d].fillna(0)
    cluster_main = int(cluster_models['90_day'].predict(X_90d_input)[0])

    # Step 3: Risk scores and tiers
    risk_scores = {}
    risk_tiers = {}
    for window, model in cluster_models.items():
        features = cluster_features[window]
        X_window = pd.DataFrame([member_row])[features].fillna(0)
        cluster_id = int(model.predict(X_window)[0])
        score = float(np.linalg.norm(model.cluster_centers_[cluster_id]))
        risk_scores[window] = round(score, 2)

        # Tier logic
        if score < 5:
            tier = 1
        elif score < 10:
            tier = 2
        elif score < 15:
            tier = 3
        elif score < 20:
            tier = 4
        else:
            tier = 5
        risk_tiers[window] = tier

    # Step 4: SHAP top 5 features
    shap_values = shap_explainer(X_pca_input)
    shap_dict = dict(sorted(
        zip(X_pca_input.columns, shap_values.values[0]),
        key=lambda x: abs(x[1]), reverse=True
    )[:5])
    shap_dict = {k: round(v, 3) for k, v in shap_dict.items()}

    # Step 5: Narrative
    narratives = {
        '30_day': "Acute utilization spike—likely inpatient or pharmacy driven.",
        '60_day': "Sustained multi-claim activity and diagnostic complexity.",
        '90_day': "Chronic burden and systemic fragmentation—long-term deterioration."
    }

    # Step 6: ROI logic
    tier_90 = risk_tiers['90_day']
    intervention_costs = {1: 0, 2: 100, 3: 300, 4: 500, 5: 1000}
    intervention_cost = intervention_costs[tier_90]
    expected_savings = round(risk_scores['90_day'] * member_row.get('total_spending', 0) * 0.2)
    eligible = expected_savings > intervention_cost
    recommended_action = "Care coordination + pharmacy review" if eligible else "Monitor only"

    return {
        "DESYNPUF_ID": member_row.get("DESYNPUF_ID", f"member_{member_index}"),
        "cluster": cluster_main,
        "risk_scores": risk_scores,
        "risk_tiers": risk_tiers,
        "narratives": narratives,
        "shap_top_features": shap_dict,
        "intervention_roi": {
            "eligible": eligible,
            "expected_savings": expected_savings,
            "recommended_action": recommended_action
        }
    }

# ------------------- API ROUTE -------------------
@app.route('/risk', methods=['POST'])
def risk():
    try:
        data = request.get_json()
        member_index = data.get('member_index', 0)
        member_features = data.get('features', {})

        # Convert input dict to Series
        member_row = pd.Series(member_features)

        # Cluster features mapping
        cluster_features_map = {
            '30_day': model_30d.feature_names_in_.tolist(),
            '60_day': model_60d.feature_names_in_.tolist(),
            '90_day': model_90d.feature_names_in_.tolist()
        }

        # Generate risk JSON
        risk_json = generate_member_risk_json(
            member_index=member_index,
            member_row=member_row,
            scaler=scaler,
            pca_model=pca,
            shap_explainer=explainer,
            cluster_models={
                '30_day': model_30d,
                '60_day': model_60d,
                '90_day': model_90d
            },
            cluster_features=cluster_features_map
        )
        return jsonify(risk_json)

    except Exception as e:
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500

# ------------------- RUN -------------------
if __name__ == '__main__':
    app.run(debug=True, port=5000)
