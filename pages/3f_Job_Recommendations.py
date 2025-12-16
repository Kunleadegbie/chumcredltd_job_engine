
# ============================
# 3f_Job_Recommendations.py — Persistent
# ============================

import streamlit as st
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.ai_engine import ai_generate_job_recommendations
from services.utils import get_subscription, deduct_credits
from config.supabase_client import supabase

st.set_page_config(page_title="AI Job Recommendations", page_icon="🧠")

# ---------------- AUTH ----------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state.get("user")
user_id = user["id"]

# ---------------- SUBSCRIPTION ----------------
subscription = get_subscription(user_id)
if not subscription or subscription.get("subscription_status") != "active":
    st.error("Active subscription required.")
    st.stop()

CREDIT_COST = 5
TOOL = "job_recommendations"

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
    st.info("📌 Your last Job Recommendations")
    st.markdown(saved[0]["output"])

# ---------------- UI ----------------
st.title("🧠 AI Job Recommendations")

resume_text = st.text_area("Paste Resume", height=220)
career_goal = st.text_input("Career Target (Optional)")

if st.button("Generate Recommendations"):
    if not resume_text.strip():
        st.warning("Resume required.")
        st.stop()

    ok, msg = deduct_credits(user_id, CREDIT_COST)
    if not ok:
        st.error(msg)
        st.stop()

    output = ai_generate_job_recommendations(
        resume_text=resume_text,
        career_goal=career_goal
    )

    supabase.table("ai_outputs").insert({
        "user_id": user_id,
        "tool": TOOL,
        "input": {"career_goal": career_goal},
        "output": output,
        "credits_used": CREDIT_COST
    }).execute()

    st.success("Recommendations generated!")
    st.markdown(output)

st.caption("Chumcred Job Engine © 2025")
