
# ============================
# 3d_Eligibility.py — Persistent
# ============================

import streamlit as st
import os, sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.ai_engine import ai_check_eligibility
from services.utils import get_subscription, auto_expire_subscription, deduct_credits
from config.supabase_client import supabase

# ======================================================
# HIDE STREAMLIT SIDEBAR
# ======================================================
from components.ui import hide_streamlit_sidebar
from components.sidebar import render_sidebar

# Hide Streamlit default navigation
hide_streamlit_sidebar()

st.session_state["_sidebar_rendered"] = False


# Auth check
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")
    st.stop()

# Render custom sidebar
render_sidebar()


st.set_page_config(page_title="Eligibility Checker", page_icon="✔️")

# ---------------- AUTH ----------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state.get("user")
user_id = user["id"]

# ---------------- SUBSCRIPTION ----------------
auto_expire_subscription(user_id)
subscription = get_subscription(user_id)

if not subscription or subscription.get("subscription_status") != "active":
    st.error("Active subscription required.")
    st.stop()

CREDIT_COST = 5
TOOL = "eligibility"

# ---------------- LOAD LAST OUTPUT ----------------
saved = (
    supabase.table("ai_outputs")
    .select("*")
    .eq("user_id", user_id)
    .eq("tool", TOOL)
    .order("created_at", desc=True)
    .limit(1)
    .execute()
).data

if saved:
    st.info("📌 Your last Eligibility Result")
    st.write(saved[0]["output"])

# ---------------- UI ----------------
st.title("✔️ AI Job Eligibility Checker")

resume_text = st.text_area("Paste Resume", height=240)
job_description = st.text_area("Paste Job Description", height=240)

if st.button("Check Eligibility"):
    if not resume_text.strip() or not job_description.strip():
        st.warning("Both fields required.")
        st.stop()

    ok, msg = deduct_credits(user_id, CREDIT_COST)
    if not ok:
        st.error(msg)
        st.stop()

    output = ai_check_eligibility(
        resume_text=resume_text,
        job_description=job_description
    )

    supabase.table("ai_outputs").insert({
        "user_id": user_id,
        "tool": TOOL,
        "input": {"job_description": job_description[:200]},
        "output": output,
        "credits_used": CREDIT_COST
    }).execute()

    st.success("Eligibility check complete!")
    st.write(output)

st.caption("Chumcred TalentIQ © 2025")
