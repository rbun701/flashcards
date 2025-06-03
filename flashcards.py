# flashcards.py
import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="Pega Knowledge Buddy Flashcards", layout="centered")
st.title("🧠 Pega Knowledge Buddy Flashcards (v24.2)")

@st.cache_data
def load_data():
    csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQqxElEi3CxDFD-zytiV5_c8xfmXvCFMj_PXfTj9evGyyC3GJNDcYLtmMsbFlVVjuvTETg_XHgSMd_k/pub?output=csv"
    return pd.read_csv(csv_url)

df = load_data()

# ---- Startup screen ----
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

        concepts = filtered["Concept ID"].unique()
        selected_concepts = random.sample(list(concepts), min(15, len(concepts)))
        session_df = filtered[filtered["Concept ID"].isin(selected_concepts)].groupby("Concept ID").apply(lambda g: g.sample(1)).reset_index(drop=True)

        st.session_state.session_df = session_df
        st.session_state.index = 0
        st.session_state.score = 0
        st.session_state.responses = []
        st.session_state.started = True
        st.session_state.awaiting_submit = True
        st.session_state.user_selection = None
        st.rerun()
    st.stop()

# ---- Quiz display ----
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
        st.success("🏆 Great job! You got all topics correct.")

    if st.button("Start Over"):
        for key in ["started", "index", "score", "responses", "session_df", "awaiting_submit", "user_selection"]:
            st.session_state.pop(key, None)
        st.rerun()
    st.stop()

q = session_df.iloc[st.session_state.index]

st.markdown(f"**Question {st.session_state.index + 1} of {len(session_df)}**")
st.markdown(f"**Topic:** {q['Topic']}  |  **Difficulty:** {q['Difficulty']}\n\n")
st.write(q["Question"])

# Randomly select 3 incorrect options from 5
distractors = [q[f"Incorrect Option {i}"] for i in range(1, 6)]
chosen_distractors = random.sample(distractors, 3)
choices = [q["Correct Answer"]] + chosen_distractors
random.shuffle(choices)

# Capture selection into state
if f"selection_{st.session_state.index}" not in st.session_state:
    st.session_state[f"selection_{st.session_state.index}"] = None

st.session_state[f"selection_{st.session_state.index}"] = st.radio(
    "Choose your answer:", choices, index=None, key=f"radio_{st.session_state.index}")

if "awaiting_submit" not in st.session_state:
    st.session_state.awaiting_submit = True

if st.session_state.awaiting_submit:
    if st.button("Submit Answer"):
        selected = st.session_state[f"selection_{st.session_state.index}"]
        if selected is None:
            st.warning("Please select an answer before submitting.")
        else:
            correct = selected == q["Correct Answer"]
            st.session_state.responses.append({
                "Concept ID": q["Concept ID"],
                "Question": q["Question"],
                "Selected": selected,
                "Correct": q["Correct Answer"],
                "Was Correct": correct,
                "Topic": q["Topic"]
            })
            if correct:
                st.session_state.score += 1
                st.success("✅ Correct!")
            else:
                st.error(f"❌ Incorrect. Correct answer: {q['Correct Answer']}")

            st.session_state.awaiting_submit = False
else:
    if st.button("Next Question"):
        st.session_state.index += 1
        st.session_state.awaiting_submit = True
        st.rerun()
