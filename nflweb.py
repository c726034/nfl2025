import streamlit as st
import nflmod_web as nflmod

st.set_page_config(page_title="NFL Degen Contest Tools", layout="wide")
st.title("NFL Degen Contest Tools")

tabs = st.tabs(["Get Lines", "Get Picks", "Get Scores"])

# --- Get Lines ---
with tabs[0]:
    st.subheader("Retrieve and optionally email/write lines")
    write = st.selectbox("Write to sheet?", ["N", "Y"])
    send = st.selectbox("Send email to players?", ["N", "Y"])
    nflweek = st.number_input("NFL Week (leave blank for current)", min_value=1, max_value=18, step=1)
    if st.button("Run get_lines()"):
        week = int(nflweek) if nflweek else None
        df = nflmod.get_lines(write=write, send=send, nflweek=week)
        st.dataframe(df)

# --- Get Picks ---
with tabs[1]:
    st.subheader("Retrieve picks")
    picksday = st.selectbox("Pick Day (T=Thurs, S=Sun, X=View Only)", ["T", "S", "X"])
    nflweek = st.number_input("NFL Week (leave blank for current)", min_value=1, max_value=18, step=1, key="picksweek")
    if st.button("Run get_picks()"):
        week = int(nflweek) if nflweek else None
        df = nflmod.get_picks(picksday=picksday, w=week)
        st.dataframe(df)

# --- Get Scores ---
with tabs[2]:
    st.subheader("Retrieve game scores")
    day1 = st.text_input("Day 1 (YYYY-MM-DD)", "")
    day2 = st.text_input("Day 2 (YYYY-MM-DD)", "")
    if st.button("Run get_scores()"):
        d1 = day1 if day1.strip() else None
        d2 = day2 if day2.strip() else None
        df = nflmod.get_scores(day1=d1, day2=d2)
        st.dataframe(df)
