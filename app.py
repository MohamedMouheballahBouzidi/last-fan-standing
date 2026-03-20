import io
import zipfile
from pathlib import Path
from typing import Dict, Optional

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="Last Fan Standing Dashboard",
    page_icon="LFS",
    layout="wide",
)


def _read_csv_from_zip(zf: zipfile.ZipFile, name: str) -> Optional[pd.DataFrame]:
    # Try exact path first, then a suffix match to support nested zip roots.
    candidate_names = [name]
    if name not in zf.namelist():
        suffix = "/" + name
        suffix_matches = [n for n in zf.namelist() if n.endswith(suffix) or n.endswith(name)]
        candidate_names.extend(suffix_matches)

    for candidate in candidate_names:
        try:
            with zf.open(candidate) as f:
                return pd.read_csv(f)
        except KeyError:
            continue

    return None


def _zip_contains_member(zip_path: Path, member_suffix: str) -> bool:
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            names = zf.namelist()
            return any(n == member_suffix or n.endswith("/" + member_suffix) or n.endswith(member_suffix) for n in names)
    except Exception:
        return False


def pick_default_artifacts_zip() -> Optional[Path]:
    # Prefer ZIPs that contain upcoming predictions, then newest by modified time.
    candidates = sorted(Path(".").glob("lastfan_artifacts*.zip"))
    if not candidates:
        return None

    valid = [p for p in candidates if _zip_contains_member(p, "output/upcoming_predictions_by_gameweek.csv")]
    target = valid if valid else candidates
    return max(target, key=lambda p: p.stat().st_mtime)


@st.cache_data(show_spinner=False)
def load_artifacts_from_zip_bytes(zip_bytes: bytes) -> Dict[str, Optional[pd.DataFrame]]:
    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
        return {
            "predictions": _read_csv_from_zip(zf, "output/upcoming_predictions_by_gameweek.csv"),
            "lfs_plan": _read_csv_from_zip(zf, "output/lfs_pick_plan_by_gameweek.csv"),
            "elo": _read_csv_from_zip(zf, "output/elo_ratings.csv"),
            "feature_importance": _read_csv_from_zip(zf, "output/feature_importance.csv"),
        }


def derive_highest_probability_team(pred_df: pd.DataFrame) -> pd.DataFrame:
    df = pred_df.copy()
    df["p_home"] = pd.to_numeric(df["p_home"], errors="coerce")
    df["p_away"] = pd.to_numeric(df["p_away"], errors="coerce")

    home_better = df["p_home"] >= df["p_away"]
    df["top_team"] = df["HomeTeam"].where(home_better, df["AwayTeam"])
    df["opponent"] = df["AwayTeam"].where(home_better, df["HomeTeam"])
    df["venue"] = "HOME"
    df.loc[~home_better, "venue"] = "AWAY"
    df["team_win_probability"] = df["p_home"].where(home_better, df["p_away"])

    idx = df.groupby("GameWeek")["team_win_probability"].idxmax()
    out = df.loc[idx, ["GameWeek", "top_team", "opponent", "venue", "team_win_probability"]].copy()
    out = out.sort_values("GameWeek").reset_index(drop=True)
    return out


def normalize_prediction_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    # Backward compatibility with older notebook export names.
    rename_map = {
        "best_outcome_prob": "best_win_prob",
        "outcome_confidence": "confidence",
    }
    out = out.rename(columns={k: v for k, v in rename_map.items() if k in out.columns})

    for col in ["Date", "GameWeek", "p_home", "p_draw", "p_away", "best_win_prob"]:
        if col in out.columns:
            if col == "Date":
                out[col] = pd.to_datetime(out[col], errors="coerce")
            else:
                out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


def show_overview(pred_df: pd.DataFrame, highest_df: pd.DataFrame, lfs_df: Optional[pd.DataFrame]) -> None:
    st.subheader("Overview")

    total_matches = len(pred_df)
    total_gameweeks = pred_df["GameWeek"].nunique() if "GameWeek" in pred_df.columns else 0
    avg_best_prob = pred_df["best_win_prob"].mean() if "best_win_prob" in pred_df.columns else float("nan")

    c1, c2, c3 = st.columns(3)
    c1.metric("Upcoming matches", f"{total_matches}")
    c2.metric("Gameweeks", f"{total_gameweeks}")
    c3.metric("Avg best winner probability", f"{avg_best_prob:.1%}" if pd.notna(avg_best_prob) else "N/A")

    if highest_df.empty:
        st.info("Predictions CSV loaded, but there are currently no upcoming fixtures to display.")
    else:
        st.markdown("Highest-probability team per gameweek")
        st.dataframe(highest_df, use_container_width=True)

    if lfs_df is not None and not lfs_df.empty:
        st.markdown("One-team-once LFS pick plan")
        st.dataframe(lfs_df, use_container_width=True)


def show_gameweek_view(pred_df: pd.DataFrame, highest_df: pd.DataFrame) -> None:
    st.subheader("Gameweek predictions")

    if pred_df.empty:
        st.info("No upcoming fixtures are available in the current predictions file.")
        return

    gameweeks = sorted([int(gw) for gw in pred_df["GameWeek"].dropna().unique().tolist()])
    if not gameweeks:
        st.info("No gameweek data found in predictions file.")
        return

    selected_gw = st.selectbox("Select gameweek", options=gameweeks, index=0)

    gw_df = pred_df[pred_df["GameWeek"] == selected_gw].copy()
    gw_df = gw_df.sort_values("best_win_prob", ascending=False)

    st.markdown(f"Matches in gameweek {selected_gw}")
    st.dataframe(gw_df, use_container_width=True)

    st.markdown(f"Top team for gameweek {selected_gw}")
    top_row = highest_df[highest_df["GameWeek"] == selected_gw]
    st.dataframe(top_row, use_container_width=True)


def show_probability_charts(pred_df: pd.DataFrame, highest_df: pd.DataFrame) -> None:
    st.subheader("Probability charts")

    if pred_df.empty or highest_df.empty:
        st.info("Charts will appear once upcoming fixtures are available.")
        return

    chart_df = highest_df.copy()
    chart_df["team_win_probability"] = pd.to_numeric(chart_df["team_win_probability"], errors="coerce")

    fig = px.bar(
        chart_df,
        x="GameWeek",
        y="team_win_probability",
        color="top_team",
        title="Highest team win probability by gameweek",
        labels={"team_win_probability": "Win probability"},
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    if "predicted_winner" in pred_df.columns:
        winner_counts = (
            pred_df["predicted_winner"]
            .dropna()
            .value_counts()
            .rename_axis("team")
            .reset_index(name="count")
            .head(15)
        )
        fig2 = px.bar(
            winner_counts,
            x="team",
            y="count",
            title="Most frequently predicted winners (top 15)",
        )
        st.plotly_chart(fig2, use_container_width=True)


def show_model_context(elo_df: Optional[pd.DataFrame], fi_df: Optional[pd.DataFrame]) -> None:
    st.subheader("Model context")

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("Current Elo ranking (top 20)")
        if elo_df is not None and not elo_df.empty:
            st.dataframe(elo_df.head(20), use_container_width=True)
        else:
            st.info("No elo_ratings.csv found in artifacts zip.")

    with c2:
        st.markdown("Top feature importance")
        if fi_df is not None and not fi_df.empty:
            st.dataframe(fi_df.head(20), use_container_width=True)
        else:
            st.info("No feature_importance.csv found in artifacts zip.")


def show_downloads(pred_df: pd.DataFrame, highest_df: pd.DataFrame, lfs_df: Optional[pd.DataFrame]) -> None:
    st.subheader("Download outputs")

    st.download_button(
        label="Download upcoming predictions CSV",
        data=pred_df.to_csv(index=False).encode("utf-8"),
        file_name="upcoming_predictions_by_gameweek.csv",
        mime="text/csv",
    )

    if not highest_df.empty:
        st.download_button(
            label="Download highest-probability team CSV",
            data=highest_df.to_csv(index=False).encode("utf-8"),
            file_name="highest_probability_team_by_gameweek.csv",
            mime="text/csv",
        )

    if lfs_df is not None and not lfs_df.empty:
        st.download_button(
            label="Download LFS pick plan CSV",
            data=lfs_df.to_csv(index=False).encode("utf-8"),
            file_name="lfs_pick_plan_by_gameweek.csv",
            mime="text/csv",
        )


def main() -> None:
    st.title("Last Fan Standing - Premier League Predictor")
    st.caption("Deploy-ready dashboard for weekly winner predictions and highest-probability team picks.")

    st.sidebar.header("Artifacts source")
    uploaded_zip = st.sidebar.file_uploader("Upload latest artifacts zip", type=["zip"])

    default_zip = pick_default_artifacts_zip()
    use_default = st.sidebar.checkbox(
        "Use bundled zip from repository",
        value=(default_zip is not None) and uploaded_zip is None,
    )

    zip_bytes: Optional[bytes] = None

    if uploaded_zip is not None:
        zip_bytes = uploaded_zip.read()
        st.sidebar.caption(f"Using uploaded ZIP: {uploaded_zip.name}")
    elif use_default and default_zip is not None and default_zip.exists():
        zip_bytes = default_zip.read_bytes()
        st.sidebar.caption(f"Using bundled ZIP: {default_zip.name}")

    if zip_bytes is None:
        st.info(
            "Upload your notebook artifacts zip from the sidebar to start. "
            "The zip should contain output/upcoming_predictions_by_gameweek.csv."
        )
        return

    data = load_artifacts_from_zip_bytes(zip_bytes)

    pred_df = data["predictions"]
    if pred_df is None:
        st.error(
            "Could not find output/upcoming_predictions_by_gameweek.csv in the zip. "
            "Run the notebook weekly planning cell and regenerate artifacts."
        )
        return

    pred_df = normalize_prediction_columns(pred_df)
    highest_df = derive_highest_probability_team(pred_df)
    lfs_df = data["lfs_plan"]

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Overview", "Gameweek", "Charts", "Model context", "Downloads"]
    )

    with tab1:
        show_overview(pred_df, highest_df, lfs_df)
    with tab2:
        show_gameweek_view(pred_df, highest_df)
    with tab3:
        show_probability_charts(pred_df, highest_df)
    with tab4:
        show_model_context(data["elo"], data["feature_importance"])
    with tab5:
        show_downloads(pred_df, highest_df, lfs_df)


if __name__ == "__main__":
    main()
