import streamlit as st

st.title("Rake poker ref.lol Calculator")
st.write("see out how much the sportsbook is 'taxing' the line.")

col1, col2 = st.columns(2)
odds_a = col1.number_input("Away Team Odds", value=-110)
odds_h = col2.number_input("Home Team Odds", value=-110)

def get_prob(odds):
    return 100/(odds+100) if odds > 0 else abs(odds)/(abs(odds)+100)

vig = (get_prob(odds_a) + get_prob(odds_h) - 1) * 100
st.metric("Total Bookie Vig", f"{vig:.2f}%")

if vig < 3:
    st.success("High Value Market (Low Vig)")
elif vig > 7:
    st.error("Avoid: High Vig Market")
