# ==============================================================
# Dashboard.py — Fully Redesigned Professional Dashboard
# ==============================================================

import streamlit as st
from datetime import datetime
from config.supabase_client import supabase
from services.utils import get_subscription, is_low_credit, deduct_credits


# ======================================================
# PAGE CONFIG
# ======================================================
st.set_page_config(
    page_title="Dashboard – Job Engine",
    page_icon="📊",
    layout="wide"
)


# ======================================================
# AUTHENTICATION SAFETY CHECK
# ======================================================
# Ensure user is logged in
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state.get("user")

# Handle expired session
if not user:
    st.error("Session expired. Please log in again.")
    st.switch_page("app.py")
    st.stop()

user_id = user.get("id")
full_name = user.get("full_name", "User")


# ======================================================
# FETCH SUBSCRIPTION DETAILS
# ======================================================
subscription = get_subscription(user_id)

plan = subscription.get("plan") if subscription else "None"
credits = subscription.get("credits") if subscription else 0
status = subscription.get("subscription_status") if subscription else "inactive"

start_date = subscription.get("start_date") if subscription else None
end_date = subscription.get("end_date") if subscription else None

expiry_str = (
    datetime.fromisoformat(end_date).strftime("%d %b %Y")
    if end_date else "—"
)

sub_active = status == "active"


# ======================================================
# DASHBOARD HEADER — LinkedIn/Indeed Style
# ======================================================
st.markdown(f"""
# 👋 Welcome back, **{full_name}**  
Your one-stop AI-powered career advancement platform.
""")
st.write("---")


# ======================================================
#  TOP SUMMARY CARDS (Plan, Credits, Expiry)
# ======================================================
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div style='padding:18px; border-radius:12px; background:#F0F7FF; border:1px solid #C2DAFF;'>
        <h4 style='margin-bottom:0;'>🧩 Subscription Plan</h4>
        <p style='font-size:22px; font-weight:bold; margin-top:5px;'>""", unsafe_allow_html=True)
    st.markdown(f"**{plan}**")
    st.markdown("</p></div>", unsafe_allow_html=True)

with col2:
    color = "red" if credits < 5 else "#0047AB"
    st.markdown(f"""
    <div style='padding:18px; border-radius:12px; background:#FFF7EA; border:1px solid #FFE0A3;'>
        <h4 style='margin-bottom:0;'>💳 Credits Remaining</h4>
        <p style='font-size:22px; font-weight:bold; margin-top:5px; color:{color};'>{credits} credits</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div style='padding:18px; border-radius:12px; background:#EFFFF4; border:1px solid #A0E8C3;'>
        <h4 style='margin-bottom:0;'>⏳ Subscription Expires</h4>
        <p style='font-size:22px; font-weight:bold; margin-top:5px;'>""", unsafe_allow_html=True)
    st.markdown(f"{expiry_str}")
    st.markdown("</p></div>", unsafe_allow_html=True)


st.write("---")


# ======================================================
#  ABOUT THIS APP — Strong Marketing Version
# ======================================================
st.markdown("""
## 🌟 About This App (Read This First)

Chumcred Job Engine is an **AI-powered career platform** designed to give job seekers a competitive edge.

This app combines **six intelligence engines**:

1. **Match Score Analyzer** — compares your CV against job descriptions  
2. **AI Skills Extraction** — reveals missing and relevant skills  
3. **AI Cover Letter Writer** — tailored to each job  
4. **Eligibility Checker** — evaluates your suitability  
5. **Resume Rewrite Engine** — professionally restructures your CV  
6. **AI Job Recommendations** — finds jobs matching your profile  

Everything works in **one place**, making this tool more powerful than Indeed, LinkedIn, Jobberman, and MyJobMag combined.
""")

st.write("---")


# ======================================================
#   HOW TO USE THE APP (Step-by-Step Guide)
# ======================================================
with st.expander("📘 How to Use This App (Step-by-Step Guide)"):
    st.markdown("""
### **1️⃣ Create an account or log in**
Your dashboard keeps all your activity and saved jobs.

### **2️⃣ Subscribe to a plan**
You need credits to run AI tools.  
Prices start from **₦5,000 for 100 credits.**

### **3️⃣ Upload your resume / paste a job description**
Each AI module guides you step by step.

### **4️⃣ View results instantly**
Match score, rewritten resume, skills analysis, job recommendations — all in seconds.

### **5️⃣ Save jobs you like**
Job postings in the "Job Search" page can be bookmarked.

### **6️⃣ Track credits & subscription**
Your dashboard keeps real-time status.

### **That's it — your full job-search ecosystem in one place.**
""")


# ======================================================
# BENEFITS — WHY THIS APP IS BETTER THAN OTHERS
# ======================================================
with st.expander("💡 Why Job Engine is Better Than LinkedIn / Indeed / Jobberman"):
    st.markdown("""
### **Direct Benefits**
- Personalized **Match Score** for every job  
- Cover Letter + Resume rewriting using **advanced AI**  
- Skills gap identification  
- Local + global job search  
- Save jobs + track activity  

### **Advantages Over Other Platforms**
- LinkedIn does NOT analyze your resume against job descriptions  
- Indeed does NOT rewrite your resume with AI  
- Jobberman does NOT give match score analytics  
- ChatGPT alone doesn’t provide credit tracking, subscription, job saving, or real job feeds  

**Job Engine combines all of these into ONE platform.**
""")


# ======================================================
# BANK DETAILS FOR PAYMENT
# ======================================================
st.write("---")
st.markdown("""
### 💰 **Payment Information (For Manual Transfers)**  
Use these account details if paying outside the platform:

**🏦 Account Name:** Chumcred Limited  
**🏛 Bank:** Sterling Bank Plc  
**🔢 Account Number:** 0087611334  

After payment, go to **Subscription → Submit Payment**.
""")


# ======================================================
# LOW CREDIT WARNING
# ======================================================
if is_low_credit(credits):
    st.warning("⚠️ You are running low on credits. Please top up soon.")


# ======================================================
# END OF PAGE
# ======================================================
st.write("---")
st.caption("Chumcred Job Engine © 2025")
