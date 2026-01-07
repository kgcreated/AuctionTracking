import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import os
from datetime import datetime

st.set_page_config(page_title="A's Sulayve Stats", layout="wide")

# Initialize memory
if "history" not in st.session_state:
    st.session_state.history = []
if "snapshot_vault" not in st.session_state:
    st.session_state.snapshot_vault = {}

st.title("📊 Market Tracker: Live & Past")

sport_choice = st.radio("Market:", ["NBA Basketball", "NFL Football"], horizontal=True)
sport_map = {"NBA Basketball": "basketball_nba", "NFL Football": "americanfootball_nfl"}

API_KEY = os.environ.get("THE_ODDS_API_KEY") or st.secrets.get("THE_ODDS_API_KEY")

# --- DATA FETCHING ---
current_game_label = "None"
all_games = []

try:
    # Fetch both Live Odds and Past Scores
    odds_url = f"https://api.the-odds-api.com/v4/sports/{sport_map[sport_choice]}/odds/?apiKey={API_KEY}&regions=us&markets=h2h"
    scores_url = f"https://api.the-odds-api.com/v4/sports/{sport_map[sport_choice]}/scores/?apiKey={API_KEY}&daysFrom=3"
    
    live_res = requests.get(odds_url).json()
    past_res = requests.get(scores_url).json()

    # 1. Add Live Games to the list
    if isinstance(live_res, list):
        for g in live_res:
            all_games.append({
                "label": f"🟢 [LIVE] {g['away_team']} @ {g['home_team']}", 
                "data": g, 
                "is_completed": False
            })

    # 2. Add Completed Games to the list
    if isinstance(past_res, list):
        for g in past_res:
            if g.get('completed'):
                all_games.append({
                    "label": f"🏁 [FINAL] {g['away_team']} @ {g['home_team']}", 
                    "data": g, 
                    "is_completed": True
                })

    if all_games:
        current_game_label = st.selectbox("🎯 Target Game:", [g['label'] for g in all_games])
        selected_obj = next(item for item in all_games if item["label"] == current_game_label)
        selected_data = selected_obj["data"]

        # --- DISPLAY THE SCORE IF FINAL ---
        if selected_obj["is_completed"]:
            st.warning("This game is finished.")
            if "scores" in selected_data and selected_data["scores"]:
                s = selected_data["scores"]
                # This ensures the score is always visible at the top
                st.header(f"🏆 {s[0]['name']} {s[0]['score']} - {s[1]['name']} {s[1]['score']}")
            else:
                st.info("Score data is still processing for this game.")

        if st.button("Scan Market Data"):
            time_now = datetime.now().strftime("%H:%M:%S")
            current_prices = []
            
            # Look for bookmakers (may be empty for some final games)
            books = selected_data.get('bookmakers', [])
            for book in books:
                if book['key'] in ['draftkings', 'fanduel', 'caesars', 'williamhill_us']:
                    label = "Caesars" if "williamhill" in book['key'] else book['title']
                    odds = book['markets'][0]['outcomes'][0]['price']
                    team = book['markets'][0]['outcomes'][0]['name']
                    
                    price_entry = {'Bookmaker': label, 'Team': team, 'Odds': odds}
                    current_prices.append(price_entry)
                    st.session_state.history.append({
                        'Time': time_now, 'Game': current_game_label, 'Bookmaker': label, 'Odds': odds
                    })
            
            if current_prices:
                st.session_state.snapshot_vault[current_game_label] = current_prices
                st.success("Snapshot Locked!")
            elif selected_obj["is_completed"]:
                st.error("The API cleared the odds for this game, but the score is shown above.")

except Exception as e:
    st.error(f"Waiting for connection... {e}")

# --- DISPLAY SECTION ---
st.divider()

if current_game_label in st.session_state.snapshot_vault:
    st.write(f"### 💵 Verified Odds: {current_game_label}")
    st.table(pd.DataFrame(st.session_state.snapshot_vault[current_game_label]))

if st.session_state.history:
    df = pd.DataFrame(st.session_state.history)
    f_df = df[df['Game'] == current_game_label]
    if not f_df.empty:
        fig = px.line(f_df, x='Time', y='Odds', color='Bookmaker', markers=True, title="Market Movement")
        st.plotly_chart(fig, use_container_width=True)

