import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import os
from datetime import datetime

st.set_page_config(page_title="A's Sulayve Stats", layout="wide")

# --- INITIALIZE MEMORY ---
if "history" not in st.session_state:
    st.session_state.history = []
if "snapshot_vault" not in st.session_state:
    st.session_state.snapshot_vault = {}

st.title("📊 Live Odds & Snapshot Vault")

sport_choice = st.radio("Market:", ["NBA Basketball", "NFL Football"], horizontal=True)
sport_map = {"NBA Basketball": "basketball_nba", "NFL Football": "americanfootball_nfl"}

API_KEY = os.environ.get("THE_ODDS_API_KEY") or st.secrets.get("THE_ODDS_API_KEY")

# --- DATA FETCHING ---
# We initialize this as None so we don't get a 'NameError' later
current_game_label = "None" 

try:
    odds_url = f"https://api.the-odds-api.com/v4/sports/{sport_map[sport_choice]}/odds/?apiKey={API_KEY}&regions=us&markets=h2h"
    scores_url = f"https://api.the-odds-api.com/v4/sports/{sport_map[sport_choice]}/scores/?apiKey={API_KEY}&daysFrom=3"
    
    live_res = requests.get(odds_url).json()
    past_res = requests.get(scores_url).json()

    all_games = []
    if isinstance(live_res, list):
        for g in live_res:
            all_games.append({"label": f"🟢 [LIVE] {g['away_team']} @ {g['home_team']}", "data": g})
    if isinstance(past_res, list):
        for g in past_res:
            if g.get('completed'):
                all_games.append({"label": f"🏁 [FINAL] {g['away_team']} @ {g['home_team']}", "data": g})

    if all_games:
        current_game_label = st.selectbox("🎯 Target Game:", [g['label'] for g in all_games])
        selected_data = next(item for item in all_games if item["label"] == current_game_label)["data"]

        if st.button("Scan Market"):
            time_now = datetime.now().strftime("%H:%M:%S")
            current_prices = []
            
            # Extract bookmaker data safely
            books = selected_data.get('bookmakers', [])
            for book in books:
                if book['key'] in ['draftkings', 'fanduel', 'caesars', 'williamhill_us']:
                    label = "Caesars" if "williamhill" in book['key'] else book['title']
                    odds = book['markets'][0]['outcomes'][0]['price']
                    team = book['markets'][0]['outcomes'][0]['name']
                    
                    price_entry = {'Bookmaker': label, 'Team': team, 'Odds': odds}
                    current_prices.append(price_entry)
                    
                    # Log to graph history
                    st.session_state.history.append({
                        'Time': time_now, 'Game': current_game_label, 'Bookmaker': label, 'Odds': odds
                    })
            
            # SAVE SNAPSHOT: This prevents the 'inaccurate future' data issue
            if current_prices:
                st.session_state.snapshot_vault[current_game_label] = current_prices
                st.success(f"Snapshot Saved for {current_game_label}")

except Exception as e:
    st.error(f"Waiting for valid API data... ({e})")

# --- DISPLAY SECTION ---
st.divider()

# 1. Show the "Last Seen" Snapshot (The Inaccuracy Fix)
if current_game_label in st.session_state.snapshot_vault:
    st.write(f"### 💵 Latest Verified Odds: {current_game_label}")
    st.table(pd.DataFrame(st.session_state.snapshot_vault[current_game_label]))
else:
    st.info("No verified snapshot yet. Hit 'Scan Market' to lock in the prices.")

# 2. Show the Movement Graph
if st.session_state.history:
    df = pd.DataFrame(st.session_state.history)
    f_df = df[df['Game'] == current_game_label]
    if not f_df.empty:
        fig = px.line(f_df, x='Time', y='Odds', color='Bookmaker', markers=True, title="Auction Movement")
        st.plotly_chart(fig, use_container_width=True)

if st.button("Clear All App Data"):
    st.session_state.history = []
    st.session_state.snapshot_vault = {}
    st.rerun()
