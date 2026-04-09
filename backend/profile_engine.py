from typing import Dict, List
from history_engine import get_entity_side


def clamp(value, low, high):
    return max(low, min(high, value))


def safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def form_score_from_results(points: int, max_points: int) -> int:
    if max_points <= 0:
        return 50
    return clamp(round((points / max_points) * 100), 20, 95)


def build_football_profile(history: List[Dict], entity_name: str) -> Dict:
    if not history:
        return {
            "name": entity_name,
            "sport": "football",
            "matches_played": 0,
            "wins": 0,
            "draws": 0,
            "losses": 0,
            "form_score": 50,
            "avg_scored": 1.0,
            "avg_conceded": 1.0,
            "avg_possession": 50,
            "avg_shots": 5,
            "avg_corners": 4,
            "btts_rate": 50,
            "over_2_5_rate": 50,
            "home_strength": 50,
            "away_strength": 50,
        }

    wins = draws = losses = 0
    goals_for = goals_against = 0
    possession_total = shots_total = corners_total = 0
    btts_count = over_count = 0
    points = 0
    max_points = 0

    home_points = away_points = 0
    home_max = away_max = 0

    for match in history:
        side = get_entity_side(match, entity_name)
        if not side:
            continue

        hs = safe_int(match.get("home_score"))
        aw = safe_int(match.get("away_score"))

        if side == "home":
            scored = hs
            conceded = aw
            possession = safe_int(match.get("home_possession"), 50)
            shots = safe_int(match.get("home_shots"))
            corners = safe_int(match.get("home_corners"))
        else:
            scored = aw
            conceded = hs
            possession = safe_int(match.get("away_possession"), 50)
            shots = safe_int(match.get("away_shots"))
            corners = safe_int(match.get("away_corners"))

        goals_for += scored
        goals_against += conceded
        possession_total += possession
        shots_total += shots
        corners_total += corners

        if scored > 0 and conceded > 0:
            btts_count += 1
        if scored + conceded >= 3:
            over_count += 1

        max_points += 3
        if side == "home":
            home_max += 3
        else:
            away_max += 3

        if scored > conceded:
            wins += 1
            points += 3
            if side == "home":
                home_points += 3
            else:
                away_points += 3
        elif scored == conceded:
            draws += 1
            points += 1
            if side == "home":
                home_points += 1
            else:
                away_points += 1
        else:
            losses += 1

    played = max(1, len(history))

    return {
        "name": entity_name,
        "sport": "football",
        "matches_played": len(history),
        "wins": wins,
        "draws": draws,
        "losses": losses,
        "form_score": form_score_from_results(points, max_points),
        "avg_scored": round(goals_for / played, 2),
        "avg_conceded": round(goals_against / played, 2),
        "avg_possession": round(possession_total / played),
        "avg_shots": round(shots_total / played, 1),
        "avg_corners": round(corners_total / played, 1),
        "btts_rate": round((btts_count / played) * 100),
        "over_2_5_rate": round((over_count / played) * 100),
        "home_strength": form_score_from_results(home_points, home_max),
        "away_strength": form_score_from_results(away_points, away_max),
    }


def build_basketball_profile(history: List[Dict], entity_name: str) -> Dict:
    if not history:
        return {
            "name": entity_name,
            "sport": "basketball",
            "matches_played": 0,
            "wins": 0,
            "losses": 0,
            "form_score": 50,
            "avg_scored": 90,
            "avg_conceded": 90,
            "home_strength": 50,
            "away_strength": 50,
        }

    wins = losses = 0
    points_for = points_against = 0
    total_points = 0
    max_points = 0
    home_points = away_points = 0
    home_max = away_max = 0

    for match in history:
        side = get_entity_side(match, entity_name)
        if not side:
            continue

        hs = safe_int(match.get("home_score"))
        aw = safe_int(match.get("away_score"))

        if side == "home":
            scored, conceded = hs, aw
            home_max += 3
        else:
            scored, conceded = aw, hs
            away_max += 3

        points_for += scored
        points_against += conceded
        max_points += 3

        if scored > conceded:
            wins += 1
            total_points += 3
            if side == "home":
                home_points += 3
            else:
                away_points += 3
        else:
            losses += 1

    played = max(1, len(history))

    return {
        "name": entity_name,
        "sport": "basketball",
        "matches_played": len(history),
        "wins": wins,
        "losses": losses,
        "form_score": form_score_from_results(total_points, max_points),
        "avg_scored": round(points_for / played, 1),
        "avg_conceded": round(points_against / played, 1),
        "home_strength": form_score_from_results(home_points, home_max),
        "away_strength": form_score_from_results(away_points, away_max),
    }


def build_tennis_profile(history: List[Dict], entity_name: str, sport_name: str = "tennis") -> Dict:
    if not history:
        return {
            "name": entity_name,
            "sport": sport_name,
            "matches_played": 0,
            "wins": 0,
            "losses": 0,
            "form_score": 50,
            "sets_for": 0,
            "sets_against": 0,
            "avg_sets_for": 1.0,
            "avg_sets_against": 1.0,
        }

    wins = losses = 0
    sets_for = sets_against = 0
    total_points = 0
    max_points = 0

    for match in history:
        side = get_entity_side(match, entity_name)
        if not side:
            continue

        hs = safe_int(match.get("home_score"))
        aw = safe_int(match.get("away_score"))

        if side == "home":
            scored, conceded = hs, aw
        else:
            scored, conceded = aw, hs

        sets_for += scored
        sets_against += conceded
        max_points += 3

        if scored > conceded:
            wins += 1
            total_points += 3
        else:
            losses += 1

    played = max(1, len(history))

    return {
        "name": entity_name,
        "sport": sport_name,
        "matches_played": len(history),
        "wins": wins,
        "losses": losses,
        "form_score": form_score_from_results(total_points, max_points),
        "sets_for": sets_for,
        "sets_against": sets_against,
        "avg_sets_for": round(sets_for / played, 2),
        "avg_sets_against": round(sets_against / played, 2),
    }


def build_profile_for_sport(sport: str, history: List[Dict], entity_name: str) -> Dict:
    sport = (sport or "").strip()

    if sport == "football":
        return build_football_profile(history, entity_name)
    if sport == "basketball":
        return build_basketball_profile(history, entity_name)
    if sport == "tennis":
        return build_tennis_profile(history, entity_name, "tennis")
    if sport == "table_tennis":
        return build_tennis_profile(history, entity_name, "table_tennis")

    return build_football_profile(history, entity_name)