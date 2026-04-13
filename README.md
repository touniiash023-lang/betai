# Football Analytics Pro V2 Ultra Pro Analytics

Projet complet **frontend + backend** pour afficher des matchs football à venir et produire une **analyse statistique avancée** à partir de l'API `football-data.org`.

## Important
- Ce projet fournit une **analyse informative**.
- **Aucun résultat réel n'est garanti.**
- Pense à mettre ta vraie clé API dans `backend/.env`.

## Nouveautés V2
- Dashboard premium
- Filtres par jours et compétitions
- Fiche match détaillée
- Probabilités 1X2 indicatives
- Double chance
- BTTS / over-under
- Score probable + scores alternatifs
- Tendances première mi-temps
- Forme récente domicile / extérieur
- Classement et points
- Frontend prêt pour Netlify, backend prêt pour Render

## Structure
- `backend/` : Flask API
- `frontend/` : React + Vite

## Installation backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate sous Windows
pip install -r requirements.txt
cp .env.example .env
```

Puis remplis `backend/.env` :
```env
FOOTBALL_DATA_API_KEY=TA_CLE_API
FOOTBALL_DATA_BASE_URL=https://api.football-data.org/v4
DEFAULT_COMPETITIONS=PL,PD,BL1,SA,FL1,CL
PORT=5000
```

Démarrage backend :
```bash
python app.py
```

## Installation frontend
```bash
cd frontend
npm install
npm run dev
```

## Endpoints
- `GET /api/health`
- `GET /api/matches/today`
- `GET /api/matches/upcoming?days=3`
- `GET /api/matches/upcoming?days=5&competitions=PL,PD,SA`
- `GET /api/matches/<match_id>`
- `GET /api/analysis/<match_id>`

## Déploiement Render
### Backend
- Runtime: Python
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app`
- Root directory: `backend`
- Variables d'environnement:
  - `FOOTBALL_DATA_API_KEY`
  - `FOOTBALL_DATA_BASE_URL`
  - `DEFAULT_COMPETITIONS`

## Déploiement Netlify
### Frontend
- Base directory: `frontend`
- Build command: `npm run build`
- Publish directory: `dist`
- Si besoin, définir :
```env
VITE_API_BASE_URL=https://ton-backend-render.onrender.com/api
```

## Conseils
- Pour le développement local, Vite proxifie déjà `/api` vers `http://localhost:5000`.
- Pour la production Netlify, ajoute `VITE_API_BASE_URL` vers ton backend Render.
