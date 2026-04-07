from flask import Flask, request, jsonify
from flask_cors import CORS
from football_ai import predict_match

app = Flask(_name_)
CORS(app)

@app.route("/")
def home():
    return jsonify({
        "message": "BetAI Analytics API is running",
        "routes": ["/predict", "/demo"]
    })

@app.route("/demo")
def demo():
    return jsonify({
        "football": predict_match("Real Madrid", "Sevilla")
    })

@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json(force=True)

    sport = data.get("sport", "football").strip().lower()
    home = data.get("home", "").strip()
    away = data.get("away", "").strip()

    if not home or not away:
        return jsonify({"error": "home and away are required"}), 400

    if sport != "football":
        return jsonify({"error": "only football is enabled in this version"}), 400

    result = predict_match(home, away)
    return jsonify(result)

if _name_ == "_main_":
    app.run(host="0.0.0.0", port=5000, debug=True)
