import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import os
from datetime import datetime

# Initialize memory in case they skip home
if "history" not in st.session_state:
    st.session_state.history = []

st.title("📈 Real-Time Line Tracker")

# Sport Selector
sport_choice = st.radio("Select Market:", ["NBA Basketball", "NFL Football"], horizontal=True)
sport_map = {"NBA Basketball": "basketball_nba", "NFL Football": "americanfootball_nfl"}

API_KEY = os.environ.get("THE_ODDS_API_KEY") or st.secrets.get("THE_ODDS_API_KEY")

if not API_KEY:
    st.error("⚠️ API Key missing from Render Environment Variables.")
    st.stop()

if st.button(f"Refresh {sport_choice} Odds"):
    url = f"https://api.the-odds-api.com/v4/sports/{sport_map[sport_choice]}/odds/?apiKey={API_KEY}&regions=us&markets=h2h"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if not data:
            st.warning(f"No live {sport_choice} lines found right now.")
        else:
            time_now = datetime.now().strftime("%H:%M:%S")
            game = data[0] # Focuses on the most imminent game
            st.info(f"Tracking: **{game['away_team']} @ {game['home_team']}**")
            
            for book in game['bookmakers']:
                # 'williamhill_us' is the API name for Caesars in many US states
                if book['key'] in ['draftkings', 'fanduel', 'caesars', 'williamhill_us']:
                    label = "Caesars" if "williamhill" in book['key'] else book['title']
                    st.session_state.history.append({
                        'Time': time_now, 
                        'Sport': sport_choice,
                        'Bookmaker': label, 
                        'Odds': book['markets'][0]['outcomes'][0]['price']
                    })
            st.success("Market Data Updated!")
    except Exception as e:
        st.error(f"Connection Error: {e}")

# Graph Logic
if st.session_state.history:
    df = pd.DataFrame(st.session_state.history)
    filtered_df = df[df['Sport'] == sport_choice]
    
    if not filtered_df.empty:
        fig = px.line(filtered_df, x='Time', y='Odds', color='Bookmaker', markers=True,
                     title=f"Live {sport_choice} Auction Movement")
        st.plotly_chart(fig, use_container_width=True)
        
        if st.button("Clear History"):
            st.session_state.history = []
            st.rerun()
    else:
        st.info(f"No data for {sport_choice} yet. Hit Refresh!")
