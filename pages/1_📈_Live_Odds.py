import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import os
from datetime import datetime, timezone

st.set_page_config(page_title="A's Sulayve Stats", layout="wide")

# --- 1. MEMORY & CACHE LOGIC ---
if "history" not in st.session_state: st.session_state.history = []
if "snapshot_vault" not in st.session_state: st.session_state.snapshot_vault = {}

# This function prevents the app from pulling "old" data from its own memory
@st.cache_data(ttl=60)
def get_market_data(api_key, sport_key):
    # The 't' parameter trick bypasses server-side caching
    t_stamp = int(datetime.now().timestamp())
    odds_url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/?apiKey={api_key}&regions=us&markets=h2h&t={t_stamp}"
    score_url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/scores/?apiKey={api_key}&daysFrom=2&t={t_stamp}"
    
    try:
        o_res = requests.get(odds_url).json()
        s_res = requests.get(score_url).json()
        return o_res, s_res
    except:
        return None, None

# --- 2. SETUP & KEYS ---
API_KEY = os.environ.get("THE_ODDS_API_KEY")
st.title("📊 Live Tracker (Anti-Stale)")

with st.sidebar:
    st.header("Controls")
    if st.button("🔄 Force Refresh Data"):
        st.cache_data.clear()
        st.rerun()
    st.info("Data auto-refreshes every 60s")

sport_choice = st.radio("Market:", ["NBA Basketball", "NFL Football"], horizontal=True)
sport_map = {"NBA Basketball": "basketball_nba", "NFL Football": "americanfootball_nfl"}

# --- 3. EXECUTE DATA PULL ---
live_res, past_res = get_market_data(API_KEY, sport_map[sport_choice])

if not live_res:
    st.warning("Connecting to API... Make sure your API Key is set in Render.")
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
    selected_game = next(x for x in all_games if x['label'] == selected_label)
    g_data = selected_game['data']

    # Final Score Display
    if selected_game['type'] == 'past' and g_data.get('scores'):
        s = g_data['scores']
        st.header(f"🏆 Final: {s[0]['name']} {s[0]['score']} - {s[1]['name']} {s[1]['score']}")

    # --- 5. THE ANALYSIS ENGINE ---
    if st.button("🔥 Scan Market Now"):
        time_now = datetime.now().strftime("%H:%M:%S")
        prices = []
        
        for book in g_data.get('bookmakers', []):
            if book['key'] in ['draftkings', 'fanduel', 'caesars', 'williamhill_us']:
                label = "Caesars" if "william" in book['key'] else book['title']
                odds = book['markets'][0]['outcomes'][0]['price']
                team = book['markets'][0]['outcomes'][0]['name']
                
                # Timestamp Fix: Handle string or number
                raw_up = book.get('last_update', 0)
                try:
                    if isinstance(raw_up, str):
                        dt = datetime.fromisoformat(raw_up.replace('Z', '+00:00'))
                    else:
                        dt = datetime.fromtimestamp(raw_up, tz=timezone.utc)
                    up_time = dt.strftime("%H:%M")
                    # Check if the line is more than 30 mins old
                    is_fresh = (datetime.now(timezone.utc) - dt).total_seconds() < 1800
                except:
                    up_time, is_fresh = "Unknown", False

                prices.append({
                    'Book': label, 'Team': team, 'Odds': odds, 
                    'Status': "✅ FRESH" if is_fresh else "⚠️ STALE", 
                    'Line Updated': up_time
                })
                st.session_state.history.append({'Time': time_now, 'Game': selected_label, 'Bookmaker': label, 'Odds': odds})
        
        if prices:
            # VALUE RADAR: Find the Best Price
            df_p = pd.DataFrame(prices)
            best_idx = df_p['Odds'].idxmax()
            best_book = df_p.loc[best_idx, 'Book']
            best_odds = df_p.loc[best_idx, 'Odds']
            
            st.success(f"💰 **VALUE RADAR:** The best price for {df_p.loc[0, 'Team']} is **{best_odds}** at **{best_book}**.")
            st.session_state.snapshot_vault[selected_label] = prices

# --- 6. DISPLAY SNAPSHOTS & GRAPHS ---
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

