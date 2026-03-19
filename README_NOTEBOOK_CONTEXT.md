# Last Fan Standing - Notebook Context Handoff

This file captures the full context of work completed on the Colab notebook so it can be continued in a new conversation without losing decisions.

## Main Notebook
- File: `lastfan_colab.ipynb`
- Goal: End-to-end Premier League prediction workflow for Last Fan Standing (LFS)
- Core outputs:
  - Match outcome probabilities (H/D/A)
  - LFS-specific team-win candidates
  - One-team-per-gameweek LFS pick plan
  - Top 3 risk-tier picks (safe/balanced/aggressive)

---

## What Was Fixed and Added

### 1) Notebook File Integrity
- Cleaned malformed JSON exported from another model response.
- Removed trailing non-notebook text.
- Fixed malformed URL/source line issues.
- Validated notebook Python syntax after edits.

### 2) Bookmaker Baseline Bug Fix
- Fixed row mismatch error (`ValueError: inconsistent numbers of samples`) by aligning baseline rows with `y_test.index`.
- Stabilized class encoding order (`['A','D','H']`).

### 3) Current Season Support (2025-26)
- Added season `2025-26` in config and data loader (`2526` code).
- Included current season in ingestion pipeline.
- Updated season split strategy to keep current season included for live adaptation.

### 4) Team Normalization and Promotion/Relegation Handling
- Added Sunderland aliases to team normalizer.
- Added season transition Elo logic:
  - carryover/mean-reversion each new season
  - lower initial Elo for promoted teams
- Added promoted-team indicators in features:
  - `is_promoted_home`
  - `is_promoted_away`

### 5) New Feature Upgrades
- Added recency-sensitive features (rolling and weighted form variants).
- Added rest-days features from fixture dates:
  - `home_rest_days`, `away_rest_days`, `diff_rest_days`
- Added discipline proxies using cards:
  - rolling red/yellow card features
  - `discipline_risk_*`

### 6) Leakage Fix (Critical)
- Fixed Elo leakage in historical feature generation:
  - previously Elo was updated with current match result before feature capture
  - now Elo pre-match features are captured first
  - Elo update occurs after feature row creation

### 7) Multi-Model Benchmarking
- Added model comparison block:
  - XGBoost
  - Logistic Regression
  - Random Forest
  - LightGBM (if installed)
- Model with best log loss is selected as `serving_model`.
- Weekly prediction code now uses `serving_model`.

### 8) Market-Blended Probabilities
- Added robust blending with bookmaker implied probabilities when odds exist.
- Configured blend in live prediction path via `market_blend_weight` (default 0.35).

### 9) LFS Logic Tightening
- Separated generic outcome confidence from LFS team-win confidence.
- LFS picks now ignore draw as a pick target (draw is not a valid LFS pick).
- Added per-fixture LFS fields:
  - `lfs_pick_team`
  - `lfs_pick_side`
  - `lfs_pick_win_prob`
  - `lfs_pick_confidence`

### 10) Top 3 Risk-Tier Picks
- Added function to generate top 3 picks per gameweek by tier:
  - safe
  - balanced
  - aggressive
- Exported as CSV.

### 11) Upcoming Fixtures Fallback Stack
Because public fixture sources can be blocked in Colab sessions:
- Primary: Football-Data upcoming unplayed rows
- Fallback 1: FBref schedule parse (can fail with 403)
- Fallback 2: Manual CSV fallback (`/content/data/upcoming_fixtures_manual.csv`)
- Added helper cell to build manual CSV directly from fixture tuples in notebook.

---

## Current Known Behavior
- If Football-Data has only played rows and FBref is blocked, notebook creates/uses manual fixture CSV.
- For a single gameweek input (e.g., GW31 only), LFS plan correctly outputs one pick for that week.
- This is expected by LFS rules (one pick per gameweek).

---

## Saved Artifacts (from latest zip)
Inside `lastfan_artifacts (4).zip`:
- `data/matches_processed.csv`
- `data/features.csv`
- `data/upcoming_fixtures_manual.csv`
- `models/win_model.pkl`
- `models/poisson_model.pkl`
- `output/evaluation_report.md`
- `output/upcoming_predictions_by_gameweek.csv`
- `output/lfs_pick_plan_by_gameweek.csv`
- Plus plots and ranking CSVs

Note: If a newer notebook run includes the updated save block, it should also export:
- `models/serving_model.pkl`
- `models/inference_bundle.pkl`
- `output/model_comparison.csv`
- `output/lfs_candidates_by_gameweek.csv`
- `output/lfs_top3_by_tier.csv`

---

## Run Order (Recommended)
1. Setup & imports
2. Config
3. Data ingestion (including 2025-26)
4. Feature engineering (with leakage fix active)
5. Data prep
6. Baseline
7. XGBoost train/eval
8. Alternative model comparison and serving model selection
9. Poisson model
10. Live weekly forecasting + LFS planner
11. Save artifacts
12. Generate report

---

## Deployment Direction (Free)
Best free path:
- Streamlit Community Cloud (public share link)

For full interactive deployment, ensure artifacts include:
- `serving_model.pkl`
- `inference_bundle.pkl`
- required CSV outputs

---

## Project Folder Notes
This Desktop folder was created to keep notebook + handoff context + artifacts together for a fresh chat handoff.

