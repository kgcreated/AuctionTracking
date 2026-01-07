import streamlit as st

# This changes what he sees on his browser tab
st.set_page_config(page_title="A's Sulayve Stats", layout="wide", page_icon="🏆")

# Memory setup
if "bankroll" not in st.session_state:
    st.session_state.bankroll = 1000.0
if "history" not in st.session_state:
    st.session_state.history = []

# This is the big title at the top of the home screen
st.title("🏆 A’s Sulayve Stats")

st.divider()

# The "Wallet RN" section
st.subheader("Wallet RN")
st.session_state.bankroll = st.number_input("Update your bankroll:", value=st.session_state.bankroll)

st.write("---")
st.success("✅ Market Data: Connected")

# Visual Metrics
col1, col2 = st.columns(2)
col1.metric("Available Funds", f"${st.session_state.bankroll:,.2f}")
col2.write("### Quick Tips")
col2.info("Use the sidebar to flip between live odds and edge calculations.")
