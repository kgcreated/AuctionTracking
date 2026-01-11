import streamlit as st
import pandas as pd
import requests
import os
import json
import math # Added for precise rounding
from datetime import datetime
import pytz

st.set_page_config(page_title="A's Precise Tracker", layout="wide")

# --- 1. INITIALIZE ---
if "snapshot_vault" not in st.session_state:
    st.session_state.snapshot_vault = {}

local_tz = pytz.timezone('US/Eastern')
VAULT_FILE = "betting_vault.json"

# --- 2. THE PRECISION CONVERTER ---
# This version eliminates the "Rounding Too High" error
def to_american_precise(decimal_odds):
    try:
        decimal_odds = float(decimal_odds)
        if decimal_odds >= 2.0:
            # Underdog (+): Standard calculation
            # Use math.floor to keep it from rounding up prematurely
            return int(math.floor((decimal_odds - 1) * 100))
        else:
            # Favorite (-): Vegas apps usually 'floor' the negative 
            # to ensure the most accurate representation of the price
            return int(math.ceil(-100 / (decimal_odds - 1)))
    except:
        return 0

def format_odds(val):
    if val == 0: return "N/A"
    return f"+{val}" if val > 0 else str(val)

# --- 3. THE INTERFACE ---
st.title("🏆 Precise Market Auction: ML & Totals")

API_KEY = os.environ.get("THE_ODDS_API_KEY")
sport_choice = st.radio("Market:", ["NBA Basketball", "NFL Football"], horizontal=True, key="live_market_radio")
sport_map = {"NBA Basketball": "basketball_nba", "NFL Football": "americanfootball_nfl"}

def get_data():
    if not API_KEY: return None
    t_stamp = int(datetime.now().timestamp())
    url = f"https://api.the-odds-api.com/v4/sports/{sport_map[sport_choice]}/odds/?apiKey={API_KEY}&regions=us&markets=h2h,totals&oddsFormat=decimal&t={t_stamp}"
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

    if g_data and st.button("🔥 Scan Market Precision", use_container_width=True):
        now_local = datetime.now(local_tz).strftime("%I:%M:%S %p")
        current_prices = []
        
        for book in g_data.get('bookmakers', []):
            if book['key'] in ['draftkings', 'fanduel', 'caesars', 'williamhill_us']:
                label = "Caesars" if "william" in book['key'] else book['title']
                entry = {'Book': label, 'Time': now_local}
                
                for market in book['markets']:
                    if market['key'] == 'h2h':
                        entry['Away ML'] = to_american_precise(market['outcomes'][0]['price'])
                        entry['Home ML'] = to_american_precise(market['outcomes'][1]['price'])
                    
                    if market['key'] == 'totals':
                        over = next((o for o in market['outcomes'] if o['name'] == 'Over'), None)
                        if over:
                            entry['O/U Line'] = round(float(over['point']), 1)
                            entry['Over'] = to_american_precise(over['price'])
                            under = next((o for o in market['outcomes'] if o['name'] == 'Under'), None)
                            if under:
                                entry['Under'] = to_american_precise(under['price'])
                
                current_prices.append(entry)
        
        if current_prices:
            st.session_state.snapshot_vault[selected_game] = current_prices
            with open(VAULT_FILE, "w") as f:
                json.dump(st.session_state.snapshot_vault, f)
            st.success(f"Precision Snapshot Saved at {now_local}")

# --- 4. DISPLAY ---
st.divider()

if 'selected_game' in locals() and selected_game in st.session_state.snapshot_vault:
    st.write(f"### 📊 Precise Market Snapshot: {selected_game}")
    df = pd.DataFrame(st.session_state.snapshot_vault[selected_game])
    
    cols_to_show = ['Book', 'Away ML', 'Home ML', 'O/U Line', 'Over', 'Under', 'Time']
    available_cols = [c for c in cols_to_show if c in df.columns]
    df = df[available_cols]

    display_df = df.copy()
    for col in ['Away ML', 'Home ML', 'Over', 'Under']:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(format_odds)

    st.table(display_df)
