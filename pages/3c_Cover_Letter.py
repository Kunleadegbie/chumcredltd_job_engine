import streamlit as st
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from components.sidebar import render_sidebar
from services.utils import get_subscription, auto_expire_subscription, deduct_credits
from services.ai_engine import ai_generate_cover_letter

st.set_page_config(page_title="Cover Letter Generator", page_icon="✉️")

COST = 10

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
    st.error("Subscription required to generate cover letters.")
    st.stop()

credits = subscription.get("credits", 0)

# UI
st.title("✉️ AI Cover Letter Generator")
st.write(f"💳 Credits Available: {credits}")

resume = st.text_area("Paste Resume")
job_desc = st.text_area("Paste Job Description")

if st.button(f"Generate Cover Letter (Cost {COST})", disabled=credits < COST):

    if not resume.strip() or not job_desc.strip():
        st.error("Both resume and job description are required.")
        st.stop()

    ok, balance = deduct_credits(user_id, COST)
    if not ok:
        st.error(balance)
        st.stop()

    st.success(f"{COST} credits deducted. Remaining: {balance}")

    letter = ai_generate_cover_letter(resume, job_desc)
    st.write(letter)
