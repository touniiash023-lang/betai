from typing import Dict, List


def clamp(value, low, high):
    return max(low, min(high, value))


def normalize_2way(a, b):
    total = a + b
    if total <= 0:
        return 50, 50
    a_pct = round((a / total) * 100)
    b_pct = 100 - a_pct
    return a_pct, b_pct


def normalize_3way(home, draw, away):
    total = home + draw + away
    if total <= 0:
        return 33, 34, 33
    home_pct = round((home / total) * 100)
    draw_pct = round((draw / total) * 100)
    away_pct = 100 - home_pct - draw_pct
    return home_pct, draw_pct, away_pct


def risk_badge(confidence):
    if confidence >= 78:
        return "SAFE"
    if confidence >= 62:
        return "MEDIUM"
    return "RISKY"


def football_h2h_bonus(h2h: List[Dict], home_team: str, away_team: str):
    home_wins = 0
    away_wins = 0

    for match in h2h[:5]:
        hs = int(match.get("home_score", 0))
        aw = int(match.get("away_score", 0))

        if match.get("home_team") == home_team and hs > aw:
            home_wins += 1
        elif match.get("away_team") == home_team and aw > hs:
            home_wins += 1

        if match.get("home_team") == away_team and hs > aw:
            away_wins += 1
        elif match.get("away_team") == away_team and aw > hs:
            away_wins += 1

    return home_wins * 4, away_wins * 4


def predict_football_from_profiles(home_profile: Dict, away_profile: Dict, h2h: List[Dict], match: Dict) -> Dict:
    h2h_home_bonus, h2h_away_bonus = football_h2h_bonus(
        h2h, match.get("home_team", ""), match.get("away_team", "")
    )

    home_power = (
        home_profile["form_score"] * 0.26 +
        home_profile["avg_scored"] * 12 +
        (100 - home_profile["avg_conceded"] * 10) * 0.10 +
        home_profile["home_strength"] * 0.18 +
        home_profile["avg_possession"] * 0.10 +
        home_profile["avg_shots"] * 1.8 +
        home_profile["avg_corners"] * 1.1 +
        h2h_home_bonus +
        6
    )

    away_power = (
        away_profile["form_score"] * 0.26 +
        away_profile["avg_scored"] * 12 +
        (100 - away_profile["avg_conceded"] * 10) * 0.10 +
        away_profile["away_strength"] * 0.18 +
        away_profile["avg_possession"] * 0.10 +
        away_profile["avg_shots"] * 1.8 +
        away_profile["avg_corners"] * 1.1 +
        h2h_away_bonus
    )

    gap = abs(home_power - away_power)
    confidence = clamp(round(52 + gap * 0.6), 50, 94)

    draw_raw = 26 + max(4, 16 - int(gap / 8))
    home_pct, draw_pct, away_pct = normalize_3way(home_power, draw_raw, away_power)

    if home_power > away_power:
        winner = match.get("home_team", "Domicile")
        likely_score = "2-1" if confidence < 76 else "2-0"
    elif away_power > home_power:
        winner = match.get("away_team", "Extérieur")
        likely_score = "1-2" if confidence < 76 else "0-2"
    else:
        winner = "Nul"
        likely_score = "1-1"

    btts = likely_score in ["1-1", "2-1", "1-2", "2-2"]
    over_2_5 = likely_score in ["2-1", "1-2", "2-2", "3-1", "1-3"]

    return {
        "winner": winner,
        "half_winner": winner if winner != "Nul" else "Nul",
        "home_win_pct": home_pct,
        "draw_pct": draw_pct,
        "away_win_pct": away_pct,
        "likely_score": likely_score,
        "btts": btts,
        "over_2_5": over_2_5,
        "confidence": confidence,
        "risk_badge": risk_badge(confidence),
        "attack_index": round((home_profile["avg_shots"] + away_profile["avg_shots"]) / 2),
        "summary": "Prédiction basée sur l'historique football des deux équipes.",
    }


def predict_basketball_from_profiles(home_profile: Dict, away_profile: Dict, h2h: List[Dict], match: Dict) -> Dict:
    home_power = (
        home_profile["form_score"] * 0.34 +
        home_profile["avg_scored"] * 0.55 +
        (130 - home_profile["avg_conceded"]) * 0.18 +
        home_profile["home_strength"] * 0.22 +
        5
    )
    away_power = (
        away_profile["form_score"] * 0.34 +
        away_profile["avg_scored"] * 0.55 +
        (130 - away_profile["avg_conceded"]) * 0.18 +
        away_profile["away_strength"] * 0.22
    )

    gap = abs(home_power - away_power)
    confidence = clamp(round(53 + gap * 0.8), 50, 95)
    home_pct, away_pct = normalize_2way(home_power, away_power)

    winner = match.get("home_team") if home_power >= away_power else match.get("away_team")
    likely_score = "104-97" if winner == match.get("home_team") else "97-104"

    return {
        "winner": winner,
        "half_winner": winner,
        "home_win_pct": home_pct,
        "draw_pct": 0,
        "away_win_pct": away_pct,
        "likely_score": likely_score,
        "btts": True,
        "over_2_5": True,
        "confidence": confidence,
        "risk_badge": risk_badge(confidence),
        "attack_index": round((home_profile["avg_scored"] + away_profile["avg_scored"]) / 10),
        "summary": "Prédiction basée sur l'historique basketball.",
    }


def predict_tennis_from_profiles(home_profile: Dict, away_profile: Dict, h2h: List[Dict], match: Dict, tt_mode: bool = False) -> Dict:
    home_power = (
        home_profile["form_score"] * 0.42 +
        home_profile["avg_sets_for"] * 16 -
        home_profile["avg_sets_against"] * 8 +
        4
    )
    away_power = (
        away_profile["form_score"] * 0.42 +
        away_profile["avg_sets_for"] * 16 -
        away_profile["avg_sets_against"] * 8
    )

    gap = abs(home_power - away_power)
    confidence = clamp(round(54 + gap * 0.8), 50, 95)
    home_pct, away_pct = normalize_2way(home_power, away_power)

    winner = match.get("home_team") if home_power >= away_power else match.get("away_team")
    likely_score = "3-1" if tt_mode and confidence >= 74 else "3-2" if tt_mode else "2-0" if confidence >= 72 else "2-1"

    return {
        "winner": winner,
        "half_winner": winner,
        "home_win_pct": home_pct,
        "draw_pct": 0,
        "away_win_pct": away_pct,
        "likely_score": likely_score,
        "btts": False,
        "over_2_5": False,
        "confidence": confidence,
        "risk_badge": risk_badge(confidence),
        "attack_index": round((home_profile["form_score"] + away_profile["form_score"]) / 20),
        "summary": "Prédiction basée sur l'historique du joueur.",
    }