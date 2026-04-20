# ==========================================================
# app.py — AUTH ENTRY POINT (BEAUTIFIED LANDING + SAME AUTH)
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

        /* Make the page feel cleaner */
        .block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1100px; }
        h1, h2, h3 { letter-spacing: -0.02em; }

        /* Button styling (Streamlit default buttons) */
        div.stButton > button {
            border-radius: 12px !important;
            padding: 0.7rem 1rem !important;
            font-weight: 700 !important;
        }

        /* Reduce spacing above tabs a bit */
        .stTabs [data-baseweb="tab-list"] { margin-top: 0.5rem; }

        /* Soft cards look */
        .ti-card {
            border: 1px solid rgba(49, 51, 63, 0.12);
            border-radius: 16px;
            padding: 14px 14px;
            background: rgba(49, 51, 63, 0.03);
        }
        .ti-hero {
            border: 1px solid rgba(49, 51, 63, 0.12);
            border-radius: 20px;
            padding: 18px 18px;
            background: linear-gradient(135deg, rgba(53, 153, 255, 0.12), rgba(110, 231, 183, 0.10), rgba(250, 204, 21, 0.08));
        }
        .ti-badge {
            display: inline-block;
            padding: 6px 10px;
            border-radius: 999px;
            border: 1px solid rgba(49, 51, 63, 0.12);
            background: rgba(255,255,255,0.55);
            font-size: 0.85rem;
            font-weight: 600;
            margin-right: 8px;
            margin-bottom: 8px;
        }
        .ti-muted { color: rgba(49, 51, 63, 0.75); }
        .ti-small { font-size: 0.95rem; line-height: 1.45rem; }
        .ti-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
        @media (max-width: 900px) {
            .ti-grid { grid-template-columns: 1fr; }
        }
        .ti-title { font-size: 2rem; font-weight: 800; margin: 0; }
        .ti-subtitle { font-size: 1.05rem; margin-top: 8px; }
        .ti-divider { height: 1px; background: rgba(49, 51, 63, 0.10); margin: 14px 0; }
        .ti-kpi { display:flex; gap:10px; flex-wrap: wrap; }
        .ti-kpi > div { flex: 1; min-width: 200px; }
        .ti-kpi .ti-card { height: 100%; }

        /* Make tables/captions nicer */
        .stCaption { margin-top: 0.2rem; }
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
# HEADER
# ==========================================================
st.image("assets/talentiq_logo.png", width=260)

# ==========================================================
# BEAUTIFIED LANDING / STORY SECTION (ONLY)
# ==========================================================
st.markdown(
    """
    <div class="ti-hero">
        <div>
            <span class="ti-badge">⚡ CV Intelligence</span>
            <span class="ti-badge">🎯 SmartMatch</span>
            <span class="ti-badge">🧠 InterviewIQ</span>
        </div>

        <h1 class="ti-title">Turn Potential Into Opportunity — Faster</h1>
        <div class="ti-subtitle ti-muted">
            TalentIQ helps people move from <b>“I’m searching”</b> to <b>“I’m job-ready and getting interviews”</b> — with clear scoring,
            guided improvements, and role-fit matching.
        </div>

        <div class="ti-divider"></div>

        <div class="ti-kpi">
            <div class="ti-card">
                <b>✅ Know your employability score</b><br/>
                <span class="ti-muted ti-small">Upload a CV → see strengths, gaps, ATS readiness, and how to improve.</span>
            </div>
            <div class="ti-card">
                <b>🎯 Get matched to relevant roles</b><br/>
                <span class="ti-muted ti-small">SmartMatch ranks fit and shows what to fix to increase your chances.</span>
            </div>
            <div class="ti-card">
                <b>🧠 Practice interviews confidently</b><br/>
                <span class="ti-muted ti-small">InterviewIQ generates questions and gives structured feedback.</span>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Social proof / trusted banner
st.markdown(
    """
    <div style="
        margin-top: 0.75rem;
        padding: 0.85rem 1rem;
        border: 1px solid rgba(49, 51, 63, 0.12);
        border-radius: 16px;
        background: rgba(49, 51, 63, 0.03);
    ">
        <b>Trusted by programmes & institutions</b>
        <span class="ti-muted"> — TalentIQ is being adopted for employability readiness, internship support, and cohort reporting across training and placement initiatives.</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# Who it's for + how it works cards
st.markdown("<div class='ti-divider'></div>", unsafe_allow_html=True)

st.markdown(
    """
    <div class="ti-grid">
        <div class="ti-card">
            <b>👤 For Job Seekers</b><br/>
            <span class="ti-muted ti-small">
                Improve CV quality, raise ATS readiness, match to roles, and practice interviews — all in one place.
            </span>
        </div>
        <div class="ti-card">
            <b>🏫 For Institutions</b><br/>
            <span class="ti-muted ti-small">
                Cohort onboarding, readiness distribution, matching insights, and reporting for internship/placement programmes.
            </span>
        </div>
        <div class="ti-card">
            <b>🏢 For Employers</b><br/>
            <span class="ti-muted ti-small">
                Faster shortlisting with structured profiles and fit scoring (where postings and workflows are enabled).
            </span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# CTA helper text
st.markdown(
    """
    <div style="margin-top: 0.9rem;" class="ti-muted ti-small">
        Ready to begin? <b>Sign in</b> if you already have an account, or <b>create a new account</b> below in under a minute.
    </div>
    <div id="auth-section"></div>
    """,
    unsafe_allow_html=True,
)

# ==========================================================
# AUTH TABS (UNCHANGED)
# ==========================================================
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