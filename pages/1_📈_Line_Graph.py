import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import os
from datetime import datetime

# --- INITIALIZATION ---
if "history" not in st.session_state:
    st.session_state.history = []

st.title("📈 Real-Time Line Tracker")

# 1. SPORT SELECTOR TOGGLE
sport_choice = st.radio("Select Market to Track:", ["NBA Basketball", "NFL Football"], horizontal=True)

# Map the choice to the API names
sport_map = {
    "NBA Basketball": "basketball_nba",
    "NFL Football": "americanfootball_nfl"
}

API_KEY = os.environ.get("THE_ODDS_API_KEY") or st.secrets.get("THE_ODDS_API_KEY")

if st.button(f"Refresh {sport_choice} Lines"):
    url = f"https://api.the-odds-api.com/v4/sports/{sport_map[sport_choice]}/odds/?apiKey={API_KEY}&regions=us&markets=h2h"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if not data:
            st.warning(f"No live {sport_choice} games found. The season might be in a break or games haven't posted yet.")
        else:
            time_now = datetime.now().strftime("%H:%M:%S")
            game = data[0] # Tracks the most imminent game
            
            st.info(f"Tracking: **{game['away_team']} @ {game['home_team']}**")
            
            for book in game['bookmakers']:
                if book['key'] in ['draftkings', 'fanduel', 'caesars']:
                    st.session_state.history.append({
                        'Time': time_now, 
                        'Sport': sport_choice,
                        'Bookmaker': book['title'], 
                        'Odds': book['markets'][0]['outcomes'][0]['price']
                    })
            st.success("Lines Updated!")
    except Exception as e:
        st.error(f"Error fetching data: {e}")

# --- DRAW THE GRAPH ---
if st.session_state.history:
    df = pd.DataFrame(st.session_state.history)
    
    # Filter graph to only show the currently selected sport
    filtered_df = df[df['Sport'] == sport_choice]
    
    if not filtered_df.empty:
        fig = px.line(filtered_df, x='Time', y='Odds', color='Bookmaker', markers=True,
                     title=f"Movement for {sport_choice}")
        st.plotly_chart(fig, use_container_width=True)
        
        # CLEAR BUTTON
        if st.button("Clear Graph History"):
            st.session_state.history = []
            st.rerun()
    else:
        st.info(f"No history recorded for {sport_choice} yet. Tap Refresh!")
else:
    st.info("Tap 'Refresh' to start the broadcast.")

