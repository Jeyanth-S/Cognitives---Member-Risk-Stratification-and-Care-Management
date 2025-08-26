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


from flask import Flask, request, jsonify
from retriever import get_patient_info

app = Flask(__name__)

@app.route("/patient/<patient_id>", methods=["GET"])
def patient_info(patient_id):
    result = get_patient_info(patient_id)
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
