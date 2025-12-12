import streamlit as st
import os, sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from components.sidebar import render_sidebar
from config.supabase_client import supabase
from services.utils import deduct_credits, get_subscription, auto_expire_subscription
from ai_engine import ai_extract_skills, extract_text_from_file


st.set_page_config(page_title="Skills Extractor", page_icon="🧠")

# AUTH CHECK
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

render_sidebar()

user = st.session_state["user"]
user_id = user["id"]

st.title("🧠 AI Skills Extraction Tool")
st.write("Upload your resume and let AI identify your professional skills.")

auto_expire_subscription(user_id)
subscription = get_subscription(user_id)

if not subscription or subscription["subscription_status"] != "active":
    st.error("Your subscription is not active.")
    st.stop()

if subscription["credits"] < 5:
    st.error("❌ Not enough credits. Skills Extraction requires **5 credits**.")
    st.stop()

resume_file = st.file_uploader("Upload Resume (PDF / DOCX)", type=["pdf", "docx"])

if st.button("Extract Skills"):
    if not resume_file:
        st.warning("Please upload a resume.")
        st.stop()

    resume_text = extract_text_from_file(resume_file)

    with st.spinner("Extracting skills..."):
        try:
            deduct_credits(user_id, 5)
            result = ai_extract_skills(resume_text)
            st.success("Skills extracted successfully!")

            st.subheader("Identified Skills")
            st.write(", ".join(result["skills"]))

        except Exception as e:
            st.error(f"Error: {e}")
