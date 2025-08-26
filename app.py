from flask import Flask, jsonify
from retriever import get_patient_info   # <-- make sure this file exists
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Root route to check server is running
@app.route("/")
def home():
    return "✅ Flask server is running! Use /patient/<id> to get patient info."

# Patient info route
@app.route("/patient/<patient_id>", methods=["GET"])
def patient_info(patient_id):
    try:
        result = get_patient_info(patient_id)  # Your retriever logic
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)

