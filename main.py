import streamlit as st

st.set_page_config(page_title="Giving Sulayve Stats", layout="wide", page_icon="🏆")

# Memory setup for Wallet and History
if "bankroll" not in st.session_state:
    st.session_state.bankroll = 1000.0
if "bet_history" not in st.session_state:
    st.session_state.bet_history = []

st.title("🏆 A’s Sulayve Stats")
st.write("---")

# Wallet RN Section
st.subheader("Wallet RN")
st.session_state.bankroll = st.number_input("Update Bankroll:", value=st.session_state.bankroll)
st.metric("Total Funds", f"${st.session_state.bankroll:,.2f}")

st.write("### Quick Log")
col1, col2, col3 = st.columns([2,1,1])
bet_amt = col1.number_input("Bet Profit/Loss ($)", value=10.0, step=5.0)

if col2.button("✅ Won", use_container_width=True):
    st.session_state.bankroll += bet_amt
    st.session_state.bet_history.append(f"🟢 Win: +${bet_amt:.2f}")
    st.rerun()

if col3.button("❌ Lost", use_container_width=True):
    st.session_state.bankroll -= bet_amt
    st.session_state.bet_history.append(f"🔴 Loss: -${bet_amt:.2f}")
    st.rerun()

st.divider()
with st.expander("📜 Recent Session History"):
    if st.session_state.bet_history:
        for entry in reversed(st.session_state.bet_history):
            st.write(entry)
    else:
        st.write("No bets logged this session.")
