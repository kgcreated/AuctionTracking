import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime

st.title("📈 Real-Time Line Tracker")
st.write("Tracking Caesars, FanDuel, and DraftKings")

# This pulls the key you saved in Render Environment Variables
API_KEY = st.secrets["THE_ODDS_API_KEY"]

if st.button("Refresh Live Auction Lines"):
    url = f"https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds/?apiKey={API_KEY}&regions=us&markets=h2h"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        time_now = datetime.now().strftime("%H:%M:%S")
        
        # Track the first game available
        first_game = data[0]
        st.write(f"Tracking: **{first_game['away_team']} @ {first_game['home_team']}**")
        
        for book in first_game['bookmakers']:
            if book['key'] in ['draftkings', 'fanduel', 'caesars']:
                st.session_state.history.append({
                    'Time': time_now, 
                    'Bookmaker': book['title'], 
                    'Odds': book['markets'][0]['outcomes'][0]['price']
                })
        st.success("Lines Updated!")
    except Exception as e:
        st.error("Check your API key in Render Environment Variables.")

# Draw the Graph
if st.session_state.history:
    df = pd.DataFrame(st.session_state.history)
    fig = px.line(df, x='Time', y='Odds', color='Bookmaker', markers=True, 
                 title="Line Movement (Away Team)")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Click 'Refresh' to start the graph.")
