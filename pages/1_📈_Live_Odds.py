import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import os
from datetime import datetime

# --- INITIALIZATION ---
if "history" not in st.session_state:
    st.session_state.history = []

st.title("📈 Live Auction Tracker")

# 1. SPORT SELECTOR
sport_choice = st.radio("Select Market:", ["NBA Basketball", "NFL Football"], horizontal=True)
sport_map = {"NBA Basketball": "basketball_nba", "NFL Football": "americanfootball_nfl"}

API_KEY = os.environ.get("THE_ODDS_API_KEY") or st.secrets.get("THE_ODDS_API_KEY")

if not API_KEY:
    st.error("⚠️ API Key missing from Render Environment Variables.")
    st.stop()

# 2. FETCH ALL GAMES FOR THE SELECTOR
url = f"https://api.the-odds-api.com/v4/sports/{sport_map[sport_choice]}/odds/?apiKey={API_KEY}&regions=us&markets=h2h"

try:
    response = requests.get(url)
    all_data = response.json()
    
    if not all_data:
        st.warning(f"No live {sport_choice} games found right now.")
    else:
        # Create a list of game titles for the dropdown
        game_titles = [f"{g['away_team']} @ {g['home_team']}" for g in all_data]
        selected_game_title = st.selectbox("🎯 Pick a Game to Track:", game_titles)
        
        # Find the data for the selected game
        selected_game_data = next(g for g in all_data if f"{g['away_team']} @ {g['home_team']}" == selected_game_title)

        if st.button("Refresh Selected Game"):
            time_now = datetime.now().strftime("%H:%M:%S")
            
            for book in selected_game_data['bookmakers']:
                # Ensure Caesars is included (check both key names)
                if book['key'] in ['draftkings', 'fanduel', 'caesars', 'williamhill_us']:
                    label = "Caesars" if "williamhill" in book['key'] else book['title']
                    
                    st.session_state.history.append({
                        'Time': time_now, 
                        'Game': selected_game_title,
                        'Bookmaker': label, 
                        'Odds': book['markets'][0]['outcomes'][0]['price']
                    })
            st.success(f"Updated {selected_game_title}!")

except Exception as e:
    st.error(f"Connection Error: {e}")

# --- DRAW THE GRAPH ---
if st.session_state.history:
    df = pd.DataFrame(st.session_state.history)
    
    # Only show data for the game currently selected in the dropdown
    # (This prevents lines from different games getting mixed on one graph)
    if 'selected_game_title' in locals():
        filtered_df = df[df['Game'] == selected_game_title]
        
        if not filtered_df.empty:
            fig = px.line(filtered_df, x='Time', y='Odds', color='Bookmaker', markers=True,
                         title=f"Line Movement: {selected_game_title}")
            st.plotly_chart(fig, use_container_width=True)
            
            # Show a small table of the latest prices
            st

