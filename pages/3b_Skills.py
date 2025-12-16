
# ============================
# 3b_Skills.py — Persistent
# ============================

import streamlit as st
import os, sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.ai_engine import ai_extract_skills
from services.utils import get_subscription, auto_expire_subscription, deduct_credits
from config.supabase_client import supabase

st.set_page_config(page_title="Skills Extraction", page_icon="🧠")

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
TOOL = "skills_extraction"

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
    st.info("📌 Your last Skills Extraction")
    st.write(saved[0]["output"])

# ---------------- UI ----------------
st.title("🧠 AI Skills Extraction")

resume_file = st.file_uploader("Upload Resume (PDF/DOCX)", type=["pdf", "docx"])
resume_text = st.text_area("Or Paste Resume Text", height=260)

if st.button("Extract Skills"):
    if not resume_file and not resume_text.strip():
        st.warning("Provide resume input.")
        st.stop()

    ok, msg = deduct_credits(user_id, CREDIT_COST)
    if not ok:
        st.error(msg)
        st.stop()

    content = resume_file.read() if resume_file else resume_text

    output = ai_extract_skills(resume_text=content)

    supabase.table("ai_outputs").insert({
        "user_id": user_id,
        "tool": TOOL,
        "input": {"resume_preview": str(content)[:200]},
        "output": output,
        "credits_used": CREDIT_COST
    }).execute()

    st.success("Skills extracted!")
    st.write(output)

st.caption("Chumcred Job Engine © 2025")
