import streamlit as st
import pandas as pd
import requests
import os
import json
from datetime import datetime
import pytz

st.set_page_config(page_title="A's Full Market Tracker", layout="wide")

# --- 1. SETTINGS ---
local_tz = pytz.timezone('US/Eastern')
VAULT_FILE = "betting_vault.json"

def save_to_vault(data):
    try:
        with open(VAULT_FILE, "w") as f:
            json.dump(data, f)
    except:
        pass

# --- 2. ODDS CONVERTER ---
def to_american(decimal_odds):
    try:
        decimal_odds = float(decimal_odds)
        if decimal_odds >= 2.0:
            return int((decimal_odds - 1) * 100)
        else:
            return int(-100 / (decimal_odds - 1))
    except:
        return 0

def format_odds(val):
    return f"+{val}" if val > 0 else str(val)

# --- 3. THE APP ---
st.title("🏆 Full Market Auction: Moneyline & Totals")

API_KEY = os.environ.get("THE_ODDS_API_KEY")
sport_choice = st.radio("Market:", ["NBA Basketball", "NFL Football"], horizontal=True, key="live_market_radio")
sport_map = {"NBA Basketball": "basketball_nba", "NFL Football": "americanfootball_nfl"}

# FETCH DATA (Now asking for BOTH h2h and totals)
def get_data():
    if not API_KEY: return None
    t_stamp = int(datetime.now().timestamp())
    # Markets set to 'h2h,totals'
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

    if g_data and st.button("🔥 Scan Full Market", use_container_width=True):
        now_local = datetime.now(local_tz).strftime("%I:%M:%S %p")
        current_prices = []
        
        for book in g_data.get('bookmakers', []):
            if book['key'] in ['draftkings', 'fanduel', 'caesars', 'williamhill_us']:
                label = "Caesars" if "william" in book['key'] else book['title']
                
                entry = {'Book': label, 'Time': now_local}
                
                # Extract Markets
                for market in book['markets']:
                    # Moneyline (h2h)
                    if market['key'] == 'h2h':
                        # Away Team is usually index 0, Home is index 1
                        entry['Away ML'] = to_american(market['outcomes'][0]['price'])
                        entry['Home ML'] = to_american(market['outcomes'][1]['price'])
                    
                    # Over/Under (totals)
                    if market['key'] == 'totals':
                        over = next(o for o in market['outcomes'] if o['name'] == 'Over')
                        under = next(o for o in market['outcomes'] if o['name'] == 'Under')
                        entry['O/U Line'] = round(float(over['point']), 1)
                        entry['Over'] = to_american(over['price'])
                        entry['Under'] = to_american(under['price'])
                
                current_prices.append(entry)
        
        if current_prices:
            st.session_state.snapshot_vault[selected_game] = current_prices
            save_to_vault(st.session_state.snapshot_vault)

# --- 4. DISPLAY ---
st.divider()

if 'selected_game' in locals() and selected_game in st.session_state.snapshot_vault:
    st.write(f"### 📊 Full Market Snapshot: {selected_game}")
    df = pd.DataFrame(st.session_state.snapshot_vault[selected_game])
    
    # Sort columns for a cleaner look
    cols = ['Book', 'Away ML', 'Home ML', 'O/U Line', 'Over', 'Under', 'Time']
    df = df[cols]

    # Format for display (+100/-110)
    display_df = df.copy()
    for col in ['Away ML', 'Home ML', 'Over', 'Under']:
        display_df[col] = display_df[col].apply(format_odds)

    st.table(display_df)

    # VALUE ALERT
    best_away = df.loc[df['Away ML'].idxmax()]
    st.success(f"✅ **VALUE ALERT:** Best Moneyline for **{selected_game.split(' @ ')[0]}** is **{format_odds(best_away['Away ML'])}** at **{best_away['Book']}**")
