# flashcards.py
import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="Pega Knowledge Buddy Flashcards", layout="centered")
st.title("🧠 Pega Knowledge Buddy Flashcards (v24.2)")

@st.cache_data
def load_data():
    csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQqxElEi3CxDFD-zytiV5_c8xfmXvCFMj_PXfTj9evGyyC3GJNDcYLtmMsbFlVVjuvTETg_XHgSMd_k/pub?output=csv"
    df = pd.read_csv(csv_url)
    return df

df = load_data()

# Group by Concept ID and select 1 random variant per concept
unique_concepts = df["Concept ID"].unique()
session_concepts = random.sample(list(unique_concepts), 15)
session_questions = df[df["Concept ID"].isin(session_concepts)]
session_df = session_questions.groupby("Concept ID").apply(lambda g: g.sample(1)).reset_index(drop=True)

# State management
if "index" not in st.session_state:
    st.session_state.index = 0
    st.session_state.score = 0
    st.session_state.responses = []

q = session_df.iloc[st.session_state.index]

st.markdown(f"**{st.session_state.index + 1} of 15**")
st.markdown(f"**Topic:** {q['Topic']}  |  **Difficulty:** {q['Difficulty']}\n\n")
st.write(q["Question"])

# Randomly choose 3 incorrect options
distractors = [q[f"Incorrect Option {i}"] for i in range(1, 6)]
chosen_distractors = random.sample(distractors, 3)
choices = [q["Correct Answer"]] + chosen_distractors
random.shuffle(choices)

selected = st.radio("Choose your answer:", choices)

if st.button("Submit"):
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

    if st.session_state.index < 14:
        st.session_state.index += 1
        st.experimental_rerun()
    else:
        st.markdown("---")
        st.subheader("📊 Session Summary")
        st.write(f"**Score:** {st.session_state.score} / 15")

        summary_df = pd.DataFrame(st.session_state.responses)
        incorrect_by_topic = summary_df[~summary_df["Was Correct"]].groupby("Topic").size()

        if not incorrect_by_topic.empty:
            st.warning("**Topics to Review:**")
            for topic, count in incorrect_by_topic.items():
                st.write(f"- {topic} ({count} missed)")
        else:
            st.success("🏆 Great job! You got all topics correct.")

        if st.button("Restart Quiz"):
            for key in ["index", "score", "responses"]:
                del st.session_state[key]
            st.experimental_rerun()
