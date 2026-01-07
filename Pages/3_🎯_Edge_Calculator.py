import streamlit as st

st.title("🎯 Edge & Kelly Criterion")

best_odds = st.number_input("Best Odds Found", value=100)
win_confidence = st.slider("Your Win Probability (%)", 1, 100, 52)

b = best_odds/100 if best_odds > 0 else 100/abs(best_odds)
p = win_confidence / 100
q = 1 - p

kelly_f = (b * p - q) / b

st.divider()

if kelly_f > 0:
    suggested_bet = st.session_state.bankroll * kelly_f * 0.25
    st.success(f"✅ Edge Detected! Suggested Bet: ${suggested_bet:.2f}")
else:
    st.error("❌ No Edge detected.")
