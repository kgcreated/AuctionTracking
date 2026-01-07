import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import os
from datetime import datetime

st.set_page_config(page_title="Live Tracker", layout="wide")

# Memory for Graph & Vault
if "history" not in st.session_state: st.session_state.history = []
if "snapshot_vault" not in st.session_state: st.session_state.snapshot_vault = {}

st.title("📊 Live Market Tracker")

# 1. API CONFIG
API_KEY = os.environ.get("THE_ODDS_API_KEY")
sport = st.radio("Sport:", ["NBA Basketball", "NFL Football"], horizontal=True)
sport_key = "basketball_nba" if "NBA" in sport else "americanfootball_nfl"

# 2. DATA PULL
try:
    odds_url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/?apiKey={API_KEY}&regions=us&markets=h2h"
    scores_url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/scores/?apiKey={API_KEY}&daysFrom=1"
    
    live_res = requests.get(odds_url).json()
    past_res = requests.get(scores_url).json()

    all_games = []
    # Add Past Games first
    for g in (past_res if isinstance(past_res, list) else []):
        if g.get('completed'):
            all_games.append({"label": f"🏁 [FINAL] {g['away_team']} @ {g['home_team']}", "data": g, "type": "past"})
    # Add Live Games
    for g in (live_res if isinstance(live_res, list) else []):
        all_games.append({"label": f"🟢 [LIVE] {g['away_team']} @ {g['home_team']}", "data": g, "type": "live"})

    if all_games:
        selected_label = st.selectbox("🎯 Pick Matchup:", [g['label'] for g in all_games])
        selected_game = next(x for x in all_games if x['label'] == selected_label)
        g_data = selected_game['data']

        # Score Display
        if selected_game['type'] == 'past' and g_data.get('scores'):
            s = g_data['scores']
            st.subheader(f"🏆 {s[0]['name']} {s[0]['score']} - {s[1]['name']} {s[1]['score']}")

        if st.button("🔥 SCAN MARKET"):
            time_now = datetime.now().strftime("%H:%M")
            prices = []
            
            for book in g_data.get('bookmakers', []):
                if book['key'] in ['draftkings', 'fanduel', 'caesars', 'williamhill_us']:
                    label = "Caesars" if "william" in book['key'] else book['title']
                    odds = book['markets'][0]['outcomes'][0]['price']
                    
                    # INACCURACY CHECK: Check if data is stale
                    update_time = datetime.fromtimestamp(book.get('last_update', 0))
                    is_fresh = (datetime.now() - update_time).total_seconds() < 3600 # 1 hour
                    
                    prices.append({
                        'Book': label, 'Odds': odds, 
                        'Status': "✅ FRESH" if is_fresh else "⚠️ STALE",
                        'Update': update_time.strftime("%H:%M")
                    })
                    st.session_state.history.append({'Time': time_now, 'Game': selected_label, 'Bookmaker': label, 'Odds': odds})
            
            if prices:
                # STALE LINE ALERT LOGIC
                dk_fd = [p['Odds'] for p in prices if p['Book'] in ['DraftKings', 'FanDuel']]
                if len(dk_fd) >= 1:
                    avg = sum(dk_fd)/len(dk_fd)
                    for p in prices:
                        if p['Odds'] >= (avg + 7):
                            st.warning(f"🚨 STALE LINE: {p['Book']} lagging at {p['Odds']} (Market: {avg:.0f})")
                
                st.session_state.snapshot_vault[selected_label] = prices

except:
    st.error("API Connection Pending...")

# --- DISPLAY ---
if selected_label in st.session_state.snapshot_vault:
    st.write("### 💵 Latest Snapshot")
    st.table(pd.DataFrame(st.session_state.snapshot_vault[selected_label]))

if st.session_state.history:
    df = pd.DataFrame(st.session_state.history)
    f_df = df[df['Game'] == selected_label]
    if not f_df.empty:
        fig = px.line(f_df, x='Time', y='Odds', color='Bookmaker', markers=True, title="Market Auction Graph")
        st.plotly_chart(fig, use_container_width=True)

