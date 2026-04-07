from flask import Flask, request, jsonify
from flask_cors import CORS
from football_ai import predict_match

app = Flask(_name_)
CORS(app)

# ✅ Route test
@app.route("/")
def home():
    return "API BETAI OK"

# ✅ DEMO (IMPORTANT)
@app.route("/demo")
def demo():
    return jsonify({
        "match": "Real Madrid vs Barcelona",
        "winner": "Real Madrid",
        "probability": "65%",
        "score": "2-1",
        "btts": "Yes"
    })

# ✅ PREDICT (LE BOUTON UTILISE ÇA)
@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()

    home = data.get("home")
    away = data.get("away")

    if not home or not away:
        return jsonify({"error": "Missing teams"}), 400

    result = predict_match(home, away)

    return jsonify(result)

# ✅ RUN
if _name_ == "_main_":
    app.run(host="0.0.0.0", port=10000)