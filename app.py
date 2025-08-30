# # # app.py
# # from flask import Flask, request, jsonify
# # from retriever import retrieve_similar


# # app = Flask(__name__)

# # @app.route("/ask", methods=["POST"])
# # def ask():
# #     data = request.get_json()
# #     query = data.get("query", "")

# #     if not query:
# #         return jsonify({"error": "Query is required"}), 400

# #     suggestions = retrieve_similar(query, top_k=3)

# #     return jsonify({
# #         "query": query,
# #         "suggestions": suggestions
# #     })

# # if __name__ == "__main__":
# #     app.run(host="0.0.0.0", port=5000, debug=True)
from flask import Flask, jsonify
from retriever import get_patient_info
import os

app = Flask(__name__)
# CORS(app)

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

