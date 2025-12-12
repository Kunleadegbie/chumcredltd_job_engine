import streamlit as st
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.auth import require_login
from services.utils import get_subscription, auto_expire_subscription, deduct_credits
from services.ai_engine import ai_cover_letter


st.set_page_config(page_title="Cover Letter", page_icon="✍️", layout="wide")

user = require_login()
user_id = user["id"]

auto_expire_subscription(user_id)
subscription = get_subscription(user_id)

if not subscription or subscription["subscription_status"] != "active":
    st.error("Active subscription required.")
    st.stop()

if subscription["credits"] < 10:
    st.error("Insufficient credits — Cover Letter requires 10 credits.")
    st.stop()

st.title("✍️ AI Cover Letter Generator")
st.write("Provide job details to generate a tailored cover letter.")

job_title = st.text_input("Job Title")
company = st.text_input("Company Name")
job_description = st.text_area("Job Description")

if st.button("Generate Cover Letter"):
    if not job_title.strip() or not company.strip() or not job_description.strip():
        st.error("All fields are required.")
        st.stop()

    with st.spinner("Generating cover letter..."):
        success, msg = deduct_credits(user_id, 10)
        if not success:
            st.error(msg)
            st.stop()

        try:
            letter = ai_cover_letter(job_title, company, job_description)
            st.success("Cover Letter Ready!")
            st.write(letter)

        except Exception as e:
            st.error(f"Error: {e}")
