from typing import List, Dict


def normalize_name(name: str) -> str:
    return (name or "").strip().lower()


def get_entity_history(matches: List[Dict], sport: str, name: str) -> List[Dict]:
    target = normalize_name(name)
    sport = (sport or "").strip()

    result = []
    for match in matches:
        if match.get("sport") != sport:
            continue

        home_name = normalize_name(match.get("home_team"))
        away_name = normalize_name(match.get("away_team"))

        if home_name == target or away_name == target:
            result.append(match)

    result.sort(key=lambda m: m.get("match_date", ""), reverse=True)
    return result


def get_recent_history(matches: List[Dict], sport: str, name: str, limit: int = 10) -> List[Dict]:
    history = get_entity_history(matches, sport, name)
    finished = [m for m in history if m.get("status") == "finished"]
    return finished[:limit]


def get_h2h_history(matches: List[Dict], sport: str, name_a: str, name_b: str, limit: int = 10) -> List[Dict]:
    a = normalize_name(name_a)
    b = normalize_name(name_b)
    sport = (sport or "").strip()

    result = []
    for match in matches:
        if match.get("sport") != sport:
            continue

        home_name = normalize_name(match.get("home_team"))
        away_name = normalize_name(match.get("away_team"))

        if (home_name == a and away_name == b) or (home_name == b and away_name == a):
            result.append(match)

    result.sort(key=lambda m: m.get("match_date", ""), reverse=True)
    return result[:limit]


def get_entity_side(match: Dict, entity_name: str) -> str:
    target = normalize_name(entity_name)
    if normalize_name(match.get("home_team")) == target:
        return "home"
    if normalize_name(match.get("away_team")) == target:
        return "away"
    return ""