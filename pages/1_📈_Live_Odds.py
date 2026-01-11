import streamlit as st
import pandas as pd
import requests
import os
import json
from datetime import datetime
import pytz

st.set_page_config(page_title="A's Full Market Tracker", layout="wide")

# --- 1. INITIALIZE SESSION STATE ---
if "snapshot_vault" not in st.session_state:
    st.session_state.snapshot_vault = {}

# --- 2. SETTINGS & STORAGE ---
local_tz = pytz.timezone('US/Eastern')
VAULT_FILE = "betting_vault.json"

def save_to_vault(data):
    try:
        with open(VAULT_FILE, "w") as f:
            json.dump(data, f)
    except Exception:
        pass

def load_vault_into_session():
    if os.path.exists(VAULT_FILE):
        try:
            with open(VAULT_FILE, "r") as f:
                loaded_data = json.load(f)
                if loaded_data:
                    st.session_state.snapshot_vault.update(loaded_data)
        except Exception:
            pass

load_vault_into_session()

# --- 3. THE VEGAS-ACCURATE CONVERTER ---
# This fixes the "off by a hair" issue (e.g., -114 vs -115)
def to_american(decimal_odds):
    try:
        decimal_odds = float(decimal_odds)
        if decimal_odds >= 2.0:
            # Underdog (+) logic: round to nearest whole number
            return int(round((decimal_odds - 1) * 100))
        else:
            # Favorite (-) logic: round to nearest whole number
            return int(round(-100 / (decimal_odds - 1)))
    except:
        return 0

def format_odds(val):
    if val == 0: return "N/A"
    return f"+{val}" if val > 0 else str(val)

# --- 4. THE INTERFACE ---
st.title("🏆 Full Market Auction: ML & Totals")

API_KEY = os.environ.get("THE_ODDS_API_KEY")
sport_choice = st.radio("Market:", ["NBA Basketball", "NFL Football"], horizontal=True, key="live_market_radio")
sport_map = {"NBA Basketball": "basketball_nba", "NFL Football": "americanfootball_nfl"}

def get_data():
    if not API_KEY: return None
    # t_stamp ensures we bypass API provider cache for real-time accuracy
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

    if g_data and st.button("🔥 Scan Full Market", use_container_width=True):
        now_local = datetime.now(local_tz).strftime("%I:%M:%S %p")
        current_prices = []
        
        for book in g_data.get('bookmakers', []):
            if book['key'] in ['draftkings', 'fanduel', 'caesars', 'williamhill_us']:
                label = "Caesars" if "william" in book['key'] else book['title']
                entry = {'Book': label, 'Time': now_local}
                
                for market in book['markets']:
                    # Moneyline logic
                    if market['key'] == 'h2h':
                        entry['Away ML'] = to_american(market['outcomes'][0]['price'])
                        entry['Home ML'] = to_american(market['outcomes'][1]['price'])
                    
                    # Totals logic (Over/Under)
                    if market['key'] == 'totals':
                        over = next((o for o in market['outcomes'] if o['name'] == 'Over'), None)
                        if over:
                            entry['O/U Line'] = round(float(over['point']), 1)
                            entry['Over'] = to_american(over['price'])
                            under = next((o for o in market['outcomes'] if o['name'] == 'Under'), None)
                            if under:
                                entry['Under'] = to_american(under['price'])
                
                current_prices.append(entry)
        
        if current_prices:
            st.session_state.snapshot_vault[selected_game] = current_prices
            save_to_vault(st.session_state.snapshot_vault)
            st.success(f"Snapshot Saved & Rounded at {now_local}")

# --- 5. DISPLAY ---
st.divider()

if 'selected_game' in locals() and selected_game in st.session_state.snapshot_vault:
    st.write(f"### 📊 Full Market Snapshot: {selected_game}")
    df = pd.DataFrame(st.session_state.snapshot_vault[selected_game])
    
    cols_to_show = ['Book', 'Away ML', 'Home ML', 'O/U Line', 'Over', 'Under', 'Time']
    available_cols = [c for c in cols_to_show if c in df.columns]
    df = df[available_cols]

    # Display formatting for American Odds
    display_df = df.copy()
    for col in ['Away ML', 'Home ML', 'Over', 'Under']:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(format_odds)

    st.table(display_df)
else:
    st.info("Scan a game to view accurate Vegas-rounded odds.")
