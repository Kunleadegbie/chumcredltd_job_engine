# ==========================================================
# app.py — AUTH ENTRY POINT (FINAL, NO RESET LOGIC)
# ==========================================================

import streamlit as st
import sys
import os
import textwrap

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

        /* Make landing feel premium */
        .block-container { max-width: 1100px; padding-top: 1.6rem; padding-bottom: 2.2rem; }

        /* Landing components */
        .ti-hero {
            border: 1px solid rgba(49, 51, 63, 0.10);
            border-radius: 24px;
            padding: 18px 18px;
            background: linear-gradient(135deg,
                rgba(56, 189, 248, 0.22),
                rgba(110, 231, 183, 0.16),
                rgba(250, 204, 21, 0.14)
            );
        }
        .ti-title {
            font-size: 2.2rem;
            font-weight: 900;
            letter-spacing: -0.02em;
            margin: 0;
        }
        .ti-subtitle {
            font-size: 1.05rem;
            margin-top: 8px;
            color: rgba(49, 51, 63, 0.78);
            line-height: 1.55rem;
        }
        .ti-badges { margin-top: 2px; }
        .ti-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 7px 12px;
            border-radius: 999px;
            border: 1px solid rgba(49, 51, 63, 0.12);
            background: rgba(255, 255, 255, 0.70);
            font-size: 0.86rem;
            font-weight: 750;
            margin-right: 8px;
            margin-bottom: 10px;
        }
        .ti-divider {
            height: 1px;
            background: rgba(49, 51, 63, 0.10);
            margin: 14px 0;
        }
        .ti-kpi {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
        }
        @media (max-width: 900px) {
            .ti-kpi { grid-template-columns: 1fr; }
        }
        .ti-card {
            border: 1px solid rgba(49, 51, 63, 0.12);
            border-radius: 16px;
            padding: 14px 14px;
            background: rgba(255, 255, 255, 0.62);
        }
        .ti-card b { font-size: 1.02rem; }
        .ti-card p {
            margin: 6px 0 0 0;
            color: rgba(49, 51, 63, 0.78);
            font-size: 0.95rem;
            line-height: 1.45rem;
        }

        .ti-section-title {
            font-size: 1.05rem;
            font-weight: 850;
            margin: 0 0 10px 0;
            letter-spacing: -0.01em;
        }

        .ti-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            margin-top: 10px;
        }
        @media (max-width: 900px) {
            .ti-grid { grid-template-columns: 1fr; }
        }

        .ti-trust {
            margin-top: 0.8rem;
            padding: 0.9rem 1rem;
            border: 1px solid rgba(49, 51, 63, 0.12);
            border-radius: 16px;
            background: rgba(49, 51, 63, 0.03);
        }
        .ti-trust b { font-weight: 850; }
        .ti-trust span { color: rgba(49, 51, 63, 0.78); }

        .ti-cta {
            margin-top: 0.9rem;
            padding: 0.85rem 1rem;
            border-radius: 16px;
            border: 1px solid rgba(49, 51, 63, 0.12);
            background: rgba(255,255,255,0.55);
            color: rgba(49, 51, 63, 0.80);
            font-size: 0.95rem;
        }
        .ti-cta b { color: rgba(49, 51, 63, 0.95); }

        /* Buttons feel premium */
        div.stButton > button {
            border-radius: 12px !important;
            padding: 0.7rem 1rem !important;
            font-weight: 750 !important;
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
# TALENTIQ STORY (LANDING SECTION) — REDESIGNED ONLY
# ==========================================================
st.markdown(
    textwrap.dedent("""
    <div class="ti-hero">
        <div class="ti-badges">
            <span class="ti-badge">⚡ CV Intelligence</span>
            <span class="ti-badge">🎯 SmartMatch</span>
            <span class="ti-badge">🧠 InterviewIQ</span>
        </div>

        <h1 class="ti-title">Turn Potential Into Opportunity — Faster</h1>

        <div class="ti-subtitle">
            <b>Chumcred TalentIQ</b> helps you move from <b>“I’m looking for work”</b> to <b>“I’m job-ready and getting interviews.”</b>
            Get clarity on your CV, get matched to relevant roles, and practice interviews with feedback — all in one place.
        </div>

        <div class="ti-divider"></div>

        <div class="ti-section-title">What TalentIQ does in simple terms</div>

        <div class="ti-kpi">
            <div class="ti-card">
                <b>✅ CV Intelligence</b>
                <p>Upload your CV and get a clear employability score, strengths, gaps, ATS readiness, and improvements you can apply immediately.</p>
            </div>

            <div class="ti-card">
                <b>🎯 SmartMatch</b>
                <p>Get matched to relevant roles/internships and see why you fit — plus what to improve to increase your match score.</p>
            </div>

            <div class="ti-card">
                <b>🧠 InterviewIQ</b>
                <p>Practice interview questions for your role and receive structured feedback to improve clarity, confidence, and evidence.</p>
            </div>
        </div>
    </div>
    """),
    unsafe_allow_html=True
)

# Trusted banner (kept, styled nicer)
st.markdown(
    textwrap.dedent("""
    <div class="ti-trust">
        <b>Trusted by programmes & institutions</b>
        <span> — TalentIQ is being adopted for employability readiness, internship support, and cohort reporting across training and placement initiatives.</span>
    </div>
    """),
    unsafe_allow_html=True
)

st.markdown("<div class='ti-divider'></div>", unsafe_allow_html=True)

# Who it's for (cards instead of bullets)
st.markdown(
    textwrap.dedent("""
    <div class="ti-section-title">Who it’s for</div>
    <div class="ti-grid">
        <div class="ti-card">
            <b>🎓 Students & Graduates</b>
            <p>Build strong profiles early, improve readiness, and position for internships and entry-level opportunities.</p>
        </div>
        <div class="ti-card">
            <b>💼 Job Seekers & Career Switchers</b>
            <p>Improve how you present your experience, target the right roles, and practice interviews that feel real.</p>
        </div>
        <div class="ti-card">
            <b>🏛 Institutions & Programmes</b>
            <p>Run cohorts with structured profiling, readiness insights, and reporting for monitoring and outcomes.</p>
        </div>
    </div>
    """),
    unsafe_allow_html=True
)

# Why it matters (colorful benefit cards)
st.markdown(
    textwrap.dedent("""
    <div style="margin-top: 12px;">
        <div class="ti-section-title">Why it matters</div>
        <div class="ti-grid">
            <div class="ti-card">
                <b>📌 Clear direction</b>
                <p>Stop guessing. See your real gaps and what to fix to move forward quickly.</p>
            </div>
            <div class="ti-card">
                <b>⚡ Faster shortlisting</b>
                <p>Improve CV quality and alignment so you look stronger to recruiters and screening systems.</p>
            </div>
            <div class="ti-card">
                <b>📊 Accountability & outcomes</b>
                <p>Programme owners get visibility: onboarding, readiness uplift, matching activity, and success stories.</p>
            </div>
        </div>
    </div>
    """),
    unsafe_allow_html=True
)

# Anchor + CTA before tabs
st.markdown('<div id="auth-section"></div>', unsafe_allow_html=True)

st.markdown(
    textwrap.dedent("""
    <div class="ti-cta">
        <b>Get started below</b> — sign in if you already have an account, or create a new one in under a minute.
    </div>
    """),
    unsafe_allow_html=True
)

# Existing mini highlight cards (kept; not required but okay)
colA, colB, colC = st.columns([1, 1, 1])
with colA:
    st.success("✅ CV Quality + ATS Readiness")
with colB:
    st.info("🎯 Matching + Shortlisting Support")
with colC:
    st.warning("🧠 Interview Practice + Scoring")


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