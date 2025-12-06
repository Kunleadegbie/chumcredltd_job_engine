import streamlit as st
from services.utils import get_subscription, deduct_credits
from services.ai_engine import ai_generate_resume

COST = 20

st.title("📄 AI Resume Writer")

user_id = st.session_state.user["id"]
subscription = get_subscription(user_id)
credits = subscription.get("credits", 0)

st.info(f"💳 Credits Available: **{credits}**")

profile = st.text_area("Paste Your Professional Profile")
job_title = st.text_input("Target Job Title (optional)")

if st.button(f"Generate Resume (Cost {COST})", disabled=credits < COST):

    ok, result = deduct_credits(user_id, COST)
    if not ok:
        st.error(result)
        st.stop()

    st.session_state.subscription = get_subscription(user_id)

    st.success(f"✔ {COST} credits deducted. New balance: {result}")

    output = ai_generate_resume(profile, job_title)
    st.write(output)
