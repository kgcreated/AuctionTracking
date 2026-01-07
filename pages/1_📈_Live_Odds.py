import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import os
from datetime import datetime

st.set_page_config(page_title="A's Sulayve Stats", layout="wide")

if "history" not in st.session_state:
    st.session_state.history = []

st.title("📊 Live Odds")

sport_choice = st.radio("Market:", ["NBA Basketball", "NFL Football"], horizontal=True)
sport_map = {"NBA Basketball": "basketball_nba", "NFL Football": "americanfootball_nfl"}

API_KEY = os.environ.get("THE_ODDS_API_KEY") or st.secrets.get("THE_ODDS_API_KEY")

try:
    url = f"https://api.the-odds-api.com/v4/sports/{sport_map[sport_choice]}/odds/?apiKey={API_KEY}&regions=us&markets=h2h"
    res = requests.get(url).json()
    
    if res:
        game_list = [f"{g['away_team']} @ {g['home_team']}" for g in res]
        selected_game = st.selectbox("🎯 Pick a Game:", game_list)
        game_data = next(g for g in res if f"{g['away_team']} @ {g['home_team']}" == selected_game)

        if st.button("Scan Market"):
            time_now = datetime.now().strftime("%H:%M:%S")
            prices = []
            
            for book in game_data['bookmakers']:
                if book['key'] in ['draftkings', 'fanduel', 'caesars', 'williamhill_us']:
                    label = "Caesars" if "williamhill" in book['key'] else book['title']
                    odds = book['markets'][0]['outcomes'][0]['price']
                    team = book['markets'][0]['outcomes'][0]['name']
                    
                    prices.append({'Book': label, 'Odds': odds, 'Team': team})
                    st.session_state.history.append({
                        'Time': time_now, 'Game': selected_game, 'Bookmaker': label, 'Odds': odds
                    })
            
            # Best Price Alert
            if prices:
                best = max(prices, key=lambda x: x['Odds'])
                st.success(f"🔥 BEST PRICE: {best['Team']} is {best['Odds']} at {best['Book']}")

except:
    st.error("Waiting for data...")

if st.session_state.history:
    df = pd.DataFrame(st.session_state.history)
    if 'selected_game' in locals():
        f_df = df[df['Game'] == selected_game]
        if not f_df.empty:
            fig = px.line(f_df, x='Time', y='Odds', color='Bookmaker', markers=True)
            st.plotly_chart(fig, use_container_width=True)
