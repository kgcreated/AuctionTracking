import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import os
import json
from datetime import datetime
import pytz

st.set_page_config(page_title="A's Over/Under Tracker", layout="wide")

# --- 1. LOCAL CLOCK SETUP ---
# Set this to your husband's timezone (e.g., 'US/Eastern', 'US/Central', 'US/Pacific')
local_tz = pytz.timezone('US/Eastern')

# --- 2. PERMANENT DATA STORAGE ---
VAULT_FILE = "betting_vault.json"

def save_to_vault(data):
    try:
        with open(VAULT_FILE, "w") as f:
            json.dump(data, f)
    except:
        pass

def load_vault():
    if os.path.exists(VAULT_FILE):
        try:
            with open(VAULT_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

if "snapshot_vault" not in st.session_state:
    st.session_state.snapshot_vault = load_vault()

# --- 3. ODDS CONVERTER (Decimal to American) ---
def to_american(decimal_odds):
    try:
        decimal_odds = float(decimal_odds)
        if decimal_odds >= 2.0:
            return f"+{int((decimal_odds - 1) * 100)}"
        else:
            return f"-{int(100 / (decimal_odds - 1))}"
    except:
        return "N/A"

# --- 4. NAVIGATION & API ---
st.title("🎯 Over/Under Auction Tracker")

API_KEY = os.environ.get("THE_ODDS_API_KEY")

# FIX: Added unique 'key' to prevent DuplicateElementId error
sport_choice = st.radio(
    "Market:", 
    ["NBA Basketball", "NFL Football"], 
    horizontal=True, 
    key="live_odds_sport_selector" 
)

sport_map = {"NBA Basketball": "basketball_nba", "NFL Football": "americanfootball_nfl"}

# --- 5. DATA FETCHING ---
def get_data():
    if not API_KEY: return None
    t_stamp = int(datetime.now().timestamp())
    # Markets set to 'totals' for Over/Under
    url = f"https://api.the-odds-api.com/v4/sports/{sport_map[sport_choice]}/odds/?apiKey={API_KEY}&regions=us&markets=totals&oddsFormat=decimal&t={t_stamp}"
    try:
        res = requests.get(url).json()
        return res if isinstance(res, list) else None
    except:
        return None

live_data = get_data()

if live_data:
    game_list = [f"{g['away_team']} @ {g['home_team']}" for g in live_data]
    selected_game = st.selectbox("Select Game:", game_list, key="game_select_box")
    g_data = next((x for x in live_data if f"{x['away_team']} @ {x['home_team']}" == selected_game), None)

    if g_data and st.button("🔥 Scan Live Totals", use_container_width=True):
        now_local = datetime.now(local_tz).strftime("%I:%M:%S %p")
        current_prices = []
        
        for book in g_data.get('bookmakers', []):
            if book['key'] in ['draftkings', 'fanduel', 'caesars', 'williamhill_us']:
                label = "Caesars" if "william" in book['key'] else book['title']
                
                # Extract Over/Under details
                try:
                    market = book['markets'][0]['outcomes']
                    over = next(o for o in market if o['name'] == 'Over')
                    under = next(o for o in market if o['name'] == 'Under')

                    current_prices.append({
                        'Book': label,
                        'Line': over['point'],
                        'Over': to_american(over['price']),
                        'Under': to_american(under['price']),
                        'Time Saved': now_local
                    })
                except:
                    continue
        
        if current_prices:
            st.session_state.snapshot_vault[selected_game] = current_prices
            save_to_vault(st.session_state.snapshot_vault)
            st.success(f"Snapshot Saved Successfully at {now_local}")

# --- 6. DISPLAY RESULTS ---
st.divider()

if 'selected_game' in locals() and selected_game in st.session_state.snapshot_vault:
    st.write(f"### 📊 Over/Under Snapshot: {selected_game}")
    saved_df = pd.DataFrame(st.session_state.snapshot_vault[selected_game])
    
    # Highlight lines that are different from the majority
    st.table(saved_df)
    
    # Calculate Line Discrepancies
    all_lines = saved_df['Line'].tolist()
    if len(set(all_lines)) > 1:
        st.warning(f"🚨 VALUE ALERT: Sportsbooks disagree on the Total! (Range: {min(all_lines)} to {max(all_lines)})")

else:
    st.info("Select a game and hit 'Scan' to see the current Over/Under auction.")

