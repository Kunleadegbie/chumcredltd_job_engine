import os
import streamlit as st

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

st.write("BASE PATH:", BASE)

# Check what files really exist
st.write("ROOT CONTENTS:", os.listdir(BASE))

# Check if services folder exists at all
services_path = os.path.join(BASE, "services")
st.write("SERVICES FOLDER EXISTS:", os.path.isdir(services_path))

# If exists, list contents
if os.path.isdir(services_path):
    st.write("SERVICES CONTENTS:", os.listdir(services_path))
else:
    st.write("NO SERVICES FOLDER IN DEPLOYMENT")


import sys, os

# ----------------------------------------------------
# FORCE ADD PROJECT ROOT
# ----------------------------------------------------
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import streamlit as st
from services.utils import (
    get_subscription,
    auto_expire_subscription,
    deduct_credits,
)
from services.ai_engine import ai_generate_match_score
from components.sidebar import render_sidebar


COST = 5
st.set_page_config(page_title="Match Score | Chumcred", page_icon="📊")

# -------------------- AUTH CHECK --------------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state.get("user")
if not isinstance(user, dict):
    st.switch_page("app.py")

user_id = user["id"]

# Sidebar
render_sidebar()

# -------------------- SUBSCRIPTION --------------------
auto_expire_subscription(user)
subscription = get_subscription(user_id)

if not subscription or subscription.get("subscription_status") != "active":
    st.error("You need an active subscription to use Match Score.")
    st.stop()

credits = subscription.get("credits", 0)

# -------------------- PAGE UI --------------------
st.title("📊 Resume vs Job Match Score")
st.info(f"💳 Credits Available: **{credits}**")

resume_text = st.text_area("Paste your Resume Content")
job_description = st.text_area("Paste the Job Description")

if st.button(f"Run Match Score (Cost {COST} credits)", disabled=credits < COST):

    if not resume_text.strip() or not job_description.strip():
        st.warning("Please paste both resume and job description.")
        st.stop()

    ok, new_balance = deduct_credits(user_id, COST)
    if not ok:
        st.error(new_balance)
        st.stop()

    st.session_state.subscription = get_subscription(user_id)
    st.success(f"✔ {COST} credits deducted. New balance: {new_balance}")

    result = ai_generate_match_score(resume_text, job_description)
    st.write(result)
