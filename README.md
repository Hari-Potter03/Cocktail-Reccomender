# Cocktail Recommender Web App
An end-to-end project that suggests cocktails based on a user’s taste preferences and ratings. It blends data engineering with full-stack development to show how to build, run, and interact with a personalized recommendation system.

It includes:

* A Python data pipeline to collect (TheCocktailDB API), curate, and featurize a catalog of cocktails (ingredients, spirit, tags, season).

* A hybrid recommender: content + taste vector scoring (optional ALS training script for collaborative filtering when ratings grow).

* A FastAPI backend exposing /recs, /search, /drinks, /similar, /ratings, and /profile.

* A React.js frontend with onboarding questionnaire, spirit tabs, search, drink detail pages, and a star-rating widget.

* Local JSON storage (no external DB) and a Makefile for one-command setup and run.
---

## How to run the project

### Prerequisites
- **Python** 3.10+  
- **Node.js** **20+** (use `nvm install 20 && nvm use 20`)  
- **Git**
---

### 1) Clone the repo
```bash
git clone https://github.com/<your-username>/Cocktail-Reccomender.git
cd Cocktail-Reccomender
```
---

### 2) Create a Python venv & install deps

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows
# .venv\Scripts\activate

pip install -U pip
pip install -r requirements.txt
```
---

### 3) (Optional) Build data/features
If `data/curated/` and `data/features/` are already present, you can skip.

```bash
# Full pipeline: fetch → curate → featurize
make data
# or just rebuild features from curated JSON
make run-pipeline
```
---

### 4) Configure the frontend → backend URL
Create `frontend/.env`:

```.env
VITE_API_BASE_URL=http://127.0.0.1:8000
````
---

### 5) Run the backend API (FastAPI)

```bash
make run-backend
# API:  http://127.0.0.1:8000
# Docs: http://127.0.0.1:8000/docs
```
---

### 6) Run the React frontend (Vite)
  Requires Node ≥ 20.

```bash
make run-frontend
# Frontend: http://localhost:5173
```
---

### 7) Use the web app
1. Open http://localhost:5173

2. Login (local-only), confirm age

3. Complete Onboarding (pick spirits/tags/season)

4. Explore Home (recs), Browse (search/filters), Drink (details + rate), Profile (taste summary)

Reset & troubleshooting
Reset local backend data

```bash
make reset   # clears storage/ratings.jsonl and storage/profiles.json
```
