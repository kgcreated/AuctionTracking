import streamlit as st

st.set_page_config(page_title="Auction Tracking", layout="wide", page_icon="🏆")

st.title(" Knee-gar Oddd: Home")

# Sidebar Bankroll
if "bankroll" not in st.session_state:
    st.session_state.bankroll = 1000.0

st.sidebar.header("Wallet")
st.session_state.wallet = st.sidebar.number_input("Total wallet ($)", value=st.session_state.wallet)

# Main Screen Instructions
st.write("---")
st.success("✅ **System Online:** Connected to The Odds API")
st.write("### Guide")
st.info("👈 **Tap the arrow in the top-left corner** to open the graphs and calcs!")

col1, col2, col3 = st.columns(3)
col1.metric("Wallet rn", f"${st.session_state.wallet}")
col2.write(" Check Line Graphs for Line Odds.")
col3.write(" Use Calculators to calculate bet size/taxes.")

st.warning("Trust ur gut, but maybe this will help (except with lamar/ravens u musst use pure vibes).")
