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
            st.success("🏆 Great job! You got all topics correct.")

        if st.button("Start Over"):
            for key in ["started", "index", "score", "responses", "session_df", "awaiting_submit", "selected_answer", "choices"]:
                st.session_state.pop(key, None)
            st.rerun()
        st.stop()

    q = session_df.iloc[st.session_state.index]

    st.markdown(f"**Question {st.session_state.index + 1} of {len(session_df)}**")
    st.markdown(f"**Topic:** {q['Topic']}  |  **Difficulty:** {q['Difficulty']}\n\n")
    st.write(q["Question"])

    if f"q_{st.session_state.index}" not in st.session_state.choices:
        distractors = [q.get(f"Incorrect Option {i}", "") for i in range(1, 6)]
        distractors = [d for d in distractors if pd.notna(d) and d != ""]
        chosen_distractors = random.sample(distractors, 3)
        choices = [q["Correct Answer"]] + chosen_distractors
        random.shuffle(choices)
        st.session_state.choices[f"q_{st.session_state.index}"] = choices

    choices = st.session_state.choices[f"q_{st.session_state.index}"]

    if st.session_state.awaiting_submit:
        st.session_state.selected_answer = st.radio("Choose your answer:", choices, index=None, key=f"radio_{st.session_state.index}")
        if st.button("Submit Answer"):
            if st.session_state.selected_answer is None:
                st.warning("Please select an answer before submitting.")
            else:
                selected = st.session_state.selected_answer
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
                # Display placeholder explanation
                st.info("💡 Explanation: This is the correct answer based on how Knowledge Buddy handles this concept.")

                st.session_state.awaiting_submit = False
    else:
        if st.button("Next Question"):
            st.session_state.index += 1
            st.session_state.awaiting_submit = True
            st.session_state.selected_answer = None
            st.rerun()

except Exception as e:
    st.error("⚠️ Something went wrong during the quiz. Please try restarting.")
    st.exception(e)
