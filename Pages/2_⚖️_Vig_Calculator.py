import streamlit as st

st.title("⚖️ Vig & Overround Calculator")

col1, col2 = st.columns(2)
odds_a = col1.number_input("Away Team Odds", value=-110)
odds_h = col2.number_input("Home Team Odds", value=-110)

def get_prob(odds):
    if odds > 0:
        return 100 / (odds + 100)
    else:
        return abs(odds) / (abs(odds) + 100)

p1 = get_prob(odds_a)
p2 = get_prob(odds_h)
vig = (p1 + p2 - 1) * 100

st.divider()
st.metric("Total Bookie Vig", f"{vig:.2f}%")
