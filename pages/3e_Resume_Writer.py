import streamlit as st
import os, sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from components.sidebar import render_sidebar
from config.supabase_client import supabase
from services.utils import deduct_credits, get_subscription, auto_expire_subscription
from ai_engine import ai_rewrite_resume, extract_text_from_file


st.set_page_config(page_title="Resume Writer", page_icon="📄")

if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

render_sidebar()

user = st.session_state["user"]
user_id = user["id"]

st.title("📄 AI Resume Enhancer")

auto_expire_subscription(user_id)
subscription = get_subscription(user_id)

if not subscription or subscription["subscription_status"] != "active":
    st.error("Subscription required.")
    st.stop()

if subscription["credits"] < 15:
    st.error("❌ Not enough credits. Resume Rewrite requires **15 credits**.")
    st.stop()

resume_file = st.file_uploader("Upload Resume", type=["pdf", "docx"])

if st.button("Rewrite Resume"):
    if not resume_file:
        st.warning("Please upload your resume.")
        st.stop()

    resume_text = extract_text_from_file(resume_file)

    with st.spinner("Rewriting resume..."):
        try:
            deduct_credits(user_id, 15)
            result = ai_rewrite_resume(resume_text)

            st.success("Resume rewritten successfully!")
            st.write("### Your Improved Resume")
            st.write(result["content"])

        except Exception as e:
            st.error(f"Error: {e}")
