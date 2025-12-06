import streamlit as st
from services.utils import get_subscription, deduct_credits
from services.ai_engine import ai_generate_cover_letter

COST = 5

st.title("✉️ AI Cover Letter Generator")

user_id = st.session_state.user["id"]
subscription = get_subscription(user_id)
credits = subscription.get("credits", 0)

st.info(f"💳 Credits Available: **{credits}**")

resume = st.text_area("Paste your Resume")
job_description = st.text_area("Paste Job Description")

if st.button(f"Generate Cover Letter (Cost {COST})", disabled=credits < COST):

    ok, result = deduct_credits(user_id, COST)
    if not ok:
        st.error(result)
        st.stop()

    st.session_state.subscription = get_subscription(user_id)

    st.success(f"✔ {COST} credits deducted. New balance: {result}")

    output = ai_generate_cover_letter(resume, job_description)
    st.write(output)
