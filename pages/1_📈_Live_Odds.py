import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import os
import json
from datetime import datetime
import pytz # Handles the local clock

st.set_page_config(page_title="A's Over/Under Tracker", layout="wide")

# --- 1. LOCAL CLOCK SETUP ---
# Change 'US/Eastern' to his actual timezone (e.g., 'US/Central', 'US/Pacific')
local_tz = pytz.timezone('US/Eastern')

# --- 2. DATA SAVING LOGIC (The Vault) ---
VAULT_FILE = "betting_vault.json"

def save_to_vault(data):
    with open(VAULT_FILE, "w") as f:
        json.dump(data, f)

def load_vault():
    if os.path.exists(VAULT_FILE):
        with open(VAULT_FILE, "r") as f:
            return json.load(f)
    return {}

if "snapshot_vault" not in st.session_state:
    st.session_state.snapshot_vault = load_vault()

# --- 3. ODDS CONVERTER (Decimal to American) ---
def to_american(decimal_odds):
    if decimal_odds >= 2.0:
        return f"+{int((decimal_odds - 1) * 100)}"
    else:
        return f"-{int(100 / (decimal_odds - 1))}"

# --- 4. API SETUP ---
API_KEY = os.environ.get("THE_ODDS_API_KEY")
sport_choice = st.radio("Market:", ["NBA Basketball", "NFL Football"], horizontal=True)
sport_map = {"NBA Basketball": "basketball_nba", "NFL Football": "americanfootball_nfl"}

# We changed 'h2h' to 'totals' to get Over/Under
MARKET = "totals" 

st.title("🎯 Over/Under Auction Tracker")

# --- 5. THE SCAN ENGINE ---
def get_data():
    t_stamp = int(datetime.now().timestamp())
    # Notice 'totals' in the URL below
    url = f"https://api.the-odds-api.com/v4/sports/{sport_map[sport_choice]}/odds/?apiKey={API_KEY}&regions=us&markets={MARKET}&t={t_stamp}"
    try:
        return requests.get(url).json()
    except:
        return None

live_data = get_data()

if live_data:
    game_list = [f"{g['away_team']} @ {g['home_team']}" for g in live_data]
    selected_game = st.selectbox("Select Game:", game_list)
    g_data = next(x for x in live_data if f"{x['away_team']} @ {x['home_team']}" == selected_game)

    if st.button("🔥 Scan Live Totals", use_container_width=True):
        # Fix the time to Local Clock
        now_local = datetime.now(local_tz).strftime("%I:%M:%S %p")
        prices = []
        
        for book in g_data.get('bookmakers', []):
            if book['key'] in ['draftkings', 'fanduel', 'caesars', 'williamhill_us']:
                label = "Caesars" if "william" in book['key'] else book['title']
                
                # Totals data has 'Over' and 'Under' outcomes
                market = book['markets'][0]['outcomes']
                over = next(o for o in market if o['name'] == 'Over')
                under = next(o for o in market if o['name'] == 'Under')

                prices.append({
                    'Book': label,
                    'Line': over['point'], # The actual O/U number (e.g. 220.5)
                    'Over Odds': to_american(over['price']),
                    'Under Odds': to_american(under['price']),
                    'Clock': now_local
                })
        
        if prices:
            st.session_state.snapshot_vault[selected_game] = prices
            save_to_vault(st.session_state.snapshot_vault) # Save to file
            st.success(f"Snapshot Saved at {now_local}")

# --- 6. THE DISPLAY ---
st.divider()
if 'selected_game' in locals() and selected_game in st.session_state.snapshot_vault:
    st.write(f"### 📊 Over/Under Snapshot: {selected_game}")
    df = pd.DataFrame(st.session_state.snapshot_vault[selected_game])
    st.table(df)

    # Simple Analysis: Is there a discrepancy in the O/U line?
    lines = [p['Line'] for p in df]
    if len(set(lines)) > 1:
        st.warning(f"🚨 LINE DISCREPANCY: Books disagree on the total! Range: {min(lines)} - {max(lines)}")
import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import os
import json
from datetime import datetime
import pytz # Handles the local clock

st.set_page_config(page_title="A's Over/Under Tracker", layout="wide")

# --- 1. LOCAL CLOCK SETUP ---
# Change 'US/Eastern' to his actual timezone (e.g., 'US/Central', 'US/Pacific')
local_tz = pytz.timezone('US/Eastern')

# --- 2. DATA SAVING LOGIC (The Vault) ---
VAULT_FILE = "betting_vault.json"

def save_to_vault(data):
    with open(VAULT_FILE, "w") as f:
        json.dump(data, f)

def load_vault():
    if os.path.exists(VAULT_FILE):
        with open(VAULT_FILE, "r") as f:
            return json.load(f)
    return {}

if "snapshot_vault" not in st.session_state:
    st.session_state.snapshot_vault = load_vault()

# --- 3. ODDS CONVERTER (Decimal to American) ---
def to_american(decimal_odds):
    if decimal_odds >= 2.0:
        return f"+{int((decimal_odds - 1) * 100)}"
    else:
        return f"-{int(100 / (decimal_odds - 1))}"

# --- 4. API SETUP ---
API_KEY = os.environ.get("THE_ODDS_API_KEY")
sport_choice = st.radio("Market:", ["NBA Basketball", "NFL Football"], horizontal=True)
sport_map = {"NBA Basketball": "basketball_nba", "NFL Football": "americanfootball_nfl"}

# We changed 'h2h' to 'totals' to get Over/Under
MARKET = "totals" 

st.title("🎯 Over/Under Auction Tracker")

# --- 5. THE SCAN ENGINE ---
def get_data():
    t_stamp = int(datetime.now().timestamp())
    # Notice 'totals' in the URL below
    url = f"https://api.the-odds-api.com/v4/sports/{sport_map[sport_choice]}/odds/?apiKey={API_KEY}&regions=us&markets={MARKET}&t={t_stamp}"
    try:
        return requests.get(url).json()
    except:
        return None

live_data = get_data()

if live_data:
    game_list = [f"{g['away_team']} @ {g['home_team']}" for g in live_data]
    selected_game = st.selectbox("Select Game:", game_list)
    g_data = next(x for x in live_data if f"{x['away_team']} @ {x['home_team']}" == selected_game)

    if st.button("🔥 Scan Live Totals", use_container_width=True):
        # Fix the time to Local Clock
        now_local = datetime.now(local_tz).strftime("%I:%M:%S %p")
        prices = []
        
        for book in g_data.get('bookmakers', []):
            if book['key'] in ['draftkings', 'fanduel', 'caesars', 'williamhill_us']:
                label = "Caesars" if "william" in book['key'] else book['title']
                
                # Totals data has 'Over' and 'Under' outcomes
                market = book['markets'][0]['outcomes']
                over = next(o for o in market if o['name'] == 'Over')
                under = next(o for o in market if o['name'] == 'Under')

                prices.append({
                    'Book': label,
                    'Line': over['point'], # The actual O/U number (e.g. 220.5)
                    'Over Odds': to_american(over['price']),
                    'Under Odds': to_american(under['price']),
                    'Clock': now_local
                })
        
        if prices:
            st.session_state.snapshot_vault[selected_game] = prices
            save_to_vault(st.session_state.snapshot_vault) # Save to file
            st.success(f"Snapshot Saved at {now_local}")

# --- 6. THE DISPLAY ---
st.divider()
if 'selected_game' in locals() and selected_game in st.session_state.snapshot_vault:
    st.write(f"### 📊 Over/Under Snapshot: {selected_game}")
    df = pd.DataFrame(st.session_state.snapshot_vault[selected_game])
    st.table(df)

    # Simple Analysis: Is there a discrepancy in the O/U line?
    lines = [p['Line'] for p in df]
    if len(set(lines)) > 1:
        st.warning(f"🚨 LINE DISCREPANCY: Books disagree on the total! Range: {min(lines)} - {max(lines)}")

