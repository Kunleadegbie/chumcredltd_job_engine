import sys, os
import streamlit as st

# ----------------------------------------------------
# FIX IMPORT PATHS (Required for Streamlit Cloud)
# ----------------------------------------------------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ----------------------------------------------------
# SAFE IMPORTS
# ----------------------------------------------------
from components.sidebar import render_sidebar
from services.utils import (
    get_subscription,
    auto_expire_subscription,
    deduct_credits
)
from services.ai_engine import ai_extract_skills


# ----------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------
st.set_page_config(page_title="Skills Extractor | Chumcred", page_icon="🧠")

COST = 5


# ----------------------------------------------------
# AUTH CHECK
# ----------------------------------------------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state.get("user")
if not isinstance(user, dict):
    st.switch_page("app.py")

user_id = user["id"]


# ----------------------------------------------------
# SIDEBAR
# ----------------------------------------------------
render_sidebar()


# ----------------------------------------------------
# SUBSCRIPTION CHECK
# ----------------------------------------------------
auto_expire_subscription(user)
subscription = get_subscription(user_id)

if not subscription or subscription.get("subscription_status") != "active":
    st.error("❌ You need an active subscription to extract skills.")
    st.stop()

credits = subscription.get("credits", 0)


# ----------------------------------------------------
# PAGE UI
# ----------------------------------------------------
st.title("🧠 AI Skills Extractor")
st.info(f"💳 Credits Available: **{credits}**")

resume_text = st.text_area("Paste your resume here to extract skills")


if st.button(f"Extract Skills (Cost {COST} credits)", disabled=credits < COST):

    if not resume_text.strip():
        st.warning("Please paste your resume first.")
        st.stop()

    ok, new_balance = deduct_credits(user_id, COST)
    if not ok:
        st.error(new_balance)
        st.stop()

    st.success(f"✔ {COST} credits deducted. New balance: {new_balance}")
    st.write("---")

    st.write("⏳ Extracting skills...")

    result = ai_extract_skills(resume_text)
    st.write(result)
