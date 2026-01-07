import streamlit as st

st.title("🎯 Edge & Bet Sizing")
st.write("Calculates exactly how much to bet based on your Wallet.")

best_odds = st.number_input("Best American Odds Found", value=100)
win_prob = st.slider("Your Win Confidence (%)", 1, 100, 52)

# Kelly Criterion Math
b = best_odds/100 if best_odds > 0 else 100/abs(best_odds)
p = win_prob / 100
q = 1 - p
edge = (b * p - q) / b

st.divider()

if edge > 0:
    # Uses 1/4 Kelly for safety
    bet_amount = st.session_state.bankroll * edge * 0.25
    st.success(f"✅ Edge Detected! Recommended Bet: ${bet_amount:.2f}")
    st.write(f"This bet is based on your total wallet of ${st.session_state.bankroll}")
else:
    st.error("❌ No mathematical edge found at these odds.")
