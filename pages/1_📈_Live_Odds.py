import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import os
from datetime import datetime, timedelta

st.set_page_config(page_title="A's Sulayve Stats", layout="wide")

if "history" not in st.session_state:
    st.session_state.history = []

st.title("📊 Live Odds & Results")

sport_choice = st.radio("Market:", ["NBA Basketball", "NFL Football"], horizontal=True)
sport_map = {"NBA Basketball": "basketball_nba", "NFL Football": "americanfootball_nfl"}

API_KEY = os.environ.get("THE_ODDS_API_KEY") or st.secrets.get("THE_ODDS_API_KEY")

# --- DATA FETCHING LOGIC ---
try:
    # 1. Try to get LIVE/UPCOMING games first
    url = f"https://api.the-odds-api.com/v4/sports/{sport_map[sport_choice]}/odds/?apiKey={API_KEY}&regions=us&markets=h2h"
    res = requests.get(url).json()
    
    is_historical = False

    # 2. If no live games, fetch RECENT RESULTS (Past 3 days)
    if not res:
        st.info("No live games found. Fetching recent results...")
        score_url = f"https://api.the-odds-api.com/v4/sports/{sport_map[sport_choice]}/scores/?apiKey={API_KEY}&daysFrom=3"
        res = requests.get(score_url).json()
        is_historical = True

    if res:
        game_list = []
        for g in res:
            status = "🏁 FINAL" if g.get('completed') else "⏳ UPCOMING/LIVE"
            game_list.append(f"{status}: {g['away_team']} @ {g['home_team']}")
        
        selected_game_label = st.selectbox("🎯 Select Game:", game_list)
        
        # Strip the status prefix to find the game data
        clean_name = selected_game_label.split(": ")[1]
        game_data = next(g for g in res if f"{g['away_team']} @ {g['home_team']}" == clean_name)

        if st.button("Scan Market Data"):
            time_now = datetime.now().strftime("%H:%M:%S")
            prices = []
            
            # Note: Historical 'scores' endpoint has slightly different data structure for bookmakers
            bookmakers = game_data.get('bookmakers', [])
            
            if not bookmakers and is_historical:
                st.warning("Final odds aren't available for this completed game, but you can see the score below.")
                if game_data.get('scores'):
                    s = game_data['scores']
                    st.write(f"**Final Score:** {s[0]['name']} {s[0]['score']} - {s[1]['name']} {s[1]['score']}")
            
            for book in bookmakers:
                if book['key'] in ['draftkings', 'fanduel', 'caesars', 'williamhill_us']:
                    label = "Caesars" if "williamhill" in book['key'] else book['title']
                    odds = book['markets'][0]['outcomes'][0]['price']
                    team = book['markets'][0]['outcomes'][0]['name']
                    
                    prices.append({'Book': label, 'Odds': odds, 'Team': team})
                    st.session_state.history.append({
                        'Time': time_now, 'Game': clean_name, 'Bookmaker': label, 'Odds': odds
                    })
            
            if prices:
                best = max(prices, key=lambda x: x['Odds'])
                st.success(f"🔥 BEST PRICE: {best['Team']} is {best['Odds']} at {best['Book']}")

except Exception as e:
    st.error(f"Error: {e}")

# --- GRAPHING ---
if st.session_state.history:
    df = pd.DataFrame(st.session_state.history)
    if 'clean_name' in locals():
        f_df = df[df['Game'] == clean_name]
        if not f_df.empty:
            fig = px.line(f_df, x='Time', y='Odds', color='Bookmaker', markers=True, title=f"Price History: {clean_name}")
            st.plotly_chart(fig, use_container_width=True)

