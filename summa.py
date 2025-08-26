from flask import Flask, request, jsonify, send_file
from flask_cors import CORS  # <-- Add CORS
import joblib
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Must be set before importing pyplot
import matplotlib.pyplot as plt
import numpy as np
import io
import sys
import os

# 🔹 Setup
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from risk_engine import generate_member_risk_json  # Your core logic

app = Flask(__name__)
CORS(app)  # <-- Enable CORS for all routes

# 🔹 Load models
scaler = joblib.load('./pipeline/models/scaler.pkl')
pca = joblib.load('./pipeline/models/pca_model.pkl')
explainer = joblib.load('./pipeline/models/shap_explainer.pkl')
model_30d = joblib.load('./pipeline/models/kmeans_30d.pkl')
model_60d = joblib.load('./pipeline/models/kmeans_60d.pkl')
model_90d = joblib.load('./pipeline/models/kmeans_90d.pkl')

# 🔹 Load member data (used for plotting endpoints)
df = pd.read_parquet('./pipeline/features/ml_features.parquet')

# 🔹 Feature sets
features_30d_kmeans = model_30d.feature_names_in_.tolist()
features_60d_kmeans = model_60d.feature_names_in_.tolist()
features_90d_kmeans = model_90d.feature_names_in_.tolist()


# 🔹 Helper functions
def get_kmeans_risk(model, input_scaled):
    distances = model.transform(input_scaled)[0]
    min_dist = np.min(distances)
    max_dist = np.max(distances)
    risk_score = (min_dist - distances.min()) / (distances.max() - distances.min() + 1e-6)
    return round(risk_score, 3)


def explain_risk_drift(shap_values, feature_names):
    top_indices = np.argsort(np.abs(shap_values))[::-1][:3]
    drivers = [(feature_names[i], shap_values[i]) for i in top_indices]

    summary = []
    for feat, val in drivers:
        direction = "increased" if val > 0 else "reduced"
        summary.append(f"{feat} has {direction} risk contribution ({val:.2f})")

    return " | ".join(summary)


def plot_shap_summary(shap_values, feature_names):
    plt.figure(figsize=(6, 4))
    colors = ['crimson' if val > 0 else 'navy' for val in shap_values]
    plt.barh(feature_names, shap_values, color=colors)
    plt.xlabel("SHAP Value")
    plt.title("Top SHAP Drivers")
    plt.axvline(0, color='gray', linestyle='--', linewidth=1)
    plt.grid(True, axis='x', linestyle=':', alpha=0.5)
    plt.tight_layout(pad=2)

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close()
    return buf


def plot_risk_drift(risk_scores):
    windows = ['30d', '60d', '90d']
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(windows, risk_scores, marker='o', color='teal', linewidth=2)
    ax.set_title("Risk Drift Over Time")
    ax.set_ylabel("Risk Score")
    ax.set_ylim(0, 1)
    ax.grid(True, linestyle=':', alpha=0.5)
    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)
    return buf


# 🔹 Risk JSON endpoint
@app.route('/risk', methods=['POST'])
def get_risk_json():
    try:
        member_data = request.get_json()
        member_index = member_data.get("member_index", 0)
        member_row = pd.Series(member_data["features"])

        result = generate_member_risk_json(
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
            cluster_features={
                '30_day': features_30d_kmeans,
                '60_day': features_60d_kmeans,
                '90_day': features_90d_kmeans
            }
        )

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 🔹 SHAP plot endpoint
@app.route("/plot/shap/<int:member_index>")
def shap_plot(member_index):
    try:
        member_row = df.iloc[member_index]
        input_df = pd.DataFrame([member_row])[scaler.feature_names_in_].fillna(0)
        input_scaled = scaler.transform(input_df)
        shap_values = explainer.shap_values(input_scaled)[0]
        top_indices = np.argsort(np.abs(shap_values))[::-1][:5]
        top_features = [scaler.feature_names_in_[i] for i in top_indices]
        top_scores = [shap_values[i] for i in top_indices]
        buf = plot_shap_summary(top_scores, top_features)
        return send_file(buf, mimetype='image/png')
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/plot/risk/<int:member_index>")
def risk_drift_plot(member_index):
    try:
        member_row = df.iloc[member_index]

        input_30 = pd.DataFrame([member_row])[features_30d_kmeans].fillna(0)
        input_60 = pd.DataFrame([member_row])[features_60d_kmeans].fillna(0)
        input_90 = pd.DataFrame([member_row])[features_90d_kmeans].fillna(0)

        input_30_scaled = scaler.transform(input_30)
        input_60_scaled = scaler.transform(input_60)
        input_90_scaled = scaler.transform(input_90)

        risk_30 = get_kmeans_risk(model_30d, input_30_scaled)
        risk_60 = get_kmeans_risk(model_60d, input_60_scaled)
        risk_90 = get_kmeans_risk(model_90d, input_90_scaled)

        buf = plot_risk_drift([risk_30, risk_60, risk_90])
        return send_file(buf, mimetype='image/png')
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/explain/risk/<int:member_index>")
def explain_risk(member_index):
    try:
        member_row = df.iloc[member_index]
        input_df = pd.DataFrame([member_row])[scaler.feature_names_in_].fillna(0)
        input_scaled = scaler.transform(input_df)
        shap_values = explainer.shap_values(input_scaled)[0]
        summary = explain_risk_drift(shap_values, scaler.feature_names_in_)
        return jsonify({"explanation": summary})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 🔹 Run app
if __name__ == '__main__':
    app.run(debug=True, port=5000)  # <-- Specify port explicitly
