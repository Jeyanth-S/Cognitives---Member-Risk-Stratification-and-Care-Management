import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

def generate_member_risk_json(
    member_index: int,
    member_row: pd.Series,
    scaler: StandardScaler,
    pca_model,
    shap_explainer,
    cluster_models: dict,
    cluster_features: dict
) -> dict:
    """
    Generates a risk JSON for a single member using unsupervised clustering and SHAP explanations.
    """

    # Step 1: Prepare inputs for PCA + SHAP
    features_pca = scaler.feature_names_in_.tolist()
    X_pca_input = pd.DataFrame([member_row])[features_pca].fillna(0)
    X_scaled = scaler.transform(X_pca_input)
    # X_pca = pca_model.transform(X_scaled)

    # Step 2: Assign anchor cluster from 90-day model
    features_90d = cluster_features['90_day']
    X_90d_input = pd.DataFrame([member_row])[features_90d].fillna(0)
    cluster_main = int(cluster_models['90_day'].predict(X_90d_input)[0])

    # Step 3: Window-wise member-to-centroid scoring
    raw_scores = {}
    for window, model in cluster_models.items():
        features = cluster_features[window]
        X_window = pd.DataFrame([member_row])[features].fillna(0)
        cluster_id = int(model.predict(X_window)[0])
        centroid = model.cluster_centers_[cluster_id]
        score = float(np.linalg.norm(X_window.values[0] - centroid))
        raw_scores[window] = round(score, 4)

    # Step 4: Normalize scores and assign tiers
    min_score = min(raw_scores.values())
    max_score = max(raw_scores.values())
    risk_scores = {}
    risk_tiers = {}
    for window, score in raw_scores.items():
        norm_score = (score - min_score) / (max_score - min_score + 1e-6) * 20
        risk_scores[window] = round(norm_score, 2)
        if norm_score < 5:
            tier = 1
        elif norm_score < 10:
            tier = 2
        elif norm_score < 15:
            tier = 3
        elif norm_score < 20:
            tier = 4
        else:
            tier = 5
        risk_tiers[window] = tier

    # Step 5: Sort tiers and identify extremes
    sorted_tiers = dict(sorted(risk_tiers.items(), key=lambda x: x[1]))
    highest_risk = max(risk_tiers.items(), key=lambda x: x[1])
    lowest_risk = min(risk_tiers.items(), key=lambda x: x[1])

    # Step 6: SHAP top features
    shap_values = shap_explainer(X_pca_input)
    shap_dict = dict(sorted(
        zip(X_pca_input.columns, shap_values.values[0]),
        key=lambda x: abs(x[1]), reverse=True
    )[:5])
    shap_dict = {k: round(v, 3) for k, v in shap_dict.items()}

    # Step 7: Narrative generation
    narratives = {
        '30_day': "Acute utilization spike—likely inpatient or pharmacy driven.",
        '60_day': "Sustained multi-claim activity and diagnostic complexity.",
        '90_day': "Chronic burden and systemic fragmentation—long-term deterioration."
    }

    # Step 8: ROI logic
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
        "sorted_tiers": sorted_tiers,
        "highest_risk_window": highest_risk[0],
        "lowest_risk_window": lowest_risk[0],
        "narratives": narratives,
        "shap_top_features": shap_dict,
        "intervention_roi": {
            "eligible": eligible,
            "expected_savings": expected_savings,
            "recommended_action": recommended_action
        }
    }
