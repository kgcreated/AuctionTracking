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
    odds_url = f"https://api.the-odds-api.com/v4/sports/{sport_map[sport_choice]}/odds/?apiKey={API_KEY}&regions=us&markets=h2h"
    scores_url = f"https://api.the-odds-api.com/v4/sports/{sport_map[sport_choice]}/scores/?apiKey={API_KEY}&daysFrom=3"
    
    live_res = requests.get(odds_url).json()
    past_res = requests.get(scores_url).json()

    if isinstance(live_res, list):
        for g in live_res:
            all_games.append({"label": f"🟢 [LIVE] {g['away_team']} @ {g['home_team']}", "data": g, "is_completed": False})
    if isinstance(past_res, list):
        for g in past_res:
            if g.get('completed'):
                all_games.append({"label": f"🏁 [FINAL] {g['away_team']} @ {g['home_team']}", "data": g, "is_completed": True})

    if all_games:
        current_game_label = st.selectbox("🎯 Target Game:", [g['label'] for g in all_games])
        selected_obj = next(item for item in all_games if item["label"] == current_game_label)
        selected_data = selected_obj["data"]

        if selected_obj["is_completed"] and "scores" in selected_data:
            s = selected_data["scores"]
            st.header(f"🏆 Final: {s[0]['name']} {s[0]['score']} - {s[1]['name']} {s[1]['score']}")

        if st.button("Scan Market Data"):
            time_now = datetime.now().strftime("%H:%M:%S")
            prices = []
            
            books = selected_data.get('bookmakers', [])
            for book in books:
                if book['key'] in ['draftkings', 'fanduel', 'caesars', 'williamhill_us']:
                    label = "Caesars" if "williamhill" in book['key'] else book['title']
                    odds = book['markets'][0]['outcomes'][0]['price']
                    team = book['markets'][0]['outcomes'][0]['name']
                    
                    prices.append({'Book': label, 'Team': team, 'Odds': odds})
                    st.session_state.history.append({'Time': time_now, 'Game': current_game_label, 'Bookmaker': label, 'Odds': odds})
            
            if prices:
                st.session_state.snapshot_vault[current_game_label] = prices
                
                # --- NEW: STALE LINE DETECTION ---
                # 1. Get Consensus (DraftKings & FanDuel average)
                sharp_odds = [p['Odds'] for p in prices if p['Book'] in ['DraftKings', 'FanDuel']]
                if len(sharp_odds) >= 2:
                    consensus = sum(sharp_odds) / len(sharp_odds)
                    
                    # 2. Compare every book to that Consensus
                    for p in prices:
                        # Deviation logic: if a book is at least 7 points better than consensus
                        # (e.g. Consensus is -120, but Caesars is -110)
                        if p['Odds'] >= (consensus + 7):
                            st.warning(f"🚨 **STALE LINE ALERT:** {p['Book']} is lagging the market!")
                            st.write(f"The Sharp Consensus is **{consensus:.0f}**, but {p['Book']} is still at **{p['Odds']}**.")
                            st.info("💡 This is a 'Market Deviation'. Bet this before they catch up!")
                
                st.success("Snapshot Locked!")

except Exception as e:
    st.error(f"Waiting for connection... {e}")

# --- DISPLAY ---
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

