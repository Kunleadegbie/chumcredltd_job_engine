import sys, os
import streamlit as st

# ---------------------------
# FIX IMPORT PATHS FOR STREAMLIT CLOUD
# ---------------------------
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.sidebar import render_sidebar
from services.utils import (
    get_subscription,
    auto_expire_subscription,
    deduct_credits
)
from services.ai_engine import (
    ai_generate_match_score,       # only needed in Match Score
    ai_extract_skills,            # only needed in Skills
    ai_generate_cover_letter,     # only needed in Cover Letter
    ai_check_eligibility,         # only needed in Eligibility
    ai_generate_resume            # only needed in Resume Writer
)

COST = 5

st.set_page_config(page_title="Skills Extractor | Chumcred", page_icon="🧠")

# AUTH CHECK
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state.get("user")
if not isinstance(user, dict):
    st.switch_page("app.py")

user_id = user["id"]

render_sidebar()

auto_expire_subscription(user)
subscription = get_subscription(user_id)

if not subscription or subscription.get("subscription_status") != "active":
    st.error("Your subscription is inactive.")
    st.stop()

credits = subscription.get("credits", 0)

st.title("🧠 AI Skills Extraction")
st.info(f"💳 Credits Available: **{credits}**")

resume_text = st.text_area("Paste your Resume to extract skills")

if st.button(f"Extract Skills (Cost {COST} credits)", disabled=credits < COST):

    if not resume_text.strip():
        st.warning("Please paste your resume text.")
        st.stop()

    ok, new_credits = deduct_credits(user_id, COST)
    if not ok:
        st.error(new_credits)
        st.stop()

    st.session_state.subscription = get_subscription(user_id)

    st.success(f"{COST} credits deducted. Remaining: {new_credits}")

    result = ai_extract_skills(resume_text)
    st.write(result)
