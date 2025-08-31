# app.py
from flask import Flask, jsonify
from flask_cors import CORS
from retriever import get_patient_info   # <-- you must implement this
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # ✅ Allow cross-origin (for React)

# -----------------------------
# ROOT ROUTE
# -----------------------------
@app.route("/")
def home():
    return "✅ Care Management API running on port 5001. Use /patient/<id> to get insights."

# -----------------------------
# PATIENT INSIGHTS ROUTE
# -----------------------------
@app.route("/patient/<patient_id>", methods=["GET"])
def patient_info(patient_id):
    try:
        result = get_patient_info(patient_id)   # call retriever logic
        if not result:
            return jsonify({"error": f"No care insights found for ID {patient_id}"}), 404
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -----------------------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
