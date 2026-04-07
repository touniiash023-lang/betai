from math import exp, factorial

def poisson_prob(lmbda, k):
    return (exp(-lmbda) * (lmbda ** k)) / factorial(k)

def predict_match(home, away, home_stats=None, away_stats=None):
    home_stats = home_stats or {
        "avg_scored": 1.85,
        "avg_conceded": 0.95,
        "form": 1.08
    }
    away_stats = away_stats or {
        "avg_scored": 1.25,
        "avg_conceded": 1.35,
        "form": 0.96
    }

    league_home_avg = 1.45
    league_away_avg = 1.15
    league_avg = 1.30

    home_attack_strength = home_stats["avg_scored"] / league_avg
    home_defense_strength = home_stats["avg_conceded"] / league_avg
    away_attack_strength = away_stats["avg_scored"] / league_avg
    away_defense_strength = away_stats["avg_conceded"] / league_avg

    lambda_home = league_home_avg * home_attack_strength * away_defense_strength * home_stats["form"]
    lambda_away = league_away_avg * away_attack_strength * home_defense_strength * away_stats["form"]

    max_goals = 5
    home_win = 0.0
    draw = 0.0
    away_win = 0.0
    btts_yes = 0.0
    over_25 = 0.0

    best_score = "0-0"
    best_prob = 0.0

    for h in range(max_goals + 1):
        for a in range(max_goals + 1):
            p = poisson_prob(lambda_home, h) * poisson_prob(lambda_away, a)

            if p > best_prob:
                best_prob = p
                best_score = f"{h}-{a}"

            if h > a:
                home_win += p
            elif h == a:
                draw += p
            else:
                away_win += p

            if h > 0 and a > 0:
                btts_yes += p

            if h + a >= 3:
                over_25 += p

    btts_no = 1 - btts_yes
    under_25 = 1 - over_25

    if home_win >= draw and home_win >= away_win:
        winner = home
        market = "1"
    elif away_win >= draw and away_win >= home_win:
        winner = away
        market = "2"
    else:
        winner = "Match nul"
        market = "X"

    return {
        "sport": "football",
        "match": f"{home} vs {away}",
        "winner": winner,
        "prediction_1x2": market,
        "home_win": round(home_win * 100, 2),
        "draw": round(draw * 100, 2),
        "away_win": round(away_win * 100, 2),
        "home_goals_expected": round(lambda_home, 2),
        "away_goals_expected": round(lambda_away, 2),
        "btts_yes": round(btts_yes * 100, 2),
        "btts_no": round(btts_no * 100, 2),
        "over_2_5": round(over_25 * 100, 2),
        "under_2_5": round(under_25 * 100, 2),
        "score_prediction": best_score,
        "confidence": round(max(home_win, draw, away_win) * 100, 2),
        "recent_history": [
            {"team": home, "result": "W", "score": "2-0"},
            {"team": home, "result": "D", "score": "1-1"},
            {"team": away, "result": "L", "score": "0-2"},
            {"team": away, "result": "W", "score": "2-1"}
        ]
    }