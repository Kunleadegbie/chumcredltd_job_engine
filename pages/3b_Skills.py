import streamlit as st
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.auth import require_login
from services.utils import get_subscription, auto_expire_subscription, deduct_credits
from services.ai_engine import ai_extract_skills


st.set_page_config(page_title="Skills Extraction", page_icon="🧠", layout="wide")

user = require_login()
user_id = user["id"]

auto_expire_subscription(user_id)
subscription = get_subscription(user_id)

if not subscription or subscription["subscription_status"] != "active":
    st.error("You must have an active subscription to extract skills.")
    st.stop()

if subscription["credits"] < 5:
    st.error("You do not have enough AI credits. Please upgrade.")
    st.stop()

st.title("🧠 AI Skills Extraction")
st.write("Upload your resume to extract key skills.")

resume = st.file_uploader("Upload Resume", type=["pdf", "docx"])

if st.button("Extract Skills"):
    if not resume:
        st.error("Upload a resume first.")
        st.stop()

    resume_bytes = resume.read()

    with st.spinner("Extracting skills..."):
        success, msg = deduct_credits(user_id, 5)
        if not success:
            st.error(msg)
            st.stop()

        try:
            skills = ai_extract_skills(resume_bytes)
            st.success("Skills Extracted!")
            st.write("### Top Skills")
            st.write(skills)

        except Exception as e:
            st.error(f"Error: {e}")
