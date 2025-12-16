# ================================================================
# 3e_Resume_Writer.py — Persistent AI Resume Writer
# ================================================================

import streamlit as st
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.ai_engine import ai_generate_resume_rewrite
from services.utils import get_subscription, auto_expire_subscription, deduct_credits
from config.supabase_client import supabase

st.set_page_config(page_title="AI Resume Writer", page_icon="📝")

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

CREDIT_COST = 15
TOOL = "resume_writer"

# ---------------- LOAD LAST OUTPUT ----------------
saved = (
    supabase.table("ai_outputs")
    .select("*")
    .eq("user_id", user_id)
    .eq("tool", TOOL)
    .order("created_at", desc=True)
    .limit(1)
    .execute()
    .data
)

if saved:
    st.info("📌 Your last generated resume")
    st.write(saved[0]["output"])

# ---------------- UI ----------------
st.title("📝 AI Resume Writer")
resume_text = st.text_area("Paste Resume", height=300)

if st.button("Rewrite Resume"):

    if not resume_text.strip():
        st.warning("Resume required.")
        st.stop()

    ok, msg = deduct_credits(user_id, CREDIT_COST)
    if not ok:
        st.error(msg)
        st.stop()

    with st.spinner("Rewriting resume..."):
        output = ai_generate_resume_rewrite(resume_text=resume_text)

        supabase.table("ai_outputs").insert({
            "user_id": user_id,
            "tool": TOOL,
            "input": {"resume_text": resume_text[:200]},
            "output": output,
            "credits_used": CREDIT_COST,
        }).execute()

        st.success("Resume generated!")
        st.write(output)

st.caption("Chumcred Job Engine © 2025")
