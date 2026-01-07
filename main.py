import streamlit as st

st.set_page_config(page_title="Auction Tracking", layout="wide", page_icon="🏆")

st.title("🏆 Auction Tracking: Home")

# Sidebar Bankroll
if "bankroll" not in st.session_state:
    st.session_state.bankroll = 1000.0

st.sidebar.header("Wallet")
st.session_state.bankroll = st.sidebar.number_input("Total Bankroll ($)", value=st.session_state.bankroll)

# Main Screen Instructions
st.write("---")
st.success("✅ **System Online:** Connected to The Odds API")
st.write("### Quick Start Guide")
st.info("👈 **Tap the arrow in the top-left corner** to open the navigation menu!")

col1, col2, col3 = st.columns(3)
col1.metric("Current Bankroll", f"${st.session_state.bankroll}")
col2.write("**Step 1:** Check Line Graphs for movement.")
col3.write("**Step 2:** Use Edge Finder to calculate bet size.")

st.warning("Keep this tab open while betting to track real-time changes.")
