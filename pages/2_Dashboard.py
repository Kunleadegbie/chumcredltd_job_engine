# ==============================================================
# Dashboard.py — Fully Redesigned Professional Dashboard
# ==============================================================

import streamlit as st
import os, sys
from datetime import datetime

# Fix paths
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from services.auth import require_login
from config.supabase_client import supabase
from services.utils import (
    get_subscription,
    auto_expire_subscription,
    is_low_credit,
    deduct_credits,
)

# ------------------------------------
# PAGE SETTINGS
# ------------------------------------
st.set_page_config(
    page_title="Dashboard",
    page_icon="🏠",
    layout="wide"
)

user = require_login()
user_id = user["id"]

# ------------------------------------
# FETCH SUBSCRIPTION
# ------------------------------------
auto_expire_subscription(user_id)
sub = get_subscription(user_id)

credits = sub.get("credits", 0) if sub else 0
status = sub.get("subscription_status", "inactive") if sub else "inactive"

start_date = sub.get("start_date")
end_date = sub.get("end_date")

try:
    if end_date:
        end_date_fmt = datetime.fromisoformat(end_date).strftime("%d %b %Y")
    else:
        end_date_fmt = "Not available"
except:
    end_date_fmt = "Not available"

# ------------------------------------
# HEADER
# ------------------------------------
st.title("🏠 Welcome to Chumcred Job Engine")
st.write("Your all-in-one AI-powered career advancement platform.")

# ------------------------------------
# TOP SUMMARY CARDS
# ------------------------------------
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div style="
        background:#f0f6ff; padding:20px; border-radius:12px;
        border-left:5px solid #1a73e8;">
        <h4>Subscription Status</h4>
    """, unsafe_allow_html=True)

    if status == "active":
        st.success("**ACTIVE**")
    else:
        st.error("**NOT ACTIVE**")

    st.write(f"**Plan:** {sub.get('plan', 'None')}")
    st.write(f"**Expires:** {end_date_fmt}")
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style="
        background:#fff7e6; padding:20px; border-radius:12px;
        border-left:5px solid #ffa000;">
        <h4>Credits</h4>
    """, unsafe_allow_html=True)

    st.write(f"**Credits Remaining:** {credits}")
    if is_low_credit(user_id):
        st.warning("⚠️ Low credits — please top up soon.")
    st.markdown("</div>", unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div style="
        background:#e8fff1; padding:20px; border-radius:12px;
        border-left:5px solid #00a152;">
        <h4>Billing Info</h4>
    """, unsafe_allow_html=True)

    st.write("**Account Name:** Chumcred Limited")
    st.write("**Bank:** Sterling Bank Plc")
    st.write("**Account Number:** 0087611334")
    st.info("Make payment and contact support for activation.")
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")

# ------------------------------------
# HOW TO USE THE APP (USER GUIDE)
# ------------------------------------
st.subheader("🚀 How to Use This App (Step-by-Step Guide)")

st.markdown("""
### 1️⃣ **Subscribe to a Plan**
Activate a subscription and unlock AI credits.

### 2️⃣ **Use Any AI Feature**
Each tool deducts credits:
- Match Score — 5 credits  
- Skill Extraction — 5 credits  
- Cover Letter — 10 credits  
- Resume Rewrite — 15 credits  
- Job Recommendations — 5 credits  
- Job Search — 3 credits  

### 3️⃣ **Your Subscription Automatically Tracks Usage**
Credits update after every action.

### 4️⃣ **Manage Your Saved Jobs**
Save jobs and review later.

### 5️⃣ **Upgrade or Renew Anytime**
Just make a payment to the bank details above and your plan will be activated.
""")

st.markdown("---")

# ------------------------------------
# BENEFITS OVER OTHER PLATFORMS
# ------------------------------------
st.subheader("💡 Why Choose Chumcred Job Engine?")

st.markdown("""
### ✔ **All-in-One Platform**
Resume, cover letter, job search, scoring, and recommendations — everything in one place.

### ✔ **AI Personalized for Nigerian & Global Job Markets**
Many platforms are US-centric. Yours understands Nigerian context too.

### ✔ **Affordable Credit System**
Pay only for what you use.

### ✔ **Better Job Intelligence**
Unlike generic AI apps, your platform uses:
- Resume trends  
- User behavior  
- Job ranking intelligence  

### ✔ **Bank Payment Option**
Users without cards can still subscribe.

### ✔ **Privacy-Safe**
All resume processes happen securely within your system.
""")

st.markdown("---")

# ------------------------------------
# FAQs SECTION
# ------------------------------------
st.subheader("❓ Frequently Asked Questions (FAQ)")

with st.expander("How do I subscribe?"):
    st.write("""
    Make a payment to the Chumcred Limited account listed above.  
    Contact support with proof of payment — your account will be activated.
    """)

with st.expander("How are credits deducted?"):
    st.write("Each AI tool deducts a fixed number of credits automatically.")

with st.expander("Can I use multiple AI tools at once?"):
    st.write("Yes! As long as you have credits, everything works instantly.")

with st.expander("Can I cancel or pause my subscription?"):
    st.write("Subscriptions expire automatically when the duration ends.")

with st.expander("Is my resume stored?"):
    st.write("No. Resumes are processed temporarily and never stored permanently.")

st.markdown("---")

st.caption("Powered by Chumcred Job Engine © 2025")
