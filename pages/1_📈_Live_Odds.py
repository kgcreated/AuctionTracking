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

try:
    # 1. Fetch Data
    odds_url = f"https://api.the-odds-api.com/v4/sports/{sport_map[sport_choice]}/odds/?apiKey={API_KEY}&regions=us&markets=h2h"
    scores_url = f"https://api.the-odds-api.com/v4/sports/{sport_map[sport_choice]}/scores/?apiKey={API_KEY}&daysFrom=3"
    
    live_data = requests.get(odds_url).json()
    past_data = requests.get(scores_url).json()

    all_games = []
    if isinstance(live_data, list):
        for g in live_data:
            all_games.append({"label": f"🟢 [LIVE] {g['away_team']} @ {g['home_team']}", "data": g, "type": "live"})
    if isinstance(past_data, list):
        for g in past_data:
            if g.get('completed'):
                all_games.append({"label": f"🏁 [FINAL] {g['away_team']} @ {g['home_team']}", "data": g, "type": "past"})

    if all_games:
        selected_label = st.selectbox("🎯 Select Matchup:", [g['label'] for g in all_games])
        selected_game = next(item for item in all_games if item["label"] == selected_label)
        g_data = selected_game["data"]

        if selected_game["type"] == "past":
            if g_data.get('scores'):
                s = g_data['scores']
                st.subheader(f"🏆 Final: {s[0]['name']} {s[0]['score']} - {s[1]['name']} {s[1]['score']}")
        
        if st.button("Analyze Odds"):
            time_now = datetime.now().strftime("%H:%M:%S")
            found_any_odds = False
            
            # Search for bookmakers in the data structure
            books = g_data.get('bookmakers', [])
            
            if not books:
                st.warning("No closing odds found in the score record. Trying to re-sync...")
            
            for book in books:
                if book['key'] in ['draftkings', 'fanduel', 'caesars', 'williamhill_us']:
                    label = "Caesars" if "williamhill" in book['key'] else book['title']
                    # Get the odds for the first outcome (Away Team)
                    odds = book['markets'][0]['outcomes'][0]['price']
                    team_name = book['markets'][0]['outcomes'][0]['name']
                    
                    st.session_state.history.append({
                        'Time': time_now, 
                        'Game': selected_label, 
                        'Bookmaker': label, 
                        'Team': team_name,
                        'Odds': odds
                    })
                    found_any_odds = True
            
            if found_any_odds:
                st.success("Closing Lines Loaded!")
            else:
                st.error("The API provided the score but did not include the bookmaker lines for this finished game.")

except Exception as e:
    st.error(f"API Error: {e}")

# --- DISPLAY DATA ---
if st.session_state.history:
    df = pd.DataFrame(st.session_state.history)
    f_df = df[df['Game'] == selected_label]
    
    if not f_df.empty:
        # Show a Table first so he sees the numbers immediately
        st.write("### 💵 Closing Odds Table")
        latest_table = f_df.groupby('Bookmaker').last().reset_index()
        st.table(latest_table[['Bookmaker', 'Team', 'Odds']])

        # Show the Graph
        fig = px.line(f_df, x='Time', y='Odds', color='Bookmaker', markers=True, 
                     title=f"Odds Movement for {selected_label}")
        st.plotly_chart(fig, use_container_width=True)
        
        if st.button("Clear Cache"):
            st.session_state.history = []
            st.rerun()

