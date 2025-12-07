import streamlit as st
from components.sidebar import render_sidebar
from services.utils import (
    get_subscription,
    auto_expire_subscription,
    deduct_credits
)
from services.ai_engine import ai_generate_resume

COST = 8
st.set_page_config(page_title="AI Resume Writer | Chumcred", page_icon="📄")

# -------------------- AUTH CHECK --------------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state.get("user")
if not isinstance(user, dict):
    st.switch_page("app.py")

user_id = user["id"]

# Sidebar
render_sidebar()

# -------------------- SUBSCRIPTION --------------------
auto_expire_subscription(user)
subscription = get_subscription(user_id)

if not subscription or subscription.get("subscription_status") != "active":
    st.error("You need an active subscription to use the Resume Writer.")
    st.stop()

credits = subscription.get("credits", 0)

# -------------------- PAGE UI --------------------
st.title("📄 AI Resume Writer")
st.info(f"💳 Credits Available: **{credits}**")

resume_text = st.text_area("Paste your existing resume")
job_description = st.text_area("Paste job description")

if st.button(f"Generate Resume (Cost {COST} credits)", disabled=credits < COST):

    if not resume_text.strip() or not job_description.strip():
        st.warning("Please paste both resume and job description.")
        st.stop()

    ok, new_balance = deduct_credits(user_id, COST)
    if not ok:
        st.error(new_balance)
        st.stop()

    st.session_state.subscription = get_subscription(user_id)
    st.success(f"✔ {COST} credits deducted. New balance: {new_balance}")

    result = ai_generate_resume(resume_text, job_description)
    st.write(result)
