import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
import sys
from pathlib import Path

# Add root folder to path to import src modules
sys.path.append(str(Path(__file__).parent.resolve()))

from src.preprocessing import load_and_preprocess
from src.models import load_models, predict_lambdas
from src.simulations import run_monte_carlo, simulate_match
from src.helpers import format_submission, resolve_group_standings, build_knockout_bracket, get_group_fixtures
from src.config import WC2026_GROUPS, TOURNAMENT_DATE, FEATURE_COLS
from src.feature_engineering import _get_rolling_rates, get_team_form, compute_dynamic_discipline

# Set page config for wide layout and dark aesthetic
st.set_page_config(
    page_title="FIFA World Cup 2026 Prediction Engine",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Injected custom CSS to format headers, columns, and hover tooltips
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Plus+Jakarta+Sans:wght@300;400;500;700&display=swap');
    
    /* Main container stylings */
    .stApp {
        background-color: #0b0f19;
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 800;
        letter-spacing: -0.02em;
    }
    
    /* Header Gradient Banner */
    .banner {
        background: linear-gradient(135deg, #1e1b4b 0%, #0f172a 100%);
        border: 1px solid rgba(99, 102, 241, 0.15);
        border-radius: 16px;
        padding: 30px 40px;
        margin-bottom: 25px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
    }
    .banner h1 {
        background: linear-gradient(to right, #818cf8, #c084fc, #f472b6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        font-size: 38px;
    }
    .banner p {
        color: #94a3b8;
        font-size: 16px;
        margin: 8px 0 0 0;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0f172a !important;
        border-right: 1px solid rgba(255,255,255,0.05);
    }
    
    /* Bracket Container Layout */
    .bracket-wrapper {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: #0f172a;
        padding: 24px;
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        box-shadow: 0 10px 40px rgba(0,0,0,0.6);
        height: 1050px;
        overflow-x: auto;
        overflow-y: hidden;
        margin-bottom: 30px;
    }
    .bracket-column {
        display: flex;
        flex-direction: column;
        justify-content: space-around;
        height: 100%;
        min-width: 200px;
        flex: 1;
        margin: 0 10px;
    }
    .center-header {
        font-size: 14px;
        font-weight: 800;
        color: #818cf8;
        text-align: center;
        margin-bottom: 15px;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        border-bottom: 1px solid rgba(99, 102, 241, 0.2);
        padding-bottom: 6px;
    }
    
    /* Matchup Card Styling */
    .matchup {
        background: rgba(30, 41, 59, 0.65);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        padding: 10px 14px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        backdrop-filter: blur(15px);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        margin: 8px 0;
    }
    .matchup:hover {
        border-color: #818cf8;
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.25);
    }
    .matchup-header {
        font-size: 9px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #94a3b8;
        margin-bottom: 6px;
        font-weight: 700;
    }
    .team-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 5px 0;
        border-radius: 6px;
        margin: 2px 0;
        transition: background-color 0.2s;
    }
    .team-row.winner {
        background: rgba(99, 102, 241, 0.15);
        border-left: 3px solid #818cf8;
        padding-left: 5px;
    }
    .team-info {
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .team-name {
        font-size: 13px;
        font-weight: 600;
        color: #f1f5f9;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 100px;
    }
    .team-score {
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .score-goals {
        font-size: 14px;
        font-weight: 800;
        color: #f8fafc;
    }
    .score-prob {
        font-size: 10px;
        color: #94a3b8;
        font-weight: 500;
    }
    
    /* Interactive Tooltip Flags */
    .flag-wrapper {
        position: relative;
        display: inline-block;
        cursor: pointer;
        vertical-align: middle;
    }
    .flag-img {
        width: 24px;
        height: 16px;
        border-radius: 3px;
        object-fit: cover;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        border: 1px solid rgba(255,255,255,0.1);
        transition: transform 0.2s;
    }
    .flag-wrapper:hover .flag-img {
        transform: scale(1.1);
    }
    
    .flag-wrapper .tooltiptext {
        visibility: hidden;
        width: 260px;
        background-color: rgba(11, 15, 25, 0.96);
        color: #f8fafc;
        text-align: left;
        border-radius: 12px;
        padding: 15px;
        position: absolute;
        z-index: 999;
        bottom: 130%;
        left: 50%;
        transform: translateX(-50%);
        opacity: 0;
        transition: opacity 0.25s, transform 0.25s;
        box-shadow: 0 15px 30px rgba(0, 0, 0, 0.7);
        border: 1px solid rgba(129, 140, 248, 0.3);
        backdrop-filter: blur(20px);
        font-size: 12px;
        line-height: 1.6;
    }
    .flag-wrapper:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
        transform: translateX(-50%) translateY(-6px);
    }
    .flag-wrapper .tooltiptext div {
        display: flex;
        justify-content: space-between;
        margin: 5px 0;
        border-bottom: 1px solid rgba(255,255,255,0.06);
        padding-bottom: 3px;
    }
    .flag-wrapper .tooltiptext div strong {
        color: #94a3b8;
        font-weight: 500;
    }
    
    /* Champion Special Box */
    .champion-box {
        background: linear-gradient(135deg, rgba(234, 179, 8, 0.15) 0%, rgba(249, 115, 22, 0.15) 100%);
        border: 2px solid #eab308;
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 10px 30px rgba(234, 179, 8, 0.2);
        margin-top: 30px;
        transition: all 0.3s;
    }
    .champion-box:hover {
        transform: scale(1.03);
        box-shadow: 0 15px 40px rgba(234, 179, 8, 0.35);
    }
    
    /* Match Simulator Output Visualizer */
    .sim-card {
        background: rgba(15, 23, 42, 0.5);
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        padding: 20px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Data & Model Cache Loaders
# ---------------------------------------------------------------------------

@st.cache_resource
def get_cached_resources():
    data_dir = "data"
    model_dir = "models"
    
    # Load matched history and elo
    df_matches, team_hist, elo_dict = load_and_preprocess(data_dir)
    
    # Load ML models
    models = load_models(model_dir)
    
    return df_matches, team_hist, elo_dict, models

try:
    df_matches, team_hist, elo_dict, models = get_cached_resources()
except Exception as e:
    st.error(f"Error loading project resources: {e}")
    st.info("Please make sure you are running this from the project root and models/model_bundle.pkl is trained.")
    st.stop()

# ---------------------------------------------------------------------------
# Team Flags Mapping
# ---------------------------------------------------------------------------

TEAM_TO_ISO = {
    "United States": "us", "Panama": "pa", "Bolivia": "bo", "Morocco": "ma",
    "Argentina": "ar", "Chile": "cl", "Peru": "pe", "Australia": "au",
    "Mexico": "mx", "Jamaica": "jm", "Venezuela": "ve", "Paraguay": "py",
    "Brazil": "br", "Ecuador": "ec", "Egypt": "eg", "Serbia": "rs",
    "Spain": "es", "Uruguay": "uy", "Uzbekistan": "uz", "South Korea": "kr",
    "France": "fr", "Belgium": "be", "Croatia": "hr", "South Africa": "za",
    "England": "gb", "Senegal": "sn", "Colombia": "co", "Tunisia": "tn",
    "Portugal": "pt", "Algeria": "dz", "Cameroon": "cm", "Honduras": "hn",
    "Germany": "de", "Japan": "jp", "Iran": "ir", "Saudi Arabia": "sa",
    "Netherlands": "nl", "Nigeria": "ng", "New Zealand": "nz", "Ivory Coast": "ci",
    "Italy": "it", "Slovenia": "si", "Qatar": "qa", "Ukraine": "ua",
    "Canada": "ca", "Switzerland": "ch", "Norway": "no", "Poland": "pl"
}

TEAM_TO_EMOJI = {
    "United States": "🇺🇸", "Panama": "🇵🇦", "Bolivia": "🇧🇴", "Morocco": "🇲🇦",
    "Argentina": "🇦🇷", "Chile": "🇨🇱", "Peru": "🇵🇪", "Australia": "🇦🇺",
    "Mexico": "🇲🇽", "Jamaica": "🇯🇲", "Venezuela": "🇻🇪", "Paraguay": "🇵🇾",
    "Brazil": "🇧🇷", "Ecuador": "🇪🇨", "Egypt": "🇪🇬", "Serbia": "🇷🇸",
    "Spain": "🇪🇸", "Uruguay": "🇺🇾", "Uzbekistan": "🇺🇿", "South Korea": "🇰🇷",
    "France": "🇫🇷", "Belgium": "🇧🇪", "Croatia": "🇭🇷", "South Africa": "🇿🇦",
    "England": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "Senegal": "🇸🇳", "Colombia": "🇨🇴", "Tunisia": "🇹🇳",
    "Portugal": "🇵🇹", "Algeria": "🇩🇿", "Cameroon": "🇨🇲", "Honduras": "🇭🇳",
    "Germany": "🇩🇪", "Japan": "🇯🇵", "Iran": "🇮🇷", "Saudi Arabia": "🇸🇦",
    "Netherlands": "🇳🇱", "Nigeria": "🇳🇬", "New Zealand": "🇳🇿", "Ivory Coast": "🇨🇮",
    "Italy": "🇮🇹", "Slovenia": "🇸🇮", "Qatar": "🇶🇦", "Ukraine": "🇺🇦",
    "Canada": "🇨🇦", "Switzerland": "🇨🇭", "Norway": "🇳🇴", "Poland": "🇵🇱"
}

# ---------------------------------------------------------------------------
# Pre-calculate base statistics for tooltips
# ---------------------------------------------------------------------------

@st.cache_data
def get_all_team_base_stats(_team_hist, _elo_dict):
    stats = {}
    for group, teams in WC2026_GROUPS.items():
        for team in teams:
            elo = _elo_dict.get(team, 1500.0)
            history = _team_hist.get(team, [])
            attack, defense = _get_rolling_rates(history, team, TOURNAMENT_DATE)
            form = get_team_form(_team_hist, team, TOURNAMENT_DATE)
            discipline = compute_dynamic_discipline(_team_hist, team, TOURNAMENT_DATE)
            
            stats[team] = {
                "FIFA ELO Rating": f"{int(round(elo))}",
                "Recent Form (W5)": f"{form:.1%}",
                "Attack Strength (Avg Goals)": f"{attack:.2f}",
                "Defense Rating (Inverse)": f"{defense:.2f}",
                "Expected Conceded Goals": f"{1.0 / max(defense, 0.1):.2f}",
                "Discipline Index (Expected Cards)": f"{discipline:.2f}"
            }
    return stats

team_stats_cache = get_all_team_base_stats(team_hist, elo_dict)

# ---------------------------------------------------------------------------
# Helper functions for UI Bracket Components
# ---------------------------------------------------------------------------

def get_flag_html(team_name, stats_dict):
    iso = TEAM_TO_ISO.get(team_name, "un")
    emoji = TEAM_TO_EMOJI.get(team_name, "🏳️")
    flag_url = f"https://flagcdn.com/w40/{iso}.png"
    
    stats_html = ""
    if team_name in stats_dict:
        for k, v in stats_dict[team_name].items():
            stats_html += f"<div><strong>{k}:</strong> <span style='color: #818cf8; font-weight: 700;'>{v}</span></div>"
    else:
        stats_html = "<div>No stats loaded</div>"
        
    html = f"""
    <div class="flag-wrapper">
        <img class="flag-img" src="{flag_url}" alt="{team_name}" onerror="this.style.display='none'; this.nextElementSibling.style.display='inline';"/>
        <span class="emoji-flag" style="display:none; font-size:18px; margin-right:4px;">{emoji}</span>
        <div class="tooltiptext">
            <h4 style="margin: 0 0 10px 0; border-bottom: 2px solid rgba(129,140,248,0.3); padding-bottom: 6px; color: #ffffff;">{emoji} {team_name}</h4>
            {stats_html}
        </div>
    </div>
    """
    return html

def get_match_box_html(match_id, match_data, stats_dict):
    if match_data is None:
        return f'<div class="matchup empty"><div class="matchup-header">Match {match_id}</div>Pending Matchup</div>'
        
    home_team = match_data["home_team"]
    away_team = match_data["away_team"]
    home_prob = match_data.get("home_win_prob", 0.5)
    away_prob = match_data.get("away_win_prob", 0.5)
    home_goals = match_data.get("most_common_home_goals", 0)
    away_goals = match_data.get("most_common_away_goals", 0)
    stage = match_data.get("stage", "Knockout")
    
    home_flag_html = get_flag_html(home_team, stats_dict)
    away_flag_html = get_flag_html(away_team, stats_dict)
    
    home_win_class = "winner" if home_prob > away_prob else ""
    away_win_class = "winner" if away_prob > home_prob else ""
    
    html = f"""
    <div class="matchup">
        <div class="matchup-header">Match {match_id} • {stage}</div>
        <div class="team-row {home_win_class}">
            <div class="team-info">
                {home_flag_html}
                <span class="team-name" title="{home_team}">{home_team}</span>
            </div>
            <div class="team-score">
                <span class="score-goals">{home_goals}</span>
                <span class="score-prob">{home_prob:.0%}</span>
            </div>
        </div>
        <div class="team-row {away_win_class}">
            <div class="team-info">
                {away_flag_html}
                <span class="team-name" title="{away_team}">{away_team}</span>
            </div>
            <div class="team-score">
                <span class="score-goals">{away_goals}</span>
                <span class="score-prob">{away_prob:.0%}</span>
            </div>
        </div>
    </div>
    """
    return html

# ---------------------------------------------------------------------------
# Monte Carlo Simulation Runner (Cached & Dynamic)
# ---------------------------------------------------------------------------

@st.cache_data
def run_simulation_cached(_team_hist, _elo_dict, _models, n_simulations):
    return run_monte_carlo(
        team_hist=_team_hist,
        elo_df=_elo_dict,
        models=_models,
        n_simulations=n_simulations
    )

# ---------------------------------------------------------------------------
# Sidebar UI Setup
# ---------------------------------------------------------------------------

st.sidebar.markdown(f"<div style='text-align: center; padding: 15px 0;'><span style='font-size: 60px;'>🏆</span></div>", unsafe_allow_html=True)
st.sidebar.title("Simulation Console")
st.sidebar.markdown("---")

n_sims = st.sidebar.slider(
    "Monte Carlo Iterations",
    min_value=50,
    max_value=2000,
    value=200,
    step=50,
    help="Higher values yield more stable probability forecasts but take longer to run."
)

run_btn = st.sidebar.button("🚀 Run Monte Carlo Simulation", use_container_width=True)

# Maintain simulation state
if "mc_results" not in st.session_state:
    with st.spinner("Initializing first-run prediction pipeline (N=200)..."):
        st.session_state.mc_results = run_simulation_cached(team_hist, elo_dict, models, 200)
        st.session_state.n_sims = 200

if run_btn:
    with st.spinner(f"Running {n_sims} Monte Carlo tournament iterations..."):
        st.session_state.mc_results = run_monte_carlo(
            team_hist=team_hist,
            elo_df=elo_dict,
            models=models,
            n_simulations=n_sims
        )
        st.session_state.n_sims = n_sims
    st.sidebar.success(f"Successfully simulated {n_sims} tournaments!")

st.sidebar.markdown("---")
st.sidebar.markdown("### Model Properties")
st.sidebar.markdown(f"- **Goal Model**: LightGBM Poisson")
st.sidebar.markdown(f"- **Discipline Model**: LightGBM Poisson")
st.sidebar.markdown(f"- **Corner Model**: Ridge Regressor")
st.sidebar.markdown(f"- **Red Card Model**: Logistic Classifier")

# ---------------------------------------------------------------------------
# Main Banner & Dashboard Header
# ---------------------------------------------------------------------------

st.markdown(f"""
<div class="banner">
    <h1>FIFA World Cup 2026 Prediction Engine</h1>
    <p>Predicting the tournament using roll-form features, H2H statistics, and Elo-calibrated penalty shootouts. Dashboard running on <strong>{st.session_state.n_sims:,} simulations</strong>.</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Tabs Section
# ---------------------------------------------------------------------------

tab_bracket, tab_stats, tab_groups, tab_h2h = st.tabs([
    "🏆 Tournament Bracket", 
    "📊 Overall Statistics", 
    "⚽ Group Stage Standings", 
    "⚔️ Head-to-Head Simulator"
])

# ---------------------------------------------------------------------------
# TAB 1: Tournament Bracket
# ---------------------------------------------------------------------------

with tab_bracket:
    st.markdown("### Knockout Stages Bracket")
    st.caption("Hover over the team flags to see historical statistics, attack/defense ratings, and card indices. Win percentages indicate chance of progression to the next round.")
    
    mc_results = st.session_state.mc_results["match_results"]
    
    # Generate left and right columns
    left_r32 = "".join([get_match_box_html(mid, mc_results.get(mid), team_stats_cache) for mid in range(49, 57)])
    left_r16 = "".join([get_match_box_html(mid, mc_results.get(mid), team_stats_cache) for mid in range(65, 69)])
    left_qf  = "".join([get_match_box_html(mid, mc_results.get(mid), team_stats_cache) for mid in range(73, 75)])
    left_sf  = get_match_box_html(77, mc_results.get(77), team_stats_cache)
    
    right_sf  = get_match_box_html(78, mc_results.get(78), team_stats_cache)
    right_qf  = "".join([get_match_box_html(mid, mc_results.get(mid), team_stats_cache) for mid in range(75, 77)])
    right_r16 = "".join([get_match_box_html(mid, mc_results.get(mid), team_stats_cache) for mid in range(69, 73)])
    right_r32 = "".join([get_match_box_html(mid, mc_results.get(mid), team_stats_cache) for mid in range(57, 65)])
    
    final_match = mc_results.get(79)
    final_html = get_match_box_html(79, final_match, team_stats_cache)
    
    # Calculate champion
    top_champs = sorted(st.session_state.mc_results["champion_probs"].items(), key=lambda x: -x[1])
    champ_name = top_champs[0][0] if top_champs else "N/A"
    champ_prob = top_champs[0][1] if top_champs else 0.0
    
    champ_emoji = TEAM_TO_EMOJI.get(champ_name, "🏆")
    champ_flag = get_flag_html(champ_name, team_stats_cache)
    
    champion_html = f"""
    <div class="champion-box">
        <h3 style="margin: 0 0 5px 0; font-size: 15px; font-weight: 800; color: #eab308; letter-spacing: 0.05em;">{champ_emoji} PROJECTED CHAMPION</h3>
        <div style="display: flex; align-items: center; justify-content: center; gap: 8px; margin: 12px 0;">
            {champ_flag}
            <span style="font-size: 18px; font-weight: 800; color: #ffffff;">{champ_name}</span>
        </div>
        <div style="font-size: 14px; font-weight: 700; color: #eab308;">{champ_prob:.1%} Win Probability</div>
    </div>
    """
    
    bracket_html = f"""
    <div class="bracket-wrapper">
        <!-- Left Side: R32, R16, QF, SF -->
        <div class="bracket-column">
            <div class="center-header" style="font-size: 10px;">Round of 32</div>
            <div class="round">{left_r32}</div>
        </div>
        <div class="bracket-column">
            <div class="center-header" style="font-size: 10px;">Round of 16</div>
            <div class="round">{left_r16}</div>
        </div>
        <div class="bracket-column">
            <div class="center-header" style="font-size: 10px;">Quarter-Final</div>
            <div class="round">{left_qf}</div>
        </div>
        <div class="bracket-column">
            <div class="center-header" style="font-size: 10px;">Semi-Final</div>
            <div class="round">{left_sf}</div>
        </div>
        
        <!-- Center Column: Final and Champion -->
        <div class="bracket-column" style="justify-content: center; min-width: 230px; margin: 0 20px;">
            <div class="center-header" style="font-size: 14px; border-bottom: 2px solid #818cf8;">World Cup Final</div>
            {final_html}
            {champion_html}
        </div>
        
        <!-- Right Side: SF, QF, R16, R32 -->
        <div class="bracket-column">
            <div class="center-header" style="font-size: 10px;">Semi-Final</div>
            <div class="round">{right_sf}</div>
        </div>
        <div class="bracket-column">
            <div class="center-header" style="font-size: 10px;">Quarter-Final</div>
            <div class="round">{right_qf}</div>
        </div>
        <div class="bracket-column">
            <div class="center-header" style="font-size: 10px;">Round of 16</div>
            <div class="round">{right_r16}</div>
        </div>
        <div class="bracket-column">
            <div class="center-header" style="font-size: 10px;">Round of 32</div>
            <div class="round">{right_r32}</div>
        </div>
    </div>
    """
    
    st.markdown(bracket_html, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# TAB 2: Overall Statistics
# ---------------------------------------------------------------------------

with tab_stats:
    st.markdown("### Prediction Statistics Dashboard")
    
    col_chart1, col_chart2 = st.columns(2)
    
    # 1. Champion probabilities
    with col_chart1:
        st.markdown("#### 🏆 Champion Probability (Top 15)")
        top_champs_df = pd.DataFrame(
            [{"Team": t, "Probability": p} for t, p in top_champs[:15]]
        )
        fig1 = px.bar(
            top_champs_df, 
            x="Probability", 
            y="Team", 
            orientation="h",
            color="Probability",
            color_continuous_scale="Viridis",
            labels={"Probability": "Win Probability"}
        )
        fig1.update_layout(
            yaxis={"categoryorder": "total ascending"},
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#f1f5f9",
            margin=dict(l=0, r=0, t=20, b=0),
            height=400
        )
        st.plotly_chart(fig1, use_container_width=True)
        
    # 2. Finalist probabilities
    with col_chart2:
        st.markdown("#### 🥈 Finalist Probability (Top 15)")
        top_finalists = sorted(st.session_state.mc_results["finalist_probs"].items(), key=lambda x: -x[1])
        top_finalists_df = pd.DataFrame(
            [{"Team": t, "Probability": p} for t, p in top_finalists[:15]]
        )
        fig2 = px.bar(
            top_finalists_df, 
            x="Probability", 
            y="Team", 
            orientation="h",
            color="Probability",
            color_continuous_scale="Plasma",
            labels={"Probability": "Finalist Probability"}
        )
        fig2.update_layout(
            yaxis={"categoryorder": "total ascending"},
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#f1f5f9",
            margin=dict(l=0, r=0, t=20, b=0),
            height=400
        )
        st.plotly_chart(fig2, use_container_width=True)
        
    # 3. Overall Statistics Table
    st.markdown("#### 📊 Detailed Prediction Leaderboard")
    
    # Merge Champ & Finalist probs
    all_probs = []
    all_teams_wc = sorted(list(team_stats_cache.keys()))
    
    champ_probs_dict = dict(st.session_state.mc_results["champion_probs"])
    finalist_probs_dict = dict(st.session_state.mc_results["finalist_probs"])
    
    for team in all_teams_wc:
        c_prob = champ_probs_dict.get(team, 0.0)
        f_prob = finalist_probs_dict.get(team, 0.0)
        base = team_stats_cache.get(team, {})
        
        all_probs.append({
            "Team": team,
            "Emoji": TEAM_TO_EMOJI.get(team, "🏳️"),
            "WC Champ Prob": c_prob,
            "Finalist Prob": f_prob,
            "FIFA ELO": int(base.get("FIFA ELO Rating", 1500)),
            "Form Index": base.get("Recent Form (W5)", "50.0%"),
            "Attack Rating": float(base.get("Attack Strength (Avg Goals)", 1.0)),
            "Defense Rating": float(base.get("Defense Rating (Inverse)", 1.0)),
        })
        
    probs_df = pd.DataFrame(all_probs).sort_values("WC Champ Prob", ascending=False).reset_index(drop=True)
    probs_df.index += 1
    
    # Formatting
    st.dataframe(
        probs_df.style.format({
            "WC Champ Prob": "{:.2%}",
            "Finalist Prob": "{:.2%}",
            "Attack Rating": "{:.2f}",
            "Defense Rating": "{:.2f}"
        }),
        use_container_width=True,
        column_config={
            "Emoji": st.column_config.TextColumn("Flag", width="small"),
            "WC Champ Prob": st.column_config.ProgressColumn("Champ Prob", min_value=0.0, max_value=0.5, format="%.2f"),
            "Finalist Prob": st.column_config.ProgressColumn("Finalist Prob", min_value=0.0, max_value=0.7, format="%.2f"),
        }
    )

# ---------------------------------------------------------------------------
# TAB 3: Group Standings Standings
# ---------------------------------------------------------------------------

with tab_groups:
    st.markdown("### Simulated Group Stage Standings")
    st.caption("Group standings resolved using simulated match outcomes based on the most common scorelines.")
    
    # Build standings per group using group stage match aggregation
    group_fixtures = get_group_fixtures()
    group_sim_results = []
    
    for fixture in group_fixtures:
        mid = fixture["match_id"]
        res = mc_results.get(mid)
        if res:
            group_sim_results.append({
                "home_team": res["home_team"],
                "away_team": res["away_team"],
                "home_goals": res["most_common_home_goals"],
                "away_goals": res["most_common_away_goals"],
                "home_yellow": 0, "away_yellow": 0, "home_red": 0, "away_red": 0, # dummy values for resolver
                "group": fixture["group"]
            })
            
    # Group results mapping
    group_split = {}
    for res in group_sim_results:
        grp = res["group"]
        if grp not in group_split:
            group_split[grp] = []
        group_split[grp].append(res)
        
    cols = st.columns(3)
    group_names = sorted(list(WC2026_GROUPS.keys()))
    
    for i, grp in enumerate(group_names):
        col_idx = i % 3
        with cols[col_idx]:
            st.markdown(f"#### 📦 Group {grp}")
            
            results = group_split.get(grp, [])
            if results:
                standings = resolve_group_standings(results)
                
                # Format DF
                standings_display = standings[["rank", "team", "played", "pts", "gd", "gf"]].copy()
                standings_display["Flag"] = standings_display["team"].apply(lambda t: TEAM_TO_EMOJI.get(t, "🏳️"))
                standings_display = standings_display[["rank", "Flag", "team", "played", "pts", "gd", "gf"]]
                standings_display.columns = ["Pos", "Flag", "Team", "P", "Pts", "GD", "GF"]
                
                # Highlight top two qualifiers
                def highlight_qualifiers(row):
                    if row["Pos"] <= 2:
                        return ["background-color: rgba(99, 102, 241, 0.15)"] * len(row)
                    return [""] * len(row)
                
                st.dataframe(
                    standings_display.style.apply(highlight_qualifiers, axis=1),
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.info("No group stage fixtures simulated.")

# ---------------------------------------------------------------------------
# TAB 4: Head-to-Head Simulator
# ---------------------------------------------------------------------------

with tab_h2h:
    st.markdown("### ⚔️ Live Match Simulator")
    st.write("Select two teams to simulate a match on the fly using our trained ML models.")
    
    all_teams_sorted = sorted(list(team_stats_cache.keys()))
    
    col_team1, col_team2 = st.columns(2)
    with col_team1:
        t1 = st.selectbox("Home Team", all_teams_sorted, index=all_teams_sorted.index("Argentina"))
    with col_team2:
        t2 = st.selectbox("Away Team", all_teams_sorted, index=all_teams_sorted.index("France"))
        
    if t1 == t2:
        st.warning("Please select two different teams to simulate a match.")
    else:
        # Run feature builder & predict parameters
        feature_row = build_prediction_row(t1, t2, team_hist, elo_dict, TOURNAMENT_DATE)
        pred = predict_lambdas(models, feature_row)
        
        # Display side-by-side stats comparison
        col_stats1, col_stats2 = st.columns(2)
        
        with col_stats1:
            st.markdown(f"#### {TEAM_TO_EMOJI.get(t1, '')} {t1} (Home)")
            st.write(f"- **ELO Rating**: {team_stats_cache[t1]['FIFA ELO Rating']}")
            st.write(f"- **Recent Form**: {team_stats_cache[t1]['Recent Form (W5)']}")
            st.write(f"- **Goal Model Scored λ**: `{pred.home_goals_lambda:.3f}`")
            st.write(f"- **Corner Model λ**: `{pred.home_corners_lambda:.2f}`")
            st.write(f"- **Discipline (Cards) λ**: `{pred.home_yellow_lambda:.2f}`")
            st.write(f"- **Red Card Probability**: `{pred.home_red_prob:.2%}`")
            
        with col_stats2:
            st.markdown(f"#### {TEAM_TO_EMOJI.get(t2, '')} {t2} (Away)")
            st.write(f"- **ELO Rating**: {team_stats_cache[t2]['FIFA ELO Rating']}")
            st.write(f"- **Recent Form**: {team_stats_cache[t2]['Recent Form (W5)']}")
            st.write(f"- **Goal Model Scored λ**: `{pred.away_goals_lambda:.3f}`")
            st.write(f"- **Corner Model λ**: `{pred.away_corners_lambda:.2f}`")
            st.write(f"- **Discipline (Cards) λ**: `{pred.away_yellow_lambda:.2f}`")
            st.write(f"- **Red Card Probability**: `{pred.away_red_prob:.2%}`")
            
        st.markdown("---")
        
        # Live 1,000 matches simulation
        sim_btn = st.button("⚽ Simulate Match (1,000 runs)", use_container_width=True)
        
        if sim_btn:
            with st.spinner("Simulating..."):
                home_wins = 0
                draws = 0
                away_wins = 0
                goals_scored = []
                cards_issued = []
                corners_won = []
                
                # Sigmoid shootout winner calculation
                elo_diff = pred.home_elo - pred.away_elo
                shootout_prob = 1.0 / (1.0 + np.exp(-elo_diff / 400.0))
                shootout_prob = float(np.clip(shootout_prob, 0.35, 0.65))
                
                for _ in range(1000):
                    hg = int(np.random.poisson(pred.home_goals_lambda))
                    ag = int(np.random.poisson(pred.away_goals_lambda))
                    
                    goals_scored.append((hg, ag))
                    
                    # Accumulate wins
                    if hg > ag:
                        home_wins += 1
                    elif hg < ag:
                        away_wins += 1
                    else:
                        draws += 1
                        
                # Outcome probabilities
                p_home = home_wins / 1000.0
                p_draw = draws / 1000.0
                p_away = away_wins / 1000.0
                
                # Format score outputs
                score_freq = pd.Series(goals_scored).value_counts()
                top_score = score_freq.index[0]
                
                st.markdown("### Simulation Results")
                
                # Probability progress bar
                col_prob1, col_prob2, col_prob3 = st.columns(3)
                with col_prob1:
                    st.metric(f"{t1} Wins", f"{p_home:.1%}")
                    st.progress(p_home)
                with col_prob2:
                    st.metric("Draws", f"{p_draw:.1%}")
                    st.progress(p_draw)
                with col_prob3:
                    st.metric(f"{t2} Wins", f"{p_away:.1%}")
                    st.progress(p_away)
                    
                # Details
                col_det1, col_det2 = st.columns(2)
                with col_det1:
                    st.markdown("<div class='sim-card'>", unsafe_allow_html=True)
                    st.markdown("#### 🥅 Expected Match Stats")
                    st.write(f"- **Most Common Score**: `{top_score[0]} - {top_score[1]}` ({score_freq.iloc[0] / 1000:.1%} frequency)")
                    st.write(f"- **Avg Predicted Goals**: `{t1}`: **{pred.home_goals_lambda:.2f}** vs `{t2}`: **{pred.away_goals_lambda:.2f}**")
                    st.write(f"- **Avg Predicted Corners**: `{t1}`: **{pred.home_corners_lambda:.1f}** vs `{t2}`: **{pred.away_corners_lambda:.1f}**")
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                with col_det2:
                    st.markdown("<div class='sim-card'>", unsafe_allow_html=True)
                    st.markdown("#### 🟨 Expected Discipline Stats")
                    st.write(f"- **Expected Yellow Cards**: `{t1}`: **{pred.home_yellow_lambda:.2f}** vs `{t2}`: **{pred.away_yellow_lambda:.2f}**")
                    st.write(f"- **Red Card Probability**: `{t1}`: **{pred.home_red_prob:.1%}** vs `{t2}`: **{pred.away_red_prob:.1%}**")
                    st.write(f"- **Elo-Calibrated Shootout win prob (if draw)**: `{t1}`: **{shootout_prob:.1%}** vs `{t2}`: **{1-shootout_prob:.1%}**")
                    st.markdown("</div>", unsafe_allow_html=True)
