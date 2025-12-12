import streamlit as st
from config.supabase_client import supabase
from services.utils import (
    get_subscription,
    auto_expire_subscription,
    is_low_credit
)

st.set_page_config(
    page_title="Dashboard",
    page_icon="🏠",
    layout="wide"
)

# ---------------------------
# AUTH CHECK
# ---------------------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state["user"]
user_id = user["id"]

# ---------------------------
# SUBSCRIPTION STATUS
# ---------------------------
auto_expire_subscription(user_id)
subscription = get_subscription(user_id)

credits = subscription["credits"] if subscription else 0
expiry_date = subscription["end_date"] if subscription else None
status = subscription["subscription_status"] if subscription else "No Subscription"


# =========================
# PAGE HEADER — LINKEDIN STYLE
# =========================
st.markdown("""
# 👋 Welcome to **Chumcred Job Engine**
Your **AI-powered career success platform** — combining CV rewriting, interview tools, real-time job search, job recommendations, eligibility checks, skill extraction, and more into **one simple dashboard**.
""")

if is_low_credit(user_id):
    st.warning("⚠️ Your credits are low. Please top up to continue enjoying all AI features.")

# ---------------------------
# ACCOUNT BOX
# ---------------------------
with st.container():
    st.subheader("📊 Account Overview")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Subscription Status", status)

    with col2:
        st.metric("Credits Remaining", credits)

    with col3:
        st.metric("Expiry Date", expiry_date if expiry_date else "Not Available")


# =================================================
# BANK PAYMENT DETAILS — REQUIRED FOR SUBSCRIPTION
# =================================================
st.markdown("""
## 💳 Payment Details for Manual Subscription

To renew your subscription or buy more credits, please make payment to the account below:

**Account Name:** Chumcred Limited  
**Bank:** Sterling Bank Plc  
**Account Number:** 0087611334  

After payment, click the **Submit Payment** button on the Subscription page.
""")


# =================================================
# HOW TO USE THE APP — STEP BY STEP
# =================================================
st.markdown("""
## 🚀 How to Use This App (Step-by-Step)

1️⃣ **Go to Subscription page** → Activate a plan to get AI credits  
2️⃣ **Use AI Tools**:  
- Match Score (5 credits)  
- Skills Extraction (5 credits)  
- Cover Letter Writer (10 credits)  
- Resume Rewrite (15 credits)  
- Job Recommendations (5 credits)  
- Job Search (3 credits)  

3️⃣ Credits deduct automatically  
4️⃣ Download or copy your results instantly  
5️⃣ Save job posts for review later  
6️⃣ Upgrade or renew your subscription anytime  
""")


# =================================================
# WHY THIS PLATFORM IS BETTER (COMPARISON)
# =================================================
st.markdown("""
## ⭐ Why Choose **Chumcred Job Engine**?

### Compared to other platforms (LinkedIn, Indeed, standard resume builders):
| Feature | LinkedIn / Others | Chumcred Job Engine |
|--------|-------------------|----------------------|
| Real-time job search | ✔ Yes | ✔ Yes — plus instant AI evaluation |
| AI Match Score | ❌ No | ✔ Yes |
| AI Resume Rewrite | ⚠ Limited | ✔ Full rewrite using GPT-grade models |
| Cover Letter Generator | ⚠ Basic | ✔ Tailored, role-specific, ATS-optimized |
| Eligibility Checker | ❌ No | ✔ Yes |
| Skill Extraction | ❌ No | ✔ Yes |
| Localized Nigeria-friendly features | ❌ No | ✔ Yes |
| Pay-in-bank subscription | ❌ No | ✔ Yes |
| Save job posts | ✔ Yes | ✔ Yes |
| Credit-based usage | ❌ No | ✔ Affordable credit system |

### 💡 Summary:
**Chumcred Job Engine is a true all-in-one AI career platform** designed for serious job seekers who want speed, accuracy, and personalized results.
""")


# =================================================
# FAQ SECTION
# =================================================
st.markdown("""
## ❓ Frequently Asked Questions (FAQ)

### **1. Why do I need credits?**
Credits allow you to use premium AI tools without a recurring monthly fee.  
You only pay for what you use.

### **2. Can I pay manually through a bank transfer?**
Yes — see the payment details above.

### **3. Can I use this app without a subscription?**
Basic navigation works, but AI services require credits.

### **4. Are my documents stored?**
No — your resume and job descriptions are processed securely and deleted immediately.

### **5. Can I use this app on mobile?**
Yes — it is fully mobile responsive.
""")


# =================================================
# QUICK NAVIGATION BUTTONS
# =================================================
st.markdown("## ⚡ Quick Actions")

colA, colB, colC, colD = st.columns(4)

with colA:
    st.page_link("pages/3a_Match_Score.py", label="Match Score", icon="📊")

with colB:
    st.page_link("pages/3e_Resume_Writer.py", label="Resume Writer", icon="📝")

with colC:
    st.page_link("pages/3c_Cover_Letter.py", label="Cover Letter", icon="✉️")

with colD:
    st.page_link("pages/3_Job_Search.py", label="Job Search", icon="🔍")

st.write("---")

# -------------------------------------------------------
# FOOTER
# -------------------------------------------------------
st.caption("Chumcred Job Engine © 2025 — Powered by Chumcred Limited")
