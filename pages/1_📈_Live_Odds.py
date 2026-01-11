import streamlit as st
import pandas as pd
import requests
import os
import json
from datetime import datetime
import pytz

st.set_page_config(page_title="A's Precise Mirror", layout="wide")

# --- 1. INITIALIZE ---
if "snapshot_vault" not in st.session_state:
    st.session_state.snapshot_vault = {}

local_tz = pytz.timezone('US/Eastern')
VAULT_FILE = "betting_vault.json"

# --- 2. FORMATTING HELPERS ---
def format_odds(val):
    if pd.isna(val) or val == 0 or val is None: return "-"
    try:
        num = int(float(val))
        return f"+{num}" if num > 0 else str(num)
    except:
        return "-"

def format_line(val):
    if pd.isna(val) or val is None: return "-"
    return f"{float(val):.1f}"

# --- 3. THE INTERFACE ---
st.title("Live ODDS & Lines")
st.info("")

API_KEY = os.environ.get("THE_ODDS_API_KEY")
sport_choice = st.radio("Market:", ["NBA Basketball", "NFL Football"], horizontal=True, key="live_market_radio")
sport_map = {"NBA Basketball": "basketball_nba", "NFL Football": "americanfootball_nfl"}

def get_data():
    if not API_KEY: return None
    t_stamp = int(datetime.now().timestamp())
    url = f"https://api.the-odds-api.com/v4/sports/{sport_map[sport_choice]}/odds/?apiKey={API_KEY}&regions=us&markets=h2h,totals&oddsFormat=american&t={t_stamp}"
    try:
        res = requests.get(url).json()
        return res if isinstance(res, list) else None
    except:
        return None

live_data = get_data()

if live_data:
    game_list = [f"{g['away_team']} @ {g['home_team']}" for g in live_data]
    selected_game = st.selectbox("Select Game:", game_list)
    g_data = next((x for x in live_data if f"{x['away_team']} @ {x['home_team']}" == selected_game), None)

    if g_data and st.button("🔥 Sync & Align Odds", use_container_width=True):
        now_local = datetime.now(local_tz).strftime("%I:%M:%S %p")
        current_prices = []
        
        # DEFINE THE ANCHORS
        OFFICIAL_AWAY = g_data['away_team']
        OFFICIAL_HOME = g_data['home_team']
        
        for book in g_data.get('bookmakers', []):
            if book['key'] in ['draftkings', 'fanduel', 'caesars', 'williamhill_us']:
                label = "Caesars" if "william" in book['key'] else book['title']
                entry = {
                    'Book': label, 
                    'Away ML': None, 'Home ML': None, 
                    'O/U Line': None, 'Over': None, 'Under': None,
                    'Time': now_local
                }
                
                for market in book['markets']:
                    # THE ML FIX: Explicitly match name to price
                    if market['key'] == 'h2h':
                        for outcome in market['outcomes']:
                            if outcome['name'] == OFFICIAL_AWAY:
                                entry['Away ML'] = outcome['price']
                            elif outcome['name'] == OFFICIAL_HOME:
                                entry['Home ML'] = outcome['price']
                    
                    # THE TOTALS FIX
                    if market['key'] == 'totals':
                        over = next((o for o in market['outcomes'] if o['name'] == 'Over'), None)
                        under = next((o for o in market['outcomes'] if o['name'] == 'Under'), None)
                        if over:
                            entry['O/U Line'] = over['point']
                            entry['Over'] = over['price']
                        if under:
                            entry['Under'] = under['price']
                
                current_prices.append(entry)
        
        if current_prices:
            st.session_state.snapshot_vault[selected_game] = current_prices
            with open(VAULT_FILE, "w") as f:
                json.dump(st.session_state.snapshot_vault, f)
            st.success(f"Aligned successfully for {selected_game}")

# --- 4. DISPLAY ---
st.divider()

if 'selected_game' in locals() and selected_game in st.session_state.snapshot_vault:
    st.write(f"### 📊 Final Aligned Snapshot: {selected_game}")
    df = pd.DataFrame(st.session_state.snapshot_vault[selected_game])
    
    display_df = df.copy()
    
    # Format columns for a clean look
    if 'O/U Line' in display_df.columns:
        display_df['O/U Line'] = display_df['O/U Line'].apply(format_line)
    
    for col in ['Away ML', 'Home ML', 'Over', 'Under']:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(format_odds)

    # Final column order
    cols_order = ['Book', 'Away ML', 'Home ML', 'O/U Line', 'Over', 'Under', 'Time']
    display_df = display_df[[c for c in cols_order if c in display_df.columns]]

    st.table(display_df)
