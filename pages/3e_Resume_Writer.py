import streamlit as st
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from components.sidebar import render_sidebar
from services.utils import get_subscription, auto_expire_subscription, deduct_credits
from services.ai_engine import ai_generate_resume

st.set_page_config(page_title="AI Resume Writer", page_icon="📄")

COST = 20

# AUTH CHECK
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state["user"]
user_id = user["id"]

render_sidebar()

# SUBSCRIPTION CHECK
auto_expire_subscription(user)
subscription = get_subscription(user_id)

if not subscription or subscription["subscription_status"] != "active":
    st.error("You need an active subscription to use the resume writer.")
    st.stop()

credits = subscription.get("credits", 0)

st.title("📄 AI Resume Writer")
st.write(f"💳 Credits Available: {credits}")

experience = st.text_area("Describe Your Work Experience")
skills = st.text_area("List Your Skills")
education = st.text_area("Enter Education History")

# Disable button if not enough credits OR text is missing
button_disabled = credits < COST or not (experience.strip() and skills.strip() and education.strip())

if st.button(f"Generate Resume (Cost {COST})", disabled=button_disabled):

    ok, balance = deduct_credits(user_id, COST)
    if not ok:
        st.error(balance)
        st.stop()

    st.success(f"{COST} credits deducted. Remaining: {balance}")

    resume = ai_generate_resume(experience, skills, education)
    st.write(resume)
