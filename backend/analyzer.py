from sports_engine import (
    analyze_football,
    analyze_basketball,
    analyze_tennis,
    analyze_table_tennis,
)


def analyze_match(match):
    sport = (match.get("sport") or "football").strip()

    if sport == "football":
        return analyze_football(match)
    if sport == "basketball":
        return analyze_basketball(match)
    if sport == "tennis":
        return analyze_tennis(match)
    if sport == "table_tennis":
        return analyze_table_tennis(match)

    return analyze_football(match)