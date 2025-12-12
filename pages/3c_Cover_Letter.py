import streamlit as st
import os, sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from components.sidebar import render_sidebar
from config.supabase_client import supabase
from services.utils import deduct_credits, get_subscription, auto_expire_subscription
from ai_engine import ai_cover_letter, extract_text_from_file


st.set_page_config(page_title="Cover Letter Generator", page_icon="✍️")

# AUTH
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

render_sidebar()

user = st.session_state["user"]
user_id = user["id"]

st.title("✍️ AI Cover Letter Generator")

auto_expire_subscription(user_id)
subscription = get_subscription(user_id)

if not subscription or subscription["subscription_status"] != "active":
    st.error("Your subscription is not active.")
    st.stop()

if subscription["credits"] < 10:
    st.error("❌ Not enough credits. Cover Letter requires **10 credits**.")
    st.stop()

resume_file = st.file_uploader("Upload Your Resume", type=["pdf", "docx"])
job_title = st.text_input("Job Title")
job_description = st.text_area("Job Description", height=200)

if st.button("Generate Cover Letter"):
    if not resume_file or not job_title or not job_description.strip():
        st.warning("All fields are required.")
        st.stop()

    resume_text = extract_text_from_file(resume_file)

    with st.spinner("Generating cover letter..."):
        try:
            deduct_credits(user_id, 10)
            result = ai_cover_letter(resume_text, job_title, job_description)

            st.success("Cover Letter Generated!")
            st.write("### Your Cover Letter:")
            st.write(result["content"])

        except Exception as e:
            st.error(f"Error: {e}")
