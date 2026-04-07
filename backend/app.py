from flask import Flask, jsonify
from flask_cors import CORS
import random

app = Flask(__name__)
CORS(app)

# Fonction IA simple
def analyze_match(home, away):
    home_form = random.uniform(0.8, 1.4)
    away_form = random.uniform(0.8, 1.4)

    # avantage domicile
    home_form += 0.25

    home_attack = random.uniform(1.0, 2.5) * home_form
    away_attack = random.uniform(0.8, 2.2) * away_form

    home_defense = random.uniform(0.5, 1.5)
    away_defense = random.uniform(0.5, 1.5)

    home_power = home_attack - (away_defense * 0.7)
    away_power = away_attack - (home_defense * 0.7)

    home_power = max(home_power, 0.1)
    away_power = max(away_power, 0.1)

    total = home_power + away_power

    home_prob = round((home_power / total) * 100)
    away_prob = round((away_power / total) * 100)
    draw_prob = 100 - home_prob - away_prob

    prediction = "home_win" if home_prob > away_prob else "away_win"

    return {
        "match": f"{home} vs {away}",
        "prediction": prediction,
        "probabilities": {
            "home_win": home_prob,
            "draw": draw_prob,
            "away_win": away_prob
        }
    }

@app.route("/")
def home():
    return "API BETAI OK"

@app.route("/api/predictions")
def predictions():
    matches = [
        ("RB Bragantino", "CR Flamengo"),
        ("SE Palmeiras", "Gremio"),
        ("Middlesbrough FC", "Millwall FC"),
        ("Birmingham City", "Blackburn Rovers"),
        ("Sheffield United", "Swansea City")
    ]

    results = [analyze_match(home, away) for home, away in matches]
    return jsonify(results)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)