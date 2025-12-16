
# ============================
# 3c_Cover_Letter.py — Persistent
# ============================

import streamlit as st
from services.ai_engine import ai_generate_cover_letter
from services.utils import get_subscription, deduct_credits
from config.supabase_client import supabase

st.set_page_config(page_title="AI Cover Letter", page_icon="✉️")

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

CREDIT_COST = 10
TOOL = "cover_letter"

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
    st.info("📌 Your last Cover Letter")
    st.write(saved[0]["output"])

# ---------------- UI ----------------
st.title("✉️ AI Cover Letter Generator")

resume_text = st.text_area("Paste Resume", height=220)
job_description = st.text_area("Paste Job Description", height=220)

if st.button("Generate Cover Letter"):
    if not resume_text.strip() or not job_description.strip():
        st.warning("Both fields required.")
        st.stop()

    ok, msg = deduct_credits(user_id, CREDIT_COST)
    if not ok:
        st.error(msg)
        st.stop()

    output = ai_generate_cover_letter(
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

    st.success("Cover letter generated!")
    st.write(output)

st.caption("Chumcred Job Engine © 2025")
