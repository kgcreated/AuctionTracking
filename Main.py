import streamlit as st
st.set_page_config(page_title="Auction Tracking", layout="wide", page_icon="🏆")
st.title("🏆 Auction Tracking: Home")
if "bankroll" not in st.session_state:
    st.session_state.bankroll = 1000.0
if "history" not in st.session_state:
    st.session_state.history = []
st.sidebar.info("Navigate using the menu.")
st.write("### Site is Online.")
