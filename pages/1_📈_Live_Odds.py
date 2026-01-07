import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import os
from datetime import datetime

st.set_page_config(page_title="A's Sulayve Stats", layout="wide")

# --- INITIALIZE MEMORY ---
if "history" not in st.session_state: st.session_state.history = []
if "snapshot_vault" not in st.session_state: st.session_state.snapshot_vault = {}

st.title("📊 Live Odds & Value Radar")

# Configuration
API_KEY = os.environ.get("THE_ODDS_API_KEY")
if not API_KEY:
    st.error("API Key missing in Render settings.")
    st.stop()

sport = st.radio("Sport:", ["NBA Basketball", "NFL Football"], horizontal=True)
sport_key = "basketball_nba" if "NBA" in sport else "americanfootball_nfl"

# --- DATA FETCHING ---
try:
    odds_url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/?apiKey={API_KEY}&regions=us&markets=h2h"
    scores_url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/scores/?apiKey={API_KEY}&daysFrom=2"
    
    live_res = requests.get(odds_url).json()
    past_res = requests.get(scores_url).json()

    all_games = []
    if isinstance(live_res, list):
        for g in live_res:
            all_games.append({"label": f"🟢 [LIVE] {g['away_team']} @ {g['home_team']}", "data": g, "type": "live"})
    if isinstance(past_res, list):
        for g in past_res:
            if g.get('completed'):
                all_games.append({"label": f"🏁 [FINAL] {g['away_team']} @ {g['home_team']}", "data": g, "type": "past"})

    if all_games:
        selected_label = st.selectbox("🎯 Target Game:", [g['label'] for g in all_games])
        selected_game = next(x for x in all_games if x['label'] == selected_label)
        g_data = selected_game['data']

        # Show Final Score if completed
        if selected_game['type'] == 'past' and g_data.get('scores'):
            s = g_data['scores']
            st.header(f"🏆 Final: {s[0]['name']} {s[0]['score']} - {s[1]['name']} {s[1]['score']}")

        if st.button("🔥 SCAN MARKET"):
            time_now = datetime.now().strftime("%H:%M")
            prices = []
            
            for book in g_data.get('bookmakers', []):
                if book['key'] in ['draftkings', 'fanduel', 'caesars', 'williamhill_us']:
                    label = "Caesars" if "william" in book['key'] else book['title']
                    odds = book['markets'][0]['outcomes'][0]['price']
                    team = book['markets'][0]['outcomes'][0]['name']
                    
                    # --- THE TIMESTAMP FIX ---
                    raw_up = book.get('last_update', 0)
                    try:
                        if isinstance(raw_up, str):
                            # Handles "2026-01-07T..." format
                            dt_obj = datetime.fromisoformat(raw_up.replace('Z', '+00:00'))
                        else:
                            # Handles Unix number format
                            dt_obj = datetime.fromtimestamp(raw_up)
                        
                        up_time = dt_obj.strftime("%H:%M")
                        is_fresh = (datetime.now() - dt_obj).total_seconds() < 7200 # 2 hours
                    except:
                        up_time, is_fresh = "Unknown", False

                    prices.append({
                        'Book': label, 'Team': team, 'Odds': odds, 
                        'Status': "✅ FRESH" if is_fresh else "⚠️ STALE", 'Updated': up_time
                    })
                    st.session_state.history.append({'Time': time_now, 'Game': selected_label, 'Bookmaker': label, 'Odds': odds})
            
            if prices:
                # Value Radar: Highlight the best price
                df_p = pd.DataFrame(prices)
                best_odds = df_p['Odds'].max()
                best_book = df_p.loc[df_p['Odds'].idxmax(), 'Book']
                
                st.success(f"💰 **BEST PRICE:** {best_book} at {best_odds}")
                st.session_state.snapshot_vault[selected_label] = prices

except Exception as e:
    st.error(f"Waiting for stable data connection... {e}")

# --- DISPLAY ---
st.divider()
if selected_label in st.session_state.snapshot_vault:
    st.write("### 💵 Verified Odds Analysis")
    st.table(pd.DataFrame(st.session_state.snapshot_vault[selected_label]))

if st.session_state.history:
    df = pd.DataFrame(st.session_state.history)
    f_df = df[df['Game'] == selected_label]
    if not f_df.empty:
        fig = px.line(f_df, x='Time', y='Odds', color='Bookmaker', markers=True, title="Auction Movement")
        st.plotly_chart(fig, use_container_width=True)

