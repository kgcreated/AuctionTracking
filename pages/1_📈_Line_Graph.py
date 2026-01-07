import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import os  # <--- This is the new part we need
from datetime import datetime

st.title("📈 Real-Time Line Tracker")

# This new way checks BOTH Render's settings AND the secrets file
API_KEY = os.environ.get("THE_ODDS_API_KEY") or st.secrets.get("THE_ODDS_API_KEY")

if not API_KEY:
    st.error("⚠️ API Key not found! Please make sure 'THE_ODDS_API_KEY' is added to Render's Environment Variables.")
    st.stop()

if st.button("Refresh Auction Lines"):
    # Using NBA as a test because there are games every night
    url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/odds/?apiKey={API_KEY}&regions=us&markets=h2h"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if not data:
            st.warning("No live games found at this moment.")
        else:
            time_now = datetime.now().strftime("%H:%M:%S")
            game = data[0]
            st.write(f"Tracking: **{game['away_team']} @ {game['home_team']}**")
            
            for book in game['bookmakers']:
                if book['key'] in ['draftkings', 'fanduel', 'caesars']:
                    st.session_state.history.append({
                        'Time': time_now, 
                        'Bookmaker': book['title'], 
                        'Odds': book['markets'][0]['outcomes'][0]['price']
                    })
            st.success("Updated!")
    except Exception as e:
        st.error(f"Error: {e}")

if st.session_state.history:
    df = pd.DataFrame(st.session_state.history)
    fig = px.line(df, x='Time', y='Odds', color='Bookmaker', markers=True)
    st.plotly_chart(fig, use_container_width=True)
