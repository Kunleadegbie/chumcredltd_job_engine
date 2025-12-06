import streamlit as st
from services.utils import get_subscription, has_enough_credits, deduct_credits
from services.ai_engine import ai_generate_match_score

COST = 5

st.title("📊 Match Score Analysis")

user = st.session_state.user
user_id = user["id"]

subscription = get_subscription(user_id)
credits = subscription.get("credits", 0)

st.info(f"💳 Credits Available: **{credits}**")

resume_text = st.text_area("Paste your Resume")
job_description = st.text_area("Paste Job Description")

disabled = credits < COST

if st.button(f"Run Match Score (Cost {COST} credits)", disabled=disabled):

    ok, result = deduct_credits(user_id, COST)
    if not ok:
        st.error(result)
        st.stop()

    st.session_state.subscription = get_subscription(user_id)

    st.success(f"✔ {COST} credits deducted. New balance: {result}")

    output = ai_generate_match_score(resume_text, job_description)
    st.write(output)
