# ==============================================================
# Dashboard.py — Fully Redesigned Professional Dashboard
# ==============================================================

import streamlit as st
from datetime import datetime
from config.supabase_client import supabase
from services.utils import get_subscription, is_low_credit


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

# ======================================================
# PAGE CONFIG
# ======================================================
st.set_page_config(
    page_title="Dashboard – Job Engine",
    page_icon="📊",
    layout="wide"
)


# ======================================================
# AUTHENTICATION CHECK
# ======================================================
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state.get("user")

if not user:
    st.error("Session expired. Please log in again.")
    st.switch_page("app.py")
    st.stop()

user_id = user.get("id")
full_name = user.get("full_name", "User")


# ======================================================
# LOAD SUBSCRIPTION
# ======================================================
subscription = get_subscription(user_id)

if subscription:
    plan = subscription.get("plan", "None")
    credits = subscription.get("credits", 0)
    status = subscription.get("subscription_status", "inactive")
    start_date = subscription.get("start_date")
    end_date = subscription.get("end_date")
else:
    # No subscription found
    plan = "None"
    credits = 0
    status = "inactive"
    start_date = None
    end_date = None

expiry_str = (
    datetime.fromisoformat(end_date).strftime("%d %b %Y")
    if end_date else "—"
)


# ======================================================
# HEADER — LinkedIn/Indeed Style
# ======================================================
st.markdown(f"""
# 👋 Welcome back, **{full_name}**
Your AI-powered, one-stop career acceleration platform.
""")
st.write("---")


# ======================================================
# SUMMARY CARDS (Plan, Credits, Expiry)
# ======================================================
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div style='padding:18px; border-radius:12px; background:#F0F7FF; border:1px solid #C2DAFF;'>
        <h4 style='margin-bottom:0;'>🧩 Subscription Plan</h4>
    """, unsafe_allow_html=True)
    st.markdown(f"<p style='font-size:22px; font-weight:bold;'>{plan}</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    color = "red" if credits < 20 else "#0047AB"
    st.markdown(f"""
    <div style='padding:18px; border-radius:12px; background:#FFF7EA; border:1px solid #FFE0A3;'>
        <h4 style='margin-bottom:0;'>💳 Credits Remaining</h4>
        <p style='font-size:22px; font-weight:bold; color:{color};'>{credits} credits</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div style='padding:18px; border-radius:12px; background:#EFFFF4; border:1px solid #A0E8C3;'>
        <h4 style='margin-bottom:0;'>⏳ Subscription Expires</h4>
    """, unsafe_allow_html=True)
    st.markdown(f"<p style='font-size:22px; font-weight:bold;'>{expiry_str}</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

st.write("---")


# ======================================================
# ABOUT THIS APP — Enhanced Marketing Version
# ======================================================
st.markdown("""
## 🌟 About This App — Your Complete AI Career Toolkit

Chumcred Job Engine is a **full-suite AI career platform** built to help job seekers stand out instantly.

This platform integrates **six intelligent engines**:

### 🔹 1. Match Score Analyzer  
Compares your CV to any job description and returns a quantified match percentage + insights.

### 🔹 2. AI Skills Extraction  
Reveals required skills, missing skills, and strengths.

### 🔹 3. AI Cover Letter Generator  
Creates tailored, professional cover letters in seconds.

### 🔹 4. Eligibility Checker  
Assesses whether you qualify for a role and explains why.

### 🔹 5. Resume Rewrite Engine  
Transforms your CV into a professional, ATS-optimized document.

### 🔹 6. Job Recommendations  
Find jobs that fit your career profile and skills.

**Everything in one app — no switching between LinkedIn, Jobberman, ChatGPT, or multiple tools.**
""")

st.write("---")


# ======================================================
# HOW TO USE THE APP
# ======================================================
with st.expander("📘 How to Use This App"):
    st.markdown("""
### **1️⃣ Log in or create your account**  
Your dashboard keeps all your info and subscription details.

### **2️⃣ Subscribe to a plan**  
AI actions require credits.  
Pricing starts from **₦5,000 for 100 credits**.

### **3️⃣ Navigate to any AI tool**  
Upload resume → paste job description → click generate.

### **4️⃣ Review the results instantly**  
AI does all the analysis and writing for you.

### **5️⃣ Save interesting jobs**  
Use the Job Search page to find and save opportunities.

### **6️⃣ Monitor your subscription & credits**  
Dashboard updates in real time.

This platform is designed to **simplify your job search experience**.
""")


# ======================================================
# BENEFITS — WHY THIS IS BETTER THAN OTHER PLATFORMS
# ======================================================
with st.expander("💡 Why This Platform is Better Than LinkedIn / Indeed / Jobberman"):
    st.markdown("""
### 🚀 **Unique Advantages**
- Automated **Match Score** (LinkedIn & Indeed cannot do this)
- AI-powered **resume rewrites**
- AI-generated **cover letters**
- Personalized **job recommendations**
- Real-time **credit tracking**
- Saves job postings inside the app  
- Built-in **subscription management**

This is the **only Nigerian-built platform** combining AI + job search + resume engineering in one place.
""")


# ======================================================
# PAYMENT DETAILS SECTION
# ======================================================
st.write("---")
st.markdown("""
### 💰 Payment Information (Bank Transfer)

If you prefer paying manually, use:

**🏦 Account Name:** Chumcred Limited  
**🏛 Bank:** Sterling Bank Plc  
**🔢 Account Number:** 0087611334  

After payment, proceed to:  
👉 **Subscription → Submit Payment**
""")


# ======================================================
# LOW CREDIT WARNING
# ======================================================
if is_low_credit(subscription, 20):
    st.warning("⚠️ You are running low on credits (<20). Please renew or buy more credits.")


# ======================================================
# FOOTER
# ======================================================
st.write("---")
st.caption("Chumcred Job Engine © 2025")
