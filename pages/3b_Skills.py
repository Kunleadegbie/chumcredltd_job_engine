import streamlit as st
from components.sidebar import render_sidebar
from services.utils import (
    get_subscription,
    auto_expire_subscription,
    deduct_credits
)
from services.ai_engine import ai_extract_skills

from chumcred_job_engine.components.sidebar import render_sidebar

from chumcred_job_engine.services.utils import (
    get_subscription,
    auto_expire_subscription,
    deduct_credits,
)

from chumcred_job_engine.services.ai_engine import ai_extract_skills


COST = 5
st.set_page_config(page_title="Skills Extractor | Chumcred", page_icon="🧠")

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
    st.error("You need an active subscription to use Skills Extractor.")
    st.stop()

credits = subscription.get("credits", 0)

# -------------------- PAGE UI --------------------
st.title("🧠 Extract Skills from Resume")
st.info(f"💳 Credits Available: **{credits}**")

resume_text = st.text_area("Paste your Resume Content")

if st.button(f"Extract Skills (Cost {COST} credits)", disabled=credits < COST):

    if not resume_text.strip():
        st.warning("Please paste your resume text.")
        st.stop()

    ok, new_balance = deduct_credits(user_id, COST)
    if not ok:
        st.error(new_balance)
        st.stop()

    st.session_state.subscription = get_subscription(user_id)
    st.success(f"✔ {COST} credits deducted. New balance: {new_balance}")

    result = ai_extract_skills(resume_text)
    st.write(result)
