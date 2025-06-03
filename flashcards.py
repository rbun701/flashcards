# flashcards.py
import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="Pega Knowledge Buddy Flashcards", layout="centered")
st.title("🧠 Pega Knowledge Buddy Flashcards (v24.2)")

@st.cache_data

def load_data():
    try:
        csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQqxElEi3CxDFD-zytiV5_c8xfmXvCFMj_PXfTj9evGyyC3GJNDcYLtmMsbFlVVjuvTETg_XHgSMd_k/pub?output=csv"
        return pd.read_csv(csv_url)
    except Exception as e:
        st.error("Failed to load flashcard data. Please check your connection or data source.")
        st.stop()

df = load_data()

if "started" not in st.session_state:
    st.session_state.started = False
if not st.session_state.started:
    st.subheader("Welcome to the Flashcards App")
    st.write("Select your learning level and topic to begin:")

    level = st.selectbox("Choose difficulty:", ["All", "Beginner", "Intermediate", "Expert"])
    topic = st.selectbox("Choose topic:", ["All"] + sorted(df["Topic"].unique()))

    if st.button("Start Quiz"):
        filtered = df.copy()
        if level != "All":
            filtered = filtered[filtered["Difficulty"] == level]
        if topic != "All":
            filtered = filtered[filtered["Topic"] == topic]

        if filtered.empty:
            st.warning("No questions available for the selected filters. Please try a different combination.")
            st.stop()

        concepts = filtered["Concept ID"].unique()
        if len(concepts) == 0:
            st.warning("No unique concepts found. Check your filters.")
            st.stop()

        selected_concepts = random.sample(list(concepts), min(15, len(concepts)))
        session_df = filtered[filtered["Concept ID"].isin(selected_concepts)].groupby("Concept ID").apply(lambda g: g.sample(1)).reset_index(drop=True)

        st.session_state.session_df = session_df
        st.session_state.index = 0
        st.session_state.score = 0
        st.session_state.responses = []
        st.session_state.started = True
        st.session_state.awaiting_submit = True
        st.session_state.selected_answer = None
        st.session_state.choices = {}
        st.rerun()
    st.stop()

try:
    session_df = st.session_state.session_df
    if st.session_state.index >= len(session_df):
        st.subheader("📊 Session Summary")
        st.write(f"**Score:** {st.session_state.score} / {len(session_df)}")

        summary_df = pd.DataFrame(st.session_state.responses)
        incorrect_by_topic = summary_df[~summary_df["Was Correct"]].groupby("Topic").size()

        if not incorrect_by_topic.empty:
            st.warning("**Topics to Review:**")
            for topic, count in incorrect_by_topic.items():
                st.write(f"- {topic} ({count} missed)")
        else:
    if st.button("Next Question"):
        st.session_state.index += 1
        st.session_state.awaiting_submit = True
        st.session_state.selected_answer = None
        st.rerun()
            st.session_state.index += 1
            st.session_state.awaiting_submit = True
            st.session_state.selected_answer = None
            st.rerun()

except Exception as e:
    st.error("⚠️ Something went wrong during the quiz. Please try restarting.")
    st.exception(e)
