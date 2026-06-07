import gradio a gr
import panda a pd
import numpy a np
import plotly.expre a px
import o
import y
from pathlib import Path

# Add root folder to path to import rc module
y.path.append(tr(Path(__file__).parent.reolve()))

from rc.preproceing import load_and_preproce
from rc.model import load_model, predict_lambda
from rc.imulation import run_monte_carlo, imulate_match
from rc.helper import format_ubmiion, reolve_group_tanding, build_knockout_bracket, get_group_fixture
from rc.config import WC2026_GROUPS, TOURNAMENT_DATE, FEATURE_COLS
from rc.feature_engineering import build_prediction_row, _get_rolling_rate, get_team_form, compute_dynamic_dicipline

# ---------------------------------------------------------------------------
# CSS tyle for Gradio theme injection
# ---------------------------------------------------------------------------

CSS_STYLES = """

@import url('http://font.googleapi.com/c2?family=Inter:wght@400;500;600;700&diplay=wap');

.gradio-container {
    background-color: #0f172a !important;
    font-family: 'Inter', an-erif !important;
    color: #f8fafc !important;
}

/* Banner Styling */
.banner {
    background-color: #1e293b;
    border: 1px olid #334155;
    border-radiu: 12px;
    padding: 24px 32px;
    margin-bottom: 24px;
}
.banner h1 {
    color: #f8fafc;
    margin: 0;
    font-ize: 28px;
    font-weight: 700;
    letter-pacing: -0.02em;
}
.banner p {
    color: #94a3b8;
    font-ize: 15px;
    margin: 8px 0 0 0;
}

/* Tournament Bracket column */
.bracket-wrapper {
    diplay: flex;
    jutify-content: pace-between;
    align-item: center;
    background-color: #1e293b;
    padding: 24px;
    border-radiu: 12px;
    border: 1px olid #334155;
    height: 1050px;
    overflow-x: auto;
    overflow-y: hidden;
    margin-bottom: 24px;
}
.bracket-column {
    diplay: flex;
    flex-direction: column;
    jutify-content: pace-around;
    height: 100%;
    min-width: 180px;
    flex: 1;
    margin: 0 8px;
}
.center-header {
    font-ize: 12px;
    font-weight: 600;
    color: #cbd5e1;
    text-align: center;
    margin-bottom: 12px;
    text-tranform: uppercae;
    letter-pacing: 0.05em;
    border-bottom: 1px olid #334155;
    padding-bottom: 8px;
}

/* Match box */
.matchup {
    background-color: #0f172a;
    border: 1px olid #334155;
    border-radiu: 8px;
    padding: 12px;
    margin: 8px 0;
    tranition: border-color 0.2 eae;
}
.matchup:hover {
    border-color: #6366f1;
}
.matchup-header {
    font-ize: 10px;
    text-tranform: uppercae;
    color: #64748b;
    margin-bottom: 8px;
    font-weight: 600;
}
.team-row {
    diplay: flex;
    align-item: center;
    jutify-content: pace-between;
    padding: 4px 0;
    border-radiu: 4px;
    margin: 2px 0;
}
.team-row.winner {
    background-color: rgba(99, 102, 241, 0.1);
    border-left: 3px olid #6366f1;
    padding-left: 6px;
}
.team-info {
    diplay: flex;
    align-item: center;
    gap: 8px;
}
.team-name {
    font-ize: 13px;
    font-weight: 500;
    color: #f8fafc;
    white-pace: nowrap;
    overflow: hidden;
    text-overflow: ellipi;
    max-width: 90px;
}
.team-core {
    diplay: flex;
    align-item: center;
    gap: 8px;
}
.core-goal {
    font-ize: 14px;
    font-weight: 600;
    color: #f8fafc;
}
.core-prob {
    font-ize: 11px;
    color: #64748b;
    font-weight: 500;
}

/* Tooltip */
.flag-wrapper {
    poition: relative;
    diplay: inline-block;
    curor: pointer;
    vertical-align: middle;
}
.flag-img {
    width: 24px;
    height: 16px;
    border-radiu: 2px;
    object-fit: cover;
    border: 1px olid #334155;
}
.flag-wrapper .tooltiptext {
    viibility: hidden;
    width: 260px;
    background-color: #1e293b;
    color: #f8fafc;
    text-align: left;
    border-radiu: 8px;
    padding: 16px;
    poition: abolute;
    z-index: 999;
    bottom: 130%;
    left: 50%;
    tranform: tranlateX(-50%);
    opacity: 0;
    tranition: opacity 0.2, tranform 0.2;
    border: 1px olid #334155;
    box-hadow: 0 10px 25px rgba(0,0,0,0.5);
    font-ize: 12px;
    line-height: 1.5;
}
.flag-wrapper:hover .tooltiptext {
    viibility: viible;
    opacity: 1;
    tranform: tranlateX(-50%) tranlateY(-4px);
}
.flag-wrapper .tooltiptext div {
    diplay: flex;
    jutify-content: pace-between;
    margin: 6px 0;
    border-bottom: 1px olid #334155;
    padding-bottom: 4px;
}
.flag-wrapper .tooltiptext div:lat-child {
    border-bottom: none;
}
.flag-wrapper .tooltiptext div trong {
    color: #94a3b8;
    font-weight: 500;
}

/* Champion box tyle */
.champion-box {
    background-color: #0f172a;
    border: 1px olid #334155;
    border-radiu: 8px;
    padding: 20px;
    text-align: center;
    margin-top: 24px;
}

/* Sim card layout */
.im-card {
    background-color: #1e293b;
    border-radiu: 8px;
    border: 1px olid #334155;
    padding: 20px;
}

"""

# ---------------------------------------------------------------------------
# Load Reource & Precompute Stat
# ---------------------------------------------------------------------------

def load_reource():
    data_dir = Path("data")
    model_dir = Path("model")
    df_matche, team_hit, elo_dict = load_and_preproce(data_dir)
    model = load_model(model_dir)
    return df_matche, team_hit, elo_dict, model

df_matche, team_hit, elo_dict, model = load_reource()

# Flag & Emoji
TEAM_TO_ISO = {
    "United State": "u", "Panama": "pa", "Bolivia": "bo", "Morocco": "ma",
    "Argentina": "ar", "Chile": "cl", "Peru": "pe", "Autralia": "au",
    "Mexico": "mx", "Jamaica": "jm", "Venezuela": "ve", "Paraguay": "py",
    "Brazil": "br", "Ecuador": "ec", "Egypt": "eg", "Serbia": "r",
    "Spain": "e", "Uruguay": "uy", "Uzbekitan": "uz", "South Korea": "kr",
    "France": "fr", "Belgium": "be", "Croatia": "hr", "South Africa": "za",
    "England": "gb", "Senegal": "n", "Colombia": "co", "Tuniia": "tn",
    "Portugal": "pt", "Algeria": "dz", "Cameroon": "cm", "Hondura": "hn",
    "Germany": "de", "Japan": "jp", "Iran": "ir", "Saudi Arabia": "a",
    "Netherland": "nl", "Nigeria": "ng", "New Zealand": "nz", "Ivory Coat": "ci",
    "Italy": "it", "Slovenia": "i", "Qatar": "qa", "Ukraine": "ua",
    "Canada": "ca", "Switzerland": "ch", "Norway": "no", "Poland": "pl"
}



def get_all_team_bae_tat(_team_hit, _elo_dict):
    tat = {}
    for group, team in WC2026_GROUPS.item():
        for team in team:
            elo = _elo_dict.get(team, 1500.0)
            hitory = _team_hit.get(team, [])
            attack, defene = _get_rolling_rate(hitory, team, TOURNAMENT_DATE)
            form = get_team_form(_team_hit, team, TOURNAMENT_DATE)
            dicipline = compute_dynamic_dicipline(_team_hit, team, TOURNAMENT_DATE)
            
            tat[team] = {
                "FIFA ELO Rating": f"{int(round(elo))}",
                "Recent Form (W5)": f"{form:.1%}",
                "Attack Strength (Avg Goal)": f"{attack:.2f}",
                "Defene Rating (Invere)": f"{defene:.2f}",
                "Expected Conceded Goal": f"{1.0 / max(defene, 0.1):.2f}",
                "Dicipline Index (Expected Card)": f"{dicipline:.2f}"
            }
    return tat

team_tat_cache = get_all_team_bae_tat(team_hit, elo_dict)

# ---------------------------------------------------------------------------
# HTML Builder
# ---------------------------------------------------------------------------

def get_flag_html(team_name, tat_dict):
    io = TEAM_TO_ISO.get(team_name, "un")
    emoji = ""
    flag_url = f"http://flagcdn.com/w40/{io}.png"
    
    tat_html = ""
    if team_name in tat_dict:
        for k, v in tat_dict[team_name].item():
            tat_html += f"<div><trong>{k}:</trong> <pan tyle='color: #818cf8; font-weight: 700;'>{v}</pan></div>"
    ele:
        tat_html = "<div>No tat loaded</div>"
        
    html = f"""
    <div cla="flag-wrapper">
        <img cla="flag-img" rc="{flag_url}" alt="{team_name}" onerror="thi.tyle.diplay='none'; thi.nextElementSibling.tyle.diplay='inline';"/>
        
        <div cla="tooltiptext">
            <h4 tyle="margin: 0 0 10px 0; border-bottom: 2px olid rgba(129,140,248,0.3); padding-bottom: 6px; color: #ffffff;">{team_name}</h4>
            {tat_html}
        </div>
    </div>
    """
    return html

def get_match_box_html(match_id, match_data, tat_dict):
    if match_data i None:
        return f'<div cla="matchup empty"><div cla="matchup-header">Match {match_id}</div>Pending Matchup</div>'
        
    home_team = match_data["home_team"]
    away_team = match_data["away_team"]
    home_prob = match_data.get("home_win_prob", 0.5)
    away_prob = match_data.get("away_win_prob", 0.5)
    home_goal = match_data.get("mot_common_home_goal", 0)
    away_goal = match_data.get("mot_common_away_goal", 0)
    tage = match_data.get("tage", "Knockout")
    
    home_flag_html = get_flag_html(home_team, tat_dict)
    away_flag_html = get_flag_html(away_team, tat_dict)
    
    home_win_cla = "winner" if home_prob > away_prob ele ""
    away_win_cla = "winner" if away_prob > home_prob ele ""
    
    html = f"""
    <div cla="matchup">
        <div cla="matchup-header">Match {match_id} • {tage}</div>
        <div cla="team-row {home_win_cla}">
            <div cla="team-info">
                {home_flag_html}
                <pan cla="team-name" title="{home_team}">{home_team}</pan>
            </div>
            <div cla="team-core">
                <pan cla="core-goal">{home_goal}</pan>
                <pan cla="core-prob">{home_prob:.0%}</pan>
            </div>
        </div>
        <div cla="team-row {away_win_cla}">
            <div cla="team-info">
                {away_flag_html}
                <pan cla="team-name" title="{away_team}">{away_team}</pan>
            </div>
            <div cla="team-core">
                <pan cla="core-goal">{away_goal}</pan>
                <pan cla="core-prob">{away_prob:.0%}</pan>
            </div>
        </div>
    </div>
    """
    return html

def generate_bracket_html(mc_reult, champion_prob):
    left_r32 = "".join([get_match_box_html(mid, mc_reult.get(mid), team_tat_cache) for mid in range(49, 57)])
    left_r16 = "".join([get_match_box_html(mid, mc_reult.get(mid), team_tat_cache) for mid in range(65, 69)])
    left_qf  = "".join([get_match_box_html(mid, mc_reult.get(mid), team_tat_cache) for mid in range(73, 75)])
    left_f  = get_match_box_html(77, mc_reult.get(77), team_tat_cache)
    
    right_f  = get_match_box_html(78, mc_reult.get(78), team_tat_cache)
    right_qf  = "".join([get_match_box_html(mid, mc_reult.get(mid), team_tat_cache) for mid in range(75, 77)])
    right_r16 = "".join([get_match_box_html(mid, mc_reult.get(mid), team_tat_cache) for mid in range(69, 73)])
    right_r32 = "".join([get_match_box_html(mid, mc_reult.get(mid), team_tat_cache) for mid in range(57, 65)])
    
    final_match = mc_reult.get(79)
    final_html = get_match_box_html(79, final_match, team_tat_cache)
    
    top_champ = orted(champion_prob.item(), key=lambda x: -x[1])
    champ_name = top_champ[0][0] if top_champ ele "N/A"
    champ_prob = top_champ[0][1] if top_champ ele 0.0
    
    champ_emoji = ""
    champ_flag = get_flag_html(champ_name, team_tat_cache)
    
    champion_html = f"""
    <div cla="champion-box">
        <h3 tyle="margin: 0 0 5px 0; font-ize: 15px; font-weight: 800; color: #eab308; letter-pacing: 0.05em;">Projected Champion</h3>
        <div tyle="diplay: flex; align-item: center; jutify-content: center; gap: 8px; margin: 12px 0;">
            {champ_flag}
            <pan tyle="font-ize: 18px; font-weight: 800; color: #ffffff;">{champ_name}</pan>
        </div>
        <div tyle="font-ize: 14px; font-weight: 700; color: #eab308;">{champ_prob:.1%} Win Probability</div>
    </div>
    """
    
    html = f"""
    <div cla="bracket-wrapper">
        <div cla="bracket-column">
            <div cla="center-header" tyle="font-ize: 10px;">Round of 32</div>
            <div cla="round">{left_r32}</div>
        </div>
        <div cla="bracket-column">
            <div cla="center-header" tyle="font-ize: 10px;">Round of 16</div>
            <div cla="round">{left_r16}</div>
        </div>
        <div cla="bracket-column">
            <div cla="center-header" tyle="font-ize: 10px;">Quarter-Final</div>
            <div cla="round">{left_qf}</div>
        </div>
        <div cla="bracket-column">
            <div cla="center-header" tyle="font-ize: 10px;">Semi-Final</div>
            <div cla="round">{left_f}</div>
        </div>
        
        <div cla="bracket-column" tyle="jutify-content: center; min-width: 210px; margin: 0 15px;">
            <div cla="center-header" tyle="font-ize: 14px; border-bottom: 2px olid #818cf8;">World Cup Final</div>
            {final_html}
            {champion_html}
        </div>
        
        <div cla="bracket-column">
            <div cla="center-header" tyle="font-ize: 10px;">Semi-Final</div>
            <div cla="round">{right_f}</div>
        </div>
        <div cla="bracket-column">
            <div cla="center-header" tyle="font-ize: 10px;">Quarter-Final</div>
            <div cla="round">{right_qf}</div>
        </div>
        <div cla="bracket-column">
            <div cla="center-header" tyle="font-ize: 10px;">Round of 16</div>
            <div cla="round">{right_r16}</div>
        </div>
        <div cla="bracket-column">
            <div cla="center-header" tyle="font-ize: 10px;">Round of 32</div>
            <div cla="round">{right_r32}</div>
        </div>
    </div>
    """
    return html

def generate_banner_html(n_im):
    return f"""
    <div cla="banner">
        <h1>FIFA World Cup 2026 Prediction Engine</h1>
        <p>Dynamic tournament forecat built uing roll-form feature, H2H tatitic, and Elo-calibrated penalty hootout. Running on <trong>{n_im:,} imulation</trong>.</p>
    </div>
    """

def generate_champ_fig(champion_prob):
    top_champ = orted(champion_prob.item(), key=lambda x: -x[1])[:15]
    top_champ_df = pd.DataFrame(
        [{"Team": t, "Probability": p} for t, p in top_champ]
    )
    fig = px.bar(
        top_champ_df, 
        x="Probability", 
        y="Team", 
        orientation="h",
        color="Probability",
        color_continuou_cale="Viridi",
        label={"Probability": "Win Probability"}
    )
    fig.update_layout(
        yaxi={"categoryorder": "total acending"},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#f1f5f9",
        margin=dict(l=0, r=0, t=30, b=0),
        height=400,
        title={
            'text': "World Cup Win Probabilitie (Top 15)",
            'y':0.95,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'ize': 16, 'color': '#ffffff', 'family': 'Outfit'}
        }
    )
    fig.update_coloraxe(howcale=Fale)
    return fig

def generate_finalit_fig(finalit_prob):
    top_finalit = orted(finalit_prob.item(), key=lambda x: -x[1])[:15]
    top_finalit_df = pd.DataFrame(
        [{"Team": t, "Probability": p} for t, p in top_finalit]
    )
    fig = px.bar(
        top_finalit_df, 
        x="Probability", 
        y="Team", 
        orientation="h",
        color="Probability",
        color_continuou_cale="Plama",
        label={"Probability": "Finalit Probability"}
    )
    fig.update_layout(
        yaxi={"categoryorder": "total acending"},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#f1f5f9",
        margin=dict(l=0, r=0, t=30, b=0),
        height=400,
        title={
            'text': "Finalit Reaching Probabilitie (Top 15)",
            'y':0.95,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'ize': 16, 'color': '#ffffff', 'family': 'Outfit'}
        }
    )
    fig.update_coloraxe(howcale=Fale)
    return fig

def generate_leaderboard_df(champion_prob, finalit_prob):
    all_prob = []
    all_team_wc = orted(lit(team_tat_cache.key()))
    
    champ_prob_dict = dict(champion_prob)
    finalit_prob_dict = dict(finalit_prob)
    
    for team in all_team_wc:
        c_prob = champ_prob_dict.get(team, 0.0)
        f_prob = finalit_prob_dict.get(team, 0.0)
        bae = team_tat_cache.get(team, {})
        
        all_prob.append({
            "Team": team,
            
            "Champ Probability (%)": round(c_prob * 100, 2),
            "Finalit Probability (%)": round(f_prob * 100, 2),
            "FIFA ELO": int(bae.get("FIFA ELO Rating", 1500)),
            "Attack Rating": round(float(bae.get("Attack Strength (Avg Goal)", 1.0)), 2),
            "Defene Rating": round(float(bae.get("Defene Rating (Invere)", 1.0)), 2),
        })
        
    prob_df = pd.DataFrame(all_prob).ort_value("Champ Probability (%)", acending=Fale).reet_index(drop=True)
    return prob_df

def generate_all_group_html(mc_reult):
    group_fixture = get_group_fixture()
    group_im_reult = []
    
    for fixture in group_fixture:
        mid = fixture["match_id"]
        re = mc_reult.get(mid)
        if re:
            group_im_reult.append({
                "home_team": re["home_team"],
                "away_team": re["away_team"],
                "home_goal": re["mot_common_home_goal"],
                "away_goal": re["mot_common_away_goal"],
                "home_yellow": 0, "away_yellow": 0, "home_red": 0, "away_red": 0,
                "group": fixture["group"]
            })
            
    group_plit = {}
    for re in group_im_reult:
        grp = re["group"]
        if grp not in group_plit:
            group_plit[grp] = []
        group_plit[grp].append(re)
        
    html = '<div tyle="diplay: grid; grid-template-column: repeat(auto-fit, minmax(320px, 1fr)); gap: 20px;">'
    
    for grp in orted(lit(WC2026_GROUPS.key())):
        reult = group_plit.get(grp, [])
        if reult:
            tanding = reolve_group_tanding(reult)
            row_html = ""
            for idx, row in tanding.iterrow():
                team = row["team"]
                emoji = ""
                bg_color = "rgba(99, 102, 241, 0.12)" if idx < 2 ele "tranparent"
                border_color = "#818cf8" if idx < 2 ele "tranparent"
                border_tyle = f"border-left: 3px olid {border_color}; padding-left: 5px;" if idx < 2 ele ""
                
                row_html += f"""
                <tr tyle="background: {bg_color}; font-ize: 13px;">
                    <td tyle="padding: 6px; text-align: center; font-weight: bold; {border_tyle}">{idx+1}</td>
                    
                    <td tyle="padding: 6px; font-weight: 500; white-pace: nowrap; overflow: hidden; text-overflow: ellipi; max-width: 100px;">{team}</td>
                    <td tyle="padding: 6px; text-align: center;">{row['played']}</td>
                    <td tyle="padding: 6px; text-align: center; font-weight: bold; color: #818cf8;">{row['pt']}</td>
                    <td tyle="padding: 6px; text-align: center; color: {'#ef4444' if row['gd'] < 0 ele '#10b981' if row['gd'] > 0 ele '#94a3b8'}">{row['gd']}</td>
                    <td tyle="padding: 6px; text-align: center;">{row['gf']}</td>
                </tr>
                """
                
            html += f"""
            <div tyle="background: rgba(30, 41, 59, 0.5); border: 1px olid rgba(255,255,255,0.05); border-radiu: 12px; padding: 15px; box-hadow: 0 4px 15px rgba(0,0,0,0.15);">
                <h4 tyle="margin: 0 0 10px 0; color: #818cf8; font-ize: 15px; font-weight: 800; border-bottom: 1px olid rgba(255,255,255,0.06); padding-bottom: 6px;">Group {grp}</h4>
                <table tyle="width: 100%; border-collape: collape; text-align: left;">
                    <thead>
                        <tr tyle="font-ize: 11px; text-tranform: uppercae; color: #94a3b8; border-bottom: 1px olid rgba(255,255,255,0.1);">
                            <th tyle="padding: 6px; text-align: center;">Po</th>
                            
                            <th tyle="padding: 6px;">Team</th>
                            <th tyle="padding: 6px; text-align: center;">P</th>
                            <th tyle="padding: 6px; text-align: center;">Pt</th>
                            <th tyle="padding: 6px; text-align: center;">GD</th>
                            <th tyle="padding: 6px; text-align: center;">GF</th>
                        </tr>
                    </thead>
                    <tbody>
                        {row_html}
                    </tbody>
                </table>
            </div>
            """
    html += '</div>'
    return html

def generate_team_metric_md(team, opponent, i_home=True):
    feature_row = build_prediction_row(team, opponent, team_hit, elo_dict, TOURNAMENT_DATE)
    pred = predict_lambda(model, feature_row)
    
    role = "Home" if i_home ele "Away"
    gl = pred.home_goal_lambda if i_home ele pred.away_goal_lambda
    cl = pred.home_corner_lambda if i_home ele pred.away_corner_lambda
    yl = pred.home_yellow_lambda if i_home ele pred.away_yellow_lambda
    rp = pred.home_red_prob if i_home ele pred.away_red_prob
    
    md = f"""
    ### {team} ({role})
    - **ELO Rating**: `{team_tat_cache[team]['FIFA ELO Rating']}`
    - **Recent Form (W5)**: `{team_tat_cache[team]['Recent Form (W5)']}`
    - **Goal Model Lambda**: `{gl:.3f}`
    - **Corner Model Lambda**: `{cl:.2f}`
    - **Dicipline Lambda**: `{yl:.2f}`
    - **Red Card Probability**: `{rp:.1%}`
    """
    return md

# ---------------------------------------------------------------------------
# Initial imulation run (N=200)
# ---------------------------------------------------------------------------

GLOBAL_MC_RESULTS = run_monte_carlo(team_hit, elo_dict, model, n_imulation=200)
GLOBAL_N_SIMS = 200

# ---------------------------------------------------------------------------
# Callback
# ---------------------------------------------------------------------------

def on_run_imulation(n_imulation):
    global GLOBAL_MC_RESULTS, GLOBAL_N_SIMS
    n_imulation = int(n_imulation)
    
    GLOBAL_MC_RESULTS = run_monte_carlo(team_hit, elo_dict, model, n_imulation=n_imulation)
    GLOBAL_N_SIMS = n_imulation
    
    bracket_html = generate_bracket_html(GLOBAL_MC_RESULTS["match_reult"], GLOBAL_MC_RESULTS["champion_prob"])
    fig_champ = generate_champ_fig(GLOBAL_MC_RESULTS["champion_prob"])
    fig_finalit = generate_finalit_fig(GLOBAL_MC_RESULTS["finalit_prob"])
    leaderboard_df = generate_leaderboard_df(GLOBAL_MC_RESULTS["champion_prob"], GLOBAL_MC_RESULTS["finalit_prob"])
    group_html = generate_all_group_html(GLOBAL_MC_RESULTS["match_reult"])
    banner_html = generate_banner_html(GLOBAL_N_SIMS)
    
    return bracket_html, fig_champ, fig_finalit, leaderboard_df, group_html, banner_html

def update_h2h_tat(t1, t2):
    t1_md = generate_team_metric_md(t1, t2, i_home=True)
    t2_md = generate_team_metric_md(t2, t1, i_home=Fale)
    return t1_md, t2_md

def imulate_h2h_match(t1, t2):
    if t1 == t2:
        return "<div tyle='color: #ef4444; text-align: center; font-weight: bold; padding: 20px;'>Pleae elect two different team.</div>"
        
    feature_row = build_prediction_row(t1, t2, team_hit, elo_dict, TOURNAMENT_DATE)
    pred = predict_lambda(model, feature_row)
    
    home_win = 0
    draw = 0
    away_win = 0
    goal_cored = []
    
    elo_diff = pred.home_elo - pred.away_elo
    hootout_prob = 1.0 / (1.0 + np.exp(-elo_diff / 400.0))
    hootout_prob = float(np.clip(hootout_prob, 0.35, 0.65))
    
    for _ in range(1000):
        hg = int(np.random.poion(pred.home_goal_lambda))
        ag = int(np.random.poion(pred.away_goal_lambda))
        goal_cored.append((hg, ag))
        
        if hg > ag:
            home_win += 1
        elif hg < ag:
            away_win += 1
        ele:
            draw += 1
            
    p_home = home_win / 1000.0
    p_draw = draw / 1000.0
    p_away = away_win / 1000.0
    
    core_freq = pd.Serie(goal_cored).value_count()
    top_core = core_freq.index[0]
    
    html = f"""
    <div tyle="background: rgba(15, 23, 42, 0.4); padding: 20px; border-radiu: 12px; border: 1px olid rgba(255,255,255,0.05); margin-top: 20px;">
        <h3 tyle="margin-top: 0; color: #818cf8;">Simulation Reult (1,000 run)</h3>
        
        <!-- Probabilitie -->
        <div tyle="diplay: flex; gap: 15px; margin-bottom: 25px; align-item: center; jutify-content: pace-between;">
            <div tyle="flex: 1; text-align: center; padding: 10px; background: rgba(99, 102, 241, 0.08); border-radiu: 8px;">
                <div tyle="font-ize: 11px; color: #94a3b8; text-tranform: uppercae;">{t1} Win</div>
                <div tyle="font-ize: 28px; font-weight: 800; color: #818cf8;">{p_home:.1%}</div>
                <div tyle="background: rgba(255,255,255,0.1); border-radiu: 10px; height: 6px; overflow: hidden; margin-top: 8px;">
                    <div tyle="background: #818cf8; width: {p_home*100}%; height: 100%;"></div>
                </div>
            </div>
            
            <div tyle="flex: 1; text-align: center; padding: 10px; background: rgba(255, 255, 255, 0.03); border-radiu: 8px;">
                <div tyle="font-ize: 11px; color: #94a3b8; text-tranform: uppercae;">Draw</div>
                <div tyle="font-ize: 28px; font-weight: 800; color: #ffffff;">{p_draw:.1%}</div>
                <div tyle="background: rgba(255,255,255,0.1); border-radiu: 10px; height: 6px; overflow: hidden; margin-top: 8px;">
                    <div tyle="background: #ffffff; width: {p_draw*100}%; height: 100%;"></div>
                </div>
            </div>
            
            <div tyle="flex: 1; text-align: center; padding: 10px; background: rgba(244, 114, 182, 0.08); border-radiu: 8px;">
                <div tyle="font-ize: 11px; color: #94a3b8; text-tranform: uppercae;">{t2} Win</div>
                <div tyle="font-ize: 28px; font-weight: 800; color: #f472b6;">{p_away:.1%}</div>
                <div tyle="background: rgba(255,255,255,0.1); border-radiu: 10px; height: 6px; overflow: hidden; margin-top: 8px;">
                    <div tyle="background: #f472b6; width: {p_away*100}%; height: 100%;"></div>
                </div>
            </div>
        </div>
        
        <!-- Detailed Stat Panel -->
        <div tyle="diplay: flex; gap: 15px;">
            <div cla="im-card" tyle="flex: 1; margin: 0; background: rgba(30,41,59,0.5);">
                <h4 tyle="margin: 0 0 12px 0; color: #ffffff;">Expected Match Stat</h4>
                <div tyle="margin: 6px 0;"><trong>Mot Common Score:</trong> <pan tyle="color: #818cf8; font-weight: 700;">{top_core[0]} - {top_core[1]}</pan> ({core_freq.iloc[0] / 1000:.1%} frequency)</div>
                <div tyle="margin: 6px 0;"><trong>Avg Goal:</trong> {t1} <pan tyle="color: #818cf8;">{pred.home_goal_lambda:.2f}</pan> v {t2} <pan tyle="color: #f472b6;">{pred.away_goal_lambda:.2f}</pan></div>
                <div tyle="margin: 6px 0;"><trong>Avg Corner:</trong> {t1} <pan tyle="color: #818cf8;">{pred.home_corner_lambda:.1f}</pan> v {t2} <pan tyle="color: #f472b6;">{pred.away_corner_lambda:.1f}</pan></div>
            </div>
            
            <div cla="im-card" tyle="flex: 1; margin: 0; background: rgba(30,41,59,0.5);">
                <h4 tyle="margin: 0 0 12px 0; color: #ffffff;">Expected Dicipline Stat</h4>
                <div tyle="margin: 6px 0;"><trong>Expected Yellow Card:</trong> {t1} <pan tyle="color: #818cf8;">{pred.home_yellow_lambda:.2f}</pan> v {t2} <pan tyle="color: #f472b6;">{pred.away_yellow_lambda:.2f}</pan></div>
                <div tyle="margin: 6px 0;"><trong>Red Card Prob:</trong> {t1} <pan tyle="color: #818cf8;">{pred.home_red_prob:.1%}</pan> v {t2} <pan tyle="color: #f472b6;">{pred.away_red_prob:.1%}</pan></div>
                <div tyle="margin: 6px 0;"><trong>Calibrated Shootout win prob (if draw):</trong> {t1} <pan tyle="color: #818cf8;">{hootout_prob:.1%}</pan> v {t2} <pan tyle="color: #f472b6;">{1-hootout_prob:.1%}</pan></div>
            </div>
        </div>
    </div>
    """
    return html

# Sorted team lit for elector
all_team_orted = orted(lit(team_tat_cache.key()))

# ---------------------------------------------------------------------------
# Gradio Block Layout
# ---------------------------------------------------------------------------

with gr.Block(c=CSS_STYLES, title="FIFA World Cup 2026 Prediction Engine") a demo:
    # Banner Top Area
    banner_view = gr.HTML(value=generate_banner_html(GLOBAL_N_SIMS))
    
    with gr.Row():
        # Control Column
        with gr.Column(cale=1, min_width=280):
            gr.Markdown("### Simulation Control")
            n_im_lider = gr.Slider(minimum=50, maximum=2000, value=200, tep=50, label="Monte Carlo Iteration")
            run_btn = gr.Button("Run Monte Carlo", variant="primary")
            
            gr.Markdown("### Model Propertie")
            gr.Markdown("""
            - **Goal Model**: LightGBM Poion
            - **Dicipline**: LightGBM Poion
            - **Corner Model**: Ridge Regreor
            - **Red Card**: Logitic Claifier
            - **Penalty Shootout**: Elo-Calibrated Sigmoid
            """)
            
        # Main Tab Column
        with gr.Column(cale=4):
            with gr.Tab():
                with gr.Tab("Tournament Bracket"):
                    gr.Markdown("### Knockout Stage Bracket")
                    bracket_view = gr.HTML(value=generate_bracket_html(GLOBAL_MC_RESULTS["match_reult"], GLOBAL_MC_RESULTS["champion_prob"]))
                    
                with gr.Tab("Overall Statitic"):
                    gr.Markdown("### Prediction Statitic")
                    with gr.Row():
                        chart_champ = gr.Plot(value=generate_champ_fig(GLOBAL_MC_RESULTS["champion_prob"]))
                        chart_finalit = gr.Plot(value=generate_finalit_fig(GLOBAL_MC_RESULTS["finalit_prob"]))
                    
                    gr.Markdown("#### Detailed Prediction Leaderboard")
                    leaderboard_tbl = gr.Dataframe(value=generate_leaderboard_df(GLOBAL_MC_RESULTS["champion_prob"], GLOBAL_MC_RESULTS["finalit_prob"]), interactive=Fale)
                    
                with gr.Tab("Group Stage Standing"):
                    gr.Markdown("### Simulated Group Stage Standing")
                    group_view = gr.HTML(value=generate_all_group_html(GLOBAL_MC_RESULTS["match_reult"]))
                    
                with gr.Tab("Head-to-Head Simulator"):
                    gr.Markdown("### Live Match Simulator")
                    with gr.Row():
                        t1_dropdown = gr.Dropdown(choice=all_team_orted, value="Argentina", label="Home Team")
                        t2_dropdown = gr.Dropdown(choice=all_team_orted, value="France", label="Away Team")
                    
                    h2h_btn = gr.Button("Simulate Match (1,000 run)", variant="primary")
                    
                    # Side-by-ide predicted metric
                    with gr.Row():
                        t1_tat_box = gr.Markdown(value=generate_team_metric_md("Argentina", "France", i_home=True))
                        t2_tat_box = gr.Markdown(value=generate_team_metric_md("France", "Argentina", i_home=Fale))
                        
                    # Simulation output
                    h2h_output_view = gr.HTML(value="<div tyle='text-align: center; color: #94a3b8; padding: 20px;'>Click 'Simulate Match' to run live match imulation.</div>")

    # Wire event callback
    run_btn.click(
        fn=on_run_imulation,
        input=[n_im_lider],
        output=[bracket_view, chart_champ, chart_finalit, leaderboard_tbl, group_view, banner_view]
    )
    
    t1_dropdown.change(
        fn=update_h2h_tat, 
        input=[t1_dropdown, t2_dropdown], 
        output=[t1_tat_box, t2_tat_box]
    )
    
    t2_dropdown.change(
        fn=update_h2h_tat, 
        input=[t1_dropdown, t2_dropdown], 
        output=[t1_tat_box, t2_tat_box]
    )
    
    h2h_btn.click(
        fn=imulate_h2h_match, 
        input=[t1_dropdown, t2_dropdown], 
        output=[h2h_output_view]
    )

if __name__ == "__main__":
    # Launch local erver
    demo.launch(erver_name="127.0.0.1", erver_port=7860, hare=Fale)
