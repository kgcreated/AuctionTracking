import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import os
from datetime import datetime, timezone

st.set_page_config(page_title="A.Sulayve Stats", layout="wide")

# --- 1. MEMORY SETUP ---
# We removed the @st.cache_data so every "Scan" is a fresh, direct pull
if "history" not in st.session_state: st.session_state.history = []
if "snapshot_vault" not in st.session_state: st.session_state.snapshot_vault = {}

st.title("📊 Live Tracker (Manual Control)")

# API KEY CHECK
API_KEY = os.environ.get("THE_ODDS_API_KEY")
if not API_KEY:
    st.error("API Key missing. Please add 'THE_ODDS_API_KEY' to Render.")
    st.stop()

# --- 2. SPORT SELECTION ---
sport_choice = st.radio("Market:", ["NBA Basketball", "NFL Football"], horizontal=True)
sport_map = {"NBA Basketball": "basketball_nba", "NFL Football": "americanfootball_nfl"}

# --- 3. DATA FETCHING (No Auto-Refresh) ---
def get_manual_data(api_key, sport_key):
    # We still use the 't' timestamp to ensure the API server gives us fresh data
    t_stamp = int(datetime.now().timestamp())
    odds_url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/?apiKey={api_key}&regions=us&markets=h2h&t={t_stamp}"
    score_url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/scores/?apiKey={api_key}&daysFrom=2&t={t_stamp}"
    
    try:
        o_res = requests.get(odds_url).json()
        s_res = requests.get(score_url).json()
        return o_res, s_res
    except:
        return None, None

live_res, past_res = get_manual_data(API_KEY, sport_map[sport_choice])

if not live_res:
    st.warning("Connecting to market... Select a game to begin.")
    st.stop()

# --- 4. GAME SELECTOR ---
all_games = []
for g in (live_res if isinstance(live_res, list) else []):
    all_games.append({"label": f"🟢 [LIVE] {g['away_team']} @ {g['home_team']}", "data": g, "type": "live"})
for g in (past_res if isinstance(past_res, list) else []):
    if g.get('completed'):
        all_games.append({"label": f"🏁 [FINAL] {g['away_team']} @ {g['home_team']}", "data": g, "type": "past"})

if all_games:
    selected_label = st.selectbox("🎯 Target Game:", [g['label'] for g in all_games])
    selected_game = next(item for item in all_games if item['label'] == selected_label)
    g_data = selected_game['data']

    # Final Score Display
    if selected_game['type'] == 'past' and g_data.get('scores'):
        s = g_data['scores']
        st.header(f"🏆 Final: {s[0]['name']} {s[0]['score']} - {s[1]['name']} {s[1]['score']}")

    # --- 5. THE SCAN BUTTON (The only way to update) ---
    if st.button("🔥 Scan Market Now", use_container_width=True):
        time_now = datetime.now().strftime("%H:%M:%S")
        prices = []
        
        for book in g_data.get('bookmakers', []):
            if book['key'] in ['draftkings', 'fanduel', 'caesars', 'williamhill_us']:
                label = "Caesars" if "william" in book['key'] else book['title']
                odds = book['markets'][0]['outcomes'][0]['price']
                team = book['markets'][0]['outcomes'][0]['name']
                
                # Timestamp Logic
                raw_up = book.get('last_update', 0)
                try:
                    if isinstance(raw_up, str):
                        dt = datetime.fromisoformat(raw_up.replace('Z', '+00:00'))
                    else:
                        dt = datetime.fromtimestamp(raw_up, tz=timezone.utc)
                    up_time = dt.strftime("%H:%M")
                    is_fresh = (datetime.now(timezone.utc) - dt).total_seconds() < 3600 # 1 hour
                except:
                    up_time, is_fresh = "Unknown", False

                prices.append({
                    'Book': label, 'Team': team, 'Odds': odds, 
                    'Status': "✅ FRESH" if is_fresh else "⚠️ STALE", 
                    'Updated': up_time
                })
                st.session_state.history.append({'Time': time_now, 'Game': selected_label, 'Bookmaker': label, 'Odds': odds})
        
        if prices:
            df_p = pd.DataFrame(prices)
            best_odds = df_p['Odds'].max()
            best_book = df_p.loc[df_p['Odds'].idxmax(), 'Book']
            
            st.success(f"💰 **VALUE RADAR:** Best price for {df_p.loc[0, 'Team']} is **{best_odds}** at **{best_book}**.")
            st.session_state.snapshot_vault[selected_label] = prices

# --- 6. DISPLAY ---
st.divider()
if selected_label in st.session_state.snapshot_vault:
    st.write(f"### 💵 Market Snapshot: {selected_label}")
    st.table(pd.DataFrame(st.session_state.snapshot_vault[selected_label]))

if st.session_state.history:
    df = pd.DataFrame(st.session_state.history)
    f_df = df[df['Game'] == selected_label]
    if not f_df.empty:
        fig = px.line(f_df, x='Time', y='Odds', color='Bookmaker', markers=True, title="Auction Price Movement")
        st.plotly_chart(fig, use_container_width=True)

if st.sidebar.button("🗑 Clear Graph History"):
    st.session_state.history = []
    st.rerun()
