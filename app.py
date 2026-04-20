# ==========================================================
# app.py — AUTH ENTRY POINT (FINAL, NO RESET LOGIC)
# ==========================================================

import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(__file__))

from services.auth import login_user, register_user
from config.supabase_client import supabase


# ==========================================================
# PAGE CONFIG (MUST BE FIRST)
# ==========================================================
st.set_page_config(
    page_title="Chumcred TalentIQ",
    page_icon="assets/talentiq_logo.png",
    layout="wide",
)


# ==========================================================
# HIDE DEFAULT NAV
# ==========================================================
st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"] { display: none; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ==========================================================
# SESSION DEFAULTS
# ==========================================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "user" not in st.session_state:
    st.session_state.user = None


# ==========================================================
# REDIRECT IF AUTHENTICATED
# ==========================================================
if st.session_state.authenticated and st.session_state.user:
    st.switch_page("pages/2_Dashboard.py")
    st.stop()


# ==========================================================
# AUTH UI
# ==========================================================
st.image("assets/talentiq_logo.png", width=280)
st.title("🔐 Welcome to Chumcred TalentIQ")
st.caption("AI-powered tools for job seekers, career growth, and talent acceleration.")


# ==========================================================
# TALENTIQ STORY (LANDING SECTION)
# ==========================================================
st.markdown("""
### 🚀 Turn Potential Into Opportunity — Faster
**Chumcred TalentIQ** is an AI-powered employability and talent-acceleration platform that helps people move from **“I’m looking for work”** to **“I’m job-ready and getting interviews.”**

**What TalentIQ does in simple terms**
- **CV Intelligence:** Upload your CV and get a clear employability score, strengths, gaps, and improvements.
- **SmartMatch:** Get matched to relevant roles/internships and understand why you fit (or what to improve).
- **InterviewIQ:** Practice interview questions for your role and get structured feedback to improve fast.

**Who it’s for**
- Students, graduates, and early-career professionals
- Career switchers and job seekers
- Institutions and programmes running employability or internship cohorts

**Why it matters**
- Reduces guesswork and improves the quality of applications
- Helps candidates present real evidence and measurable achievements
- Gives programme owners visibility: onboarding, readiness uplift, and outcomes
""")

# ✅ Trusted banner (separate block — correct placement)
st.markdown("""
<div style="
    margin-top: 0.6rem;
    padding: 0.7rem 0.9rem;
    border: 1px solid rgba(49, 51, 63, 0.12);
    border-radius: 12px;
    background: rgba(49, 51, 63, 0.03);
">
<b>Trusted by programmes & institutions</b> — TalentIQ is being adopted for employability readiness, internship support, and cohort reporting across training and placement initiatives.
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div id="auth-section"></div>
""")

colA, colB, colC = st.columns([1, 1, 1])
with colA:
    st.success("✅ CV Quality + ATS Readiness")
with colB:
    st.info("🎯 Matching + Shortlisting Support")
with colC:
    st.warning("🧠 Interview Practice + Scoring")

st.markdown("""
**Get started below** — sign in if you already have an account, or create a new one in under a minute.
""")


tab_login, tab_register = st.tabs(["🔓 Sign In", "📝 Register"])


# ==========================================================
# LOGIN TAB
# ==========================================================
with tab_login:
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Sign In"):
        result = login_user(email, password)

        user = None
        if isinstance(result, dict):
            user = result
        elif isinstance(result, tuple):
            user = next((r for r in result if isinstance(r, dict)), None)

        if not user:
            st.error("Invalid email or password.")
            st.stop()

        try:
            supabase.auth.sign_in_with_password({"email": email, "password": password})
        except Exception:
            pass

        auth_session = supabase.auth.get_session()

        if not auth_session:
            st.error("Unable to create authentication session.")
            st.stop()

        st.session_state.authenticated = True
        st.session_state.user = user

        st.success("Login successful. Redirecting...")
        st.switch_page("pages/2_Dashboard.py")


# ==========================================================
# REGISTER TAB
# ==========================================================
with tab_register:
    full_name = st.text_input("Full Name", key="reg_full_name")
    reg_email = st.text_input("Email", key="reg_email")
    reg_password = st.text_input("Password", type="password", key="reg_password")

    if st.button("Create Account"):
        if not full_name or not reg_email or not reg_password:
            st.warning("Please complete all fields.")
            st.stop()

        result = register_user(full_name, reg_email, reg_password)

        if isinstance(result, dict) and result.get("error"):
            st.error(result["error"])
            st.stop()

        st.success("Account created successfully! Please check your email to confirm your account before logging in.")
        st.info("After confirmation, return to the Sign In tab to login.")


# ==========================================================
# FOOTER
# ==========================================================
st.markdown("---")
st.caption("Chumcred TalentIQ © 2026 — AI-powered career intelligence.")