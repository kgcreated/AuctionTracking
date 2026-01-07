import streamlit as st

st.set_page_config(page_title="Auction Tracking", layout="wide", page_icon="🏆")
st.title("🏆 Auction Tracking: Home")

if "bankroll" not in st.session_state:
    st.session_state.bankroll = 1000.0
if "history" not in st.session_state:
    st.session_state.history = []

st.sidebar.success("Select a tool from the menu.")
st.session_state.bankroll = st.sidebar.number_input("Current Bankroll ($)", value=st.session_state.bankroll)
st.write("### Welcome to Auction Tracking.")
st.write("Site Status: **Online**")
