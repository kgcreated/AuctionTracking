import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime

st.title("📈 Real-Time Line Tracker")

# Pulls the key from Render Environment Variables
API_KEY = st.secrets["THE_ODDS_API_KEY"]

if st.button("Refresh Auction Lines"):
    # Tracking NFL Lines
    url = f"https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds/?apiKey={API_KEY}&regions=us&markets=h2h"
    
    try:
        response = requests.get(url)
        data = response.json()
        time_now = datetime.now().strftime("%H:%M:%S")
        
        # Pull data from DraftKings, FanDuel, and Caesars
        game = data[0]
        st.write(f"Tracking: **{game['away_team']} @ {game['home_team']}**")
        
        for book in game['bookmakers']:
            if book['key'] in ['draftkings', 'fanduel', 'caesars']:
                st.session_state.history.append({
                    'Time': time_now, 
                    'Bookmaker': book['title'], 
                    'Odds': book['markets'][0]['outcomes'][0]['price']
                })
        st.success("Lines Updated!")
    except:
        st.error("Error fetching data. Ensure the API key is set in Render.")

if st.session_state.history:
    df = pd.DataFrame(st.session_state.history)
    fig = px.line(df, x='Time', y='Odds', color='Bookmaker', markers=True)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No data yet. Tap 'Refresh' to start the broadcast.")
