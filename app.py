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
# HIDE SIDEBAR COMPLETELY + FULL WIDTH  (✅ ONLY CHANGE MADE)
# ==========================================================
st.markdown(
    """
    <style>
        /* Hide the entire Streamlit sidebar */
        [data-testid="stSidebar"] { display: none !important; }
        [data-testid="stSidebarNav"] { display: none !important; }

        /* Expand main content to full width */
        .block-container {
            max-width: 100% !important;
            padding-left: 3rem !important;
            padding-right: 3rem !important;
            padding-top: 1.5rem !important;
        }
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
# TALENTIQ STORY (LANDING SECTION) — NO HTML, PREMIUM UI
# ==========================================================
st.markdown("## 🚀 Turn Potential Into Opportunity — Faster")
st.write(
    "TalentIQ is an AI-powered employability and talent-acceleration platform that helps you move from "
    "**“I’m looking for work”** to **“I’m job-ready and getting interviews.”**"
)

st.divider()

# Feature cards (single, non-duplicated)
st.markdown("### What TalentIQ does in simple terms")
f1, f2, f3 = st.columns(3)

with f1:
    st.success("⚡ CV Intelligence")
    st.write(
        "Upload your CV and get a clear employability score, strengths, gaps, ATS readiness, "
        "and improvements you can apply immediately."
    )

with f2:
    st.info("🎯 SmartMatch")
    st.write(
        "Get matched to relevant roles/internships and understand why you fit — "
        "plus what to improve to increase your match score."
    )

with f3:
    st.warning("🧠 InterviewIQ")
    st.write(
        "Practice interview questions for your role and receive structured feedback "
        "to improve clarity, confidence, and evidence."
    )

st.divider()

# Trusted banner
st.info(
    "✅ **Trusted by programmes & institutions** — TalentIQ is being adopted for employability readiness, "
    "internship support, and cohort reporting across training and placement initiatives."
)

# Who it's for
st.markdown("### Who it’s for")
a, b, c = st.columns(3)

with a:
    st.write("**🎓 Students & Graduates**")
    st.caption("Build strong profiles early, improve readiness, and position for internships and entry-level roles.")

with b:
    st.write("**💼 Job Seekers & Career Switchers**")
    st.caption("Improve how you present your experience, target the right roles, and practice interviews that feel real.")

with c:
    st.write("**🏛 Institutions & Programmes**")
    st.caption("Run cohorts with structured profiling, readiness insights, and reporting for monitoring and outcomes.")

st.divider()

# Why it matters
st.markdown("### Why it matters")
m1, m2, m3 = st.columns(3)

with m1:
    st.success("📌 Clear direction")
    st.caption("Stop guessing. See your real gaps and what to fix to move forward faster.")

with m2:
    st.info("⚡ Faster shortlisting")
    st.caption("Improve CV quality and alignment so you look stronger to recruiters and screening systems.")

with m3:
    st.warning("📊 Accountability & outcomes")
    st.caption("Programme owners get visibility: onboarding, readiness uplift, matching activity, and success stories.")

st.divider()

st.markdown("### ✅ Get started")
st.write("Sign in if you already have an account, or create a new account below in under a minute.")

# ✅ Tabs (must exist before use)
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