# Deploy Last Fan Standing App

This project now includes a Streamlit app that can be deployed in minutes.

## Files Added
- `app.py`
- `requirements.txt`
- `.streamlit/config.toml`

## What the App Shows
- Per-match winner probabilities for upcoming fixtures
- The highest-probability team for each gameweek
- LFS one-team-once pick plan
- Elo table and feature-importance context
- CSV downloads from the dashboard

## Local Run (Windows)
From this folder:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Then open the URL shown in terminal, usually `http://localhost:8501`.

## Deploy to Streamlit Community Cloud (Free)
1. Push this folder to a GitHub repository.
2. Go to Streamlit Community Cloud and click **New app**.
3. Select your repository and branch.
4. Set main file path to `app.py`.
5. Click **Deploy**.

The app will install dependencies from `requirements.txt` automatically.

## Data Input Modes
The app supports two modes:

1. Bundled zip mode:
- If `lastfan_artifacts (4).zip` exists in repo root, app auto-loads it.

2. Upload mode (recommended weekly):
- Use the sidebar file uploader to upload the latest artifacts zip generated from your notebook.

The zip should include at least:
- `output/upcoming_predictions_by_gameweek.csv`

Optional but useful:
- `output/lfs_pick_plan_by_gameweek.csv`
- `output/elo_ratings.csv`
- `output/feature_importance.csv`

## Weekly Update Workflow
1. Run notebook weekly forecasting cells.
2. Rebuild artifacts zip.
3. Open deployed app and upload the new zip from sidebar.

No redeploy needed for weekly updates if you use upload mode.

## Optional: Use a Cleaner Artifact Name
If you prefer, rename your zip to `lastfan_artifacts.zip` before uploading.
The uploader accepts any `.zip` name, so this is optional.
