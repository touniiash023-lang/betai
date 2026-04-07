import requests

# 🔑 METS TA CLÉ API ICI
API_KEY = "7406df08dc9947d094ff523cbb61cd87"

# 📡 Headers
headers = {
    "X-Auth-Token": API_KEY
}

# 🔥 Fonction pour récupérer matchs
def get_matches():
    url = "https://api.football-data.org/v4/matches"

    try:
        response = requests.get(url, headers=headers)
        data = response.json()

        if "matches" in data:
            matches = []

            for match in data["matches"][:10]:  # limite 10 matchs
                matches.append({
                    "home": match["homeTeam"]["name"],
                    "away": match["awayTeam"]["name"],
                    "date": match["utcDate"],
                    "status": match["status"]
                })

            return matches
        else:
            return {"error": data}

    except Exception as e:
        return {"error": str(e)}

# 🔍 Test direct
if __name__ == "__main__":
    matches = get_matches()
    print(matches)




