import streamlit as st
import os, sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from components.sidebar import render_sidebar
from config.supabase_client import supabase
from services.utils import deduct_credits, get_subscription, auto_expire_subscription
from ai_engine import ai_eligibility_score, extract_text_from_file


st.set_page_config(page_title="Eligibility Checker", page_icon="📊")

if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

render_sidebar()

user = st.session_state["user"]
user_id = user["id"]

st.title("📊 Job Eligibility Checker")

auto_expire_subscription(user_id)
subscription = get_subscription(user_id)

if not subscription or subscription["subscription_status"] != "active":
    st.error("You need an active subscription.")
    st.stop()

if subscription["credits"] < 5:
    st.error("❌ Not enough credits. Eligibility Check requires **5 credits**.")
    st.stop()

resume_file = st.file_uploader("Upload Resume", type=["pdf", "docx"])
job_description = st.text_area("Paste Job Description", height=200)

if st.button("Check Eligibility"):
    if not resume_file or not job_description.strip():
        st.warning("Both fields are required.")
        st.stop()

    resume_text = extract_text_from_file(resume_file)

    with st.spinner("Analyzing eligibility..."):
        try:
            deduct_credits(user_id, 5)
            result = ai_eligibility_score(resume_text, job_description)

            st.metric("Eligibility Score", f"{result['score']}%")
            st.write("### Explanation")
            st.write(result["reason"])

        except Exception as e:
            st.error(f"Error: {e}")
