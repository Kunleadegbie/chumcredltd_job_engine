import streamlit as st
import sys, os
from datetime import datetime

# Ensure proper import paths
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from components.sidebar import render_sidebar
from config.supabase_client import supabase
from services.utils import get_subscription


# ------------------------------
# PAGE CONFIG
# ------------------------------
st.set_page_config(page_title="Dashboard", page_icon="🏠", layout="wide")

# ------------------------------
# AUTH CHECK
# ------------------------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state["user"]
user_id = user["id"]

render_sidebar()

st.title("🏠 Your Dashboard")
st.write("---")

# ------------------------------
# FETCH SUBSCRIPTION
# ------------------------------
subscription = get_subscription(user_id)

if not subscription:
    credits = 0
    plan = "No active plan"
    end_date = "N/A"
else:
    credits = subscription.get("credits", 0)
    plan = subscription.get("plan", "Unknown")
    end_date = subscription.get("end_date")
    if end_date:
        try:
            end_date = datetime.fromisoformat(end_date).strftime("%B %d, %Y")
        except:
            pass


# ------------------------------
# LAYOUT (LinkedIn/Indeed Style)
# ------------------------------
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown(
        """
        ### 👋 Welcome back!
        Your AI-powered job search and career toolkit is ready.
        
        Below is a summary of your current plan and usage.
        """
    )

    st.markdown("### 📦 Subscription Summary")

    st.markdown(
        f"""
        <div style="padding:15px;border-radius:10px;border:1px solid #ddd;background:#f8faff;">
            <b>Plan:</b> {plan}<br>
            <b>Credits Remaining:</b> {credits}<br>
            <b>Expiry Date:</b> {end_date}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    st.markdown("### 💳 How to Pay (Bank Transfer)")
    st.info(
        """
        **Account Name:** Chumcred Limited  
        **Bank:** Sterling Bank Plc  
        **Account Number:** 0087611334  

        After payment, kindly notify support for activation.
        """
    )

with col2:
    st.markdown("### ⚙️ Quick Actions")

    st.button("🔍 Job Search", on_click=lambda: st.switch_page("pages/3_Job_Search.py"))
    st.button("📊 Match Score", on_click=lambda: st.switch_page("pages/3a_Match_Score.py"))
    st.button("🧠 Skills Extractor", on_click=lambda: st.switch_page("pages/3b_Skills.py"))
    st.button("📝 Cover Letter Generator", on_click=lambda: st.switch_page("pages/3c_Cover_Letter.py"))
    st.button("📄 Resume Rewrite", on_click=lambda: st.switch_page("pages/3e_Resume_Writer.py"))
    st.button("🎯 Job Recommendations", on_click=lambda: st.switch_page("pages/3f_Job_Recommendations.py"))

st.write("---")

st.markdown(
    """
    ### ❓ About This App
    Chumcred Job Engine uses advanced AI to help you:
    - Generate professional resumes and cover letters  
    - Score match between your resume and job postings  
    - Discover targeted job opportunities  
    - Make smarter career decisions  

    Powered by AI. Built for Nigerian professionals.  
    """
)

# -------------------------------------------------------
# FOOTER
# -------------------------------------------------------
st.caption("Chumcred Job Engine © 2025 — Powered by Chumcred Limited")
