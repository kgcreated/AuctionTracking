import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import os
from datetime import datetime

st.set_page_config(page_title="A's Sulayve Stats", layout="wide")

# --- 1. CONNECTION & KEY CHECK ---
API_KEY = os.environ.get("THE_ODDS_API_KEY")

if not API_KEY:
    st.error("🚨 API KEY MISSING: Please add 'THE_ODDS_API_KEY' to your Render Environment Variables.")
    st.stop()

# Initialize memory
if "history" not in st.session_state: st.session_state.history = []
if "snapshot_vault" not in st.session_state: st.session_state.snapshot_vault = {}

st.title("📊 Market Tracker & Value Radar")

# Sport Selector
sport = st.radio("Sport:", ["NBA Basketball", "NFL Football"], horizontal=True)
sport_key = "basketball_nba" if "NBA" in sport else "americanfootball_nfl"

# --- 2. DATA PULLING (AUTOMATED) ---
@st.cache_data(ttl=60) # Refreshes every minute
def get_all_data(key, s_key):
    try:
        odds_url = f"https://api.the-odds-api.com/v4/sports/{s_key}/odds/?apiKey={key}&regions=us&markets=h2h"
        scores_url = f"https://api.the-odds-api.com/v4/sports/{s_key}/scores/?apiKey={key}&daysFrom=1"
        return requests.get(odds_url).json(), requests.get(scores_url).json()
    except:
        return None, None

live_res, past_res = get_all_data(API_KEY, sport_key)

if live_res is None:
    st.warning("🔄 Establishing Connection to Market... Please wait 5 seconds.")
    st.stop()

# --- 3. GAME SELECTOR ---
all_games = []
for g in (live_res if isinstance(live_res, list) else []):
    all_games.append({"label": f"🟢 [LIVE/UPCOMING] {g['away_team']} @ {g['home_team']}", "data": g, "type": "live"})
for g in (past_res if isinstance(past_res, list) else []):
    if g.get('completed'):
        all_games.append({"label": f"🏁 [FINAL] {g['away_team']} @ {g['home_team']}", "data": g, "type": "past"})

if all_games:
    selected_label = st.selectbox("🎯 Target Matchup:", [g['label'] for g in all_games])
    selected_game = next(x for x in all_games if x['label'] == selected_label)
    g_data = selected_game['data']

    # Display Scores for Final Games
    if selected_game['type'] == 'past' and g_data.get('scores'):
        s = g_data['scores']
        st.subheader(f"🏆 Final: {s[0]['name']} {s[0]['score']} - {s[1]['name']} {s[1]['score']}")

    # --- 4. PRE-GAME VALUE RADAR (The Requested Feature) ---
    if st.button("🔥 SCAN FOR VALUE"):
        time_now = datetime.now().strftime("%H:%M")
        prices = []
        
        for book in g_data.get('bookmakers', []):
            if book['key'] in ['draftkings', 'fanduel', 'caesars', 'williamhill_us']:
                label = "Caesars" if "william" in book['key'] else book['title']
                market = book['markets'][0]['outcomes']
                
                # We track the AWAY team (index 0) for comparison
                prices.append({
                    'Book': label, 
                    'Team': market[0]['name'],
                    'Odds': market[0]['price'],
                    'Last Update': datetime.fromtimestamp(book.get('last_update', 0)).strftime("%H:%M")
                })
        
        if prices:
            df_val = pd.DataFrame(prices)
            avg_odds = df_val['Odds'].mean()
            
            # Identify the Best Line (Highest payout)
            best_idx = df_val['Odds'].idxmax()
            best_book = df_val.loc[best_idx, 'Book']
            
            st.write("### 🧭 Value Radar Analysis")
            st.info(f"The Market Consensus for **{df_val.loc[0, 'Team']}** is **{avg_odds:.2f}**")
            
            # Highlight where to bet
            st.success(f"💰 **RECOMMENDED BOOK:** Bet at **{best_book}** ({df_val['Odds'].max()}). "
                       f"It is {((df_val['Odds'].max() - avg_odds)/avg_odds)*100:.1f}% better than the average.")
            
            st.table(df_val)
            st.session_state.snapshot_vault[selected_label] = prices

# --- 5. VISUAL TRACKER ---
if st.session_state.history:
    df = pd.DataFrame(st.session_state.history)
    f_df = df[df['Game'] == selected_label]
    if not f_df.empty:
        fig = px.line(f_df, x='Time', y='Odds', color='Bookmaker', markers=True, title="Auction Price Movement")
        st.plotly_chart(fig, use_container_width=True)

