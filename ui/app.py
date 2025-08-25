from flask import Flask, render_template, request, redirect, url_for, session
import duckdb
import joblib
import shap
import numpy as np
import pandas as pd

# ------------------- CONFIG -------------------
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # ⚠️ Change this in production

# Dummy users (replace with DB + hashing later)
users = {'caremanager': 'password123', 'admin': 'adminpass'}

# DuckDB (⚠️ update this path to your actual .duckdb file)
con = duckdb.connect(
    r"C:\Users\kesh2\OneDrive\Documents\Cognitives---Member-Risk-Stratification-and-Care-Management\pipeline\db\synpuf.duckdb",
    read_only=True
)

# Parquet paths
MAIN_PATH = r"C:\Users\kesh2\OneDrive\Documents\Cognitives---Member-Risk-Stratification-and-Care-Management\pipeline\features\ml_features.parquet"
CHRONIC_PATH = r"C:\Users\kesh2\OneDrive\Documents\Cognitives---Member-Risk-Stratification-and-Care-Management\pipeline\notebooks\combined_features_2010.parquet"

# Load parquet data once (keep in memory for fast lookup)
try:
    ml_features_df = pd.read_parquet(MAIN_PATH)
    chronic_features_df = pd.read_parquet(CHRONIC_PATH)
    # Merge if both contain DESYNPUF_ID
    if "DESYNPUF_ID" in ml_features_df.columns and "DESYNPUF_ID" in chronic_features_df.columns:
        merged_features_df = pd.merge(
            ml_features_df, chronic_features_df,
            on="DESYNPUF_ID", how="left"
        )
    else:
        merged_features_df = ml_features_df.copy()
except Exception as e:
    print("⚠️ Failed to load Parquet features:", e)
    merged_features_df = pd.DataFrame()

# Columns to display
COLUMNS = [
    "DESYNPUF_ID", "BENE_BIRTH_DT",
    "SP_ALZHDMTA", "SP_CHF", "SP_CHRNKIDN", "SP_CNCR", "SP_COPD",
    "SP_DEPRESSN", "SP_DIABETES", "SP_ISCHMCHT", "SP_OSTEOPRS",
    "SP_RA_OA", "SP_STRKETIA",
    "chronic_count_2008", "chronic_count_2009", "chronic_count_2010",
    "total_visits", "total_amount"
]

# ------------------- MODELS -------------------
model_30d = joblib.load("model_30d.pkl")
model_60d = joblib.load("model_60d.pkl")
model_90d = joblib.load("model_90d.pkl")

tier_map = {0: "Very Low", 1: "Low", 2: "Medium", 3: "High", 4: "Very High"}

features_30 = ["AGE", "chronic_count_2010", "chronic_trend", "total_visits",
               "spend_per_visit", "log_avg_claim"]

features_60 = ["AGE", "chronic_count_2010", "chronic_sum", "total_visits",
               "log_total_amount", "log_avg_claim", "visits_per_chronic"]

features_90 = ["AGE", "chronic_sum", "total_visits", "log_total_amount",
               "spend_per_visit"]

# ------------------- UTILS -------------------
def shap_story(model, X, feature_names):
    """Generate a story-like narrative from SHAP values"""
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)

    if isinstance(shap_values, list):
        pred_class = int(model.predict(X)[0])
        shap_vals = shap_values[pred_class][0]
    else:
        shap_vals = shap_values[0]

    shap_vals = np.array(shap_vals).flatten().tolist()
    feat_vals = np.array(X.iloc[0].values).flatten().tolist()

    data = []
    for f, s, v in zip(feature_names, shap_vals, feat_vals):
        data.append({
            "feature": f,
            "shap_value": float(s),
            "feature_value": float(v)
        })

    shap_df = pd.DataFrame(data)
    shap_df["abs_shap"] = shap_df["shap_value"].abs()
    shap_df = shap_df.sort_values(by="abs_shap", ascending=False).head(5)

    feature_map = {
        "AGE": "Patient's age",
        "chronic_sum": "Total number of chronic conditions (2008–2010)",
        "chronic_count_2010": "Chronic conditions in 2010",
        "chronic_trend": "Change in chronic conditions over years",
        "total_visits": "Number of healthcare visits",
        "spend_per_visit": "Average cost per visit",
        "log_total_amount": "Total spending (log-transformed)",
        "log_avg_claim": "Average claim amount (log-transformed)",
        "visits_per_chronic": "Visits per chronic condition"
    }

    story_lines = []
    for _, row in shap_df.iterrows():
        f = feature_map.get(row["feature"], row["feature"])
        s = row["shap_value"]
        v = row["feature_value"]
        effect = "increased" if s > 0 else "reduced"
        story_lines.append(f"- **{f}** (value: {round(v,2)}) {effect} the predicted risk (impact {round(s,3)}).")

    explanation = (
        "### Patient Risk Explanation (90 Days)\n"
        "The prediction is mainly influenced by the following medical factors:\n\n"
        + "\n".join(story_lines) +
        "\n\nTogether, these factors shape the overall risk tier for the patient."
    )
    return explanation


# ------------------- ROUTES -------------------
@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return redirect(url_for('home'))


# LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return redirect(url_for('home'))

    error = None
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        if username in users and users[username] == password:
            session['logged_in'] = True
            session['user'] = username
            return redirect(url_for('home'))
        else:
            error = "Invalid username or password."

    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# HOME
@app.route('/home')
def home():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('home.html', user=session.get('user'))


# MEMBERS
@app.route('/members')
def members():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    bene_id = request.args.get("bene_id", "").strip()
    page = int(request.args.get("page", 1))
    per_page = 20
    offset = (page - 1) * per_page

    if bene_id:
        # First try from DuckDB
        query = f"""
            SELECT {",".join(COLUMNS)}
            FROM combined_features
            WHERE DESYNPUF_ID = '{bene_id}'
            LIMIT 1
        """
        rows = con.execute(query).fetchdf().to_dict(orient="records")

        # If not found in DB, fallback to Parquet
        if not rows and not merged_features_df.empty:
            rows = merged_features_df[merged_features_df["DESYNPUF_ID"] == bene_id]
            rows = rows[COLUMNS].to_dict(orient="records")

        total_pages = 1
    else:
        query = f"""
            SELECT {",".join(COLUMNS)}
            FROM combined_features
            LIMIT {per_page} OFFSET {offset}
        """
        rows = con.execute(query).fetchdf().to_dict(orient="records")

        total_count = con.execute("SELECT COUNT(*) FROM combined_features").fetchone()[0]
        total_pages = (total_count // per_page) + (1 if total_count % per_page else 0)

    return render_template(
        "member_data.html",
        columns=COLUMNS,
        rows=rows,
        page=page,
        total_pages=total_pages,
        bene_id=bene_id
    )


# PREDICT
@app.route('/predict', methods=["GET", "POST"])
def predict():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    prediction, shap_text = None, None

    if request.method == "POST":
        bene_id = request.form["bene_id"].strip()

        # Try DuckDB first
        query = f"SELECT * FROM combined_features WHERE DESYNPUF_ID = '{bene_id}' LIMIT 1"
        row = con.execute(query).fetchdf()

        # If not found, fallback to Parquet
        if row.empty and not merged_features_df.empty:
            row = merged_features_df[merged_features_df["DESYNPUF_ID"] == bene_id]

        if row.empty:
            prediction = {"error": f"Beneficiary ID {bene_id} not found in DB or Parquet."}
        else:
            row = row.iloc[[0]].copy()

            # Feature engineering
            row["AGE"] = 2010 - pd.to_datetime(row["BENE_BIRTH_DT"]).dt.year
            row["chronic_trend"] = row["chronic_count_2010"].fillna(0) - row["chronic_count_2008"].fillna(0)
            row["chronic_sum"] = (
                row["chronic_count_2008"].fillna(0)
                + row["chronic_count_2009"].fillna(0)
                + row["chronic_count_2010"].fillna(0)
            )

            row["spend_per_visit"] = row["total_amount"] / (row["total_visits"].iloc[0] if row["total_visits"].iloc[0] > 0 else 1)
            row["log_total_amount"] = np.log1p(row["total_amount"])
            row["log_avg_claim"] = np.log1p(row["total_amount"] / (row["total_visits"].iloc[0] if row["total_visits"].iloc[0] > 0 else 1))
            row["visits_per_chronic"] = row["total_visits"] / (1 + row["chronic_count_2010"].fillna(0))

            # Extract features
            X30 = row[features_30]
            X60 = row[features_60]
            X90 = row[features_90]

            # Predictions
            pred_30 = tier_map[int(model_30d.predict(X30)[0])]
            pred_60 = tier_map[int(model_60d.predict(X60)[0])]
            pred_90 = tier_map[int(model_90d.predict(X90)[0])]

            prediction = {"30d": pred_30, "60d": pred_60, "90d": pred_90}

            # Narrative for 90d
            shap_text = shap_story(model_90d, X90, features_90)

    return render_template("predict.html", prediction=prediction, shap_text=shap_text)


# ------------------- RUN -------------------
if __name__ == "__main__":
    app.run(debug=True)
