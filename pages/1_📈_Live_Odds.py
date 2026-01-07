import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import os
from datetime import datetime

st.set_page_config(page_title="A's Sulayve Stats", layout="wide")

if "history" not in st.session_state:
    st.session_state.history = []

st.title("📊 Market Tracker: Live & Past")

sport_choice = st.radio("Market:", ["NBA Basketball", "NFL Football"], horizontal=True)
sport_map = {"NBA Basketball": "basketball_nba", "NFL Football": "americanfootball_nfl"}

API_KEY = os.environ.get("THE_ODDS_API_KEY") or st.secrets.get("THE_ODDS_API_KEY")

# --- DATA FETCHING ---
try:
    # 1. Fetch Upcoming/Live Odds
    odds_url = f"https://api.the-odds-api.com/v4/sports/{sport_map[sport_choice]}/odds/?apiKey={API_KEY}&regions=us&markets=h2h"
    live_data = requests.get(odds_url).json()

    # 2. Fetch Recent Scores/Past Games (Last 3 days)
    scores_url = f"https://api.the-odds-api.com/v4/sports/{sport_map[sport_choice]}/scores/?apiKey={API_KEY}&daysFrom=3"
    past_data = requests.get(scores_url).json()

    # Combine them into one master list
    all_games = []
    
    # Add Live Games
    if isinstance(live_data, list):
        for g in live_data:
            all_games.append({"label": f"🟢 [LIVE] {g['away_team']} @ {g['home_team']}", "data": g, "type": "live"})
    
    # Add Past Games
    if isinstance(past_data, list):
        for g in past_data:
            if g.get('completed'):
                all_games.append({"label": f"🏁 [FINAL] {g['away_team']} @ {g['home_team']}", "data": g, "type": "past"})

    if all_games:
        # Create the dropdown with both types of games
        selected_label = st.selectbox("🎯 Select Matchup to View:", [g['label'] for g in all_games])
        selected_game = next(item for item in all_games if item["label"] == selected_label)
        g_data = selected_game["data"]

        # Display Info based on game type
        if selected_game["type"] == "past":
            st.warning("This game is finished. Showing closing lines and final score.")
            if g_data.get('scores'):
                s = g_data['scores']
                st.subheader(f"🏆 Final: {s[0]['name']} {s[0]['score']} - {s[1]['name']} {s[1]['score']}")
        
        if st.button("Analyze Odds"):
            time_now = datetime.now().strftime("%H:%M:%S")
            # Pull bookmaker data (Common to both endpoints)
            for book in g_data.get('bookmakers', []):
                if book['key'] in ['draftkings', 'fanduel', 'caesars', 'williamhill_us']:
                    label = "Caesars" if "williamhill" in book['key'] else book['title']
                    odds = book['markets'][0]['outcomes'][0]['price']
                    st.session_state.history.append({
                        'Time': time_now, 
                        'Game': selected_label, 
                        'Bookmaker': label, 
                        'Odds': odds
                    })
            st.success("Lines Loaded!")

except Exception as e:
    st.error(f"API Error: {e}")

# --- GRAPHING ---
if st.session_state.history:
    df = pd.DataFrame(st.session_state.history)
    if 'selected_label' in locals():
        f_df = df[df['Game'] == selected_label]
        if not f_df.empty:
            fig = px.line(f_df, x='Time', y='Odds', color='Bookmaker', markers=True, title=f"Price History: {selected_label}")
            st.plotly_chart(fig, use_container_width=True)
            
            # Clear button
            if st.button("Clear Graph"):
                st.session_state.history = []
                st.rerun()

