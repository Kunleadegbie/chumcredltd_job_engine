# ==============================================================
# Dashboard.py — Fully Redesigned Professional Dashboard
# ==============================================================

import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
from config.supabase_client import supabase  # kept as-is (even if not used)
from services.utils import get_subscription, is_low_credit

from components.sidebar import render_sidebar

render_sidebar()

from components.ui import hide_streamlit_sidebar

# NEW: use admin client for broadcast read tracking (persistent popup)
try:
    from config.supabase_client import supabase_admin as supabase_srv
except Exception:
    supabase_srv = None


# ======================================================
# PAGE CONFIG (MUST BE FIRST STREAMLIT CALL)
# ======================================================
st.set_page_config(
    page_title="Dashboard – TalentIQ",
    page_icon="📊",
    layout="wide"
)


# ======================================================
# HIDE STREAMLIT SIDEBAR + RENDER CUSTOM SIDEBAR
# ======================================================
hide_streamlit_sidebar()
st.session_state["_sidebar_rendered"] = False


# ======================================================
# AUTH CHECK (ONLY ONCE)
# ======================================================
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")
    st.stop()

user = st.session_state.get("user")

if not user:
    st.error("Session expired. Please log in again.")
    st.switch_page("app.py")
    st.stop()

# Render custom sidebar (safe after auth exists)


# ======================================================
# USER CONTEXT — FIX NAME DISPLAY ONLY
# ======================================================
user = st.session_state.get("user", {})
user_id = user.get("id")  # ✅ REQUIRED for broadcast logic

raw_name = user.get("full_name", "")
email = user.get("email", "")

if not raw_name or "@" in raw_name:
    if email and "@" in email:
        full_name = email.split("@")[0].replace(".", " ").title()
    else:
        full_name = "User"
else:
    full_name = raw_name

# ======================================================
# BROADCAST POPUP (ONCE EVER, PERSISTENT)
# ======================================================
BROADCAST_TABLE = "broadcast_messages"
READS_TABLE = "broadcast_reads"


def _sanitize_text(x: str) -> str:
    if x is None:
        return ""
    return str(x).replace("\x00", "").strip()


def get_latest_active_broadcast():
    if supabase_srv is None:
        return None
    try:
        rows = (
            supabase_srv.table(BROADCAST_TABLE)
            .select("*")
            .eq("is_active", True)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
            .data
            or []
        )
        return rows[0] if rows else None
    except Exception:
        return None


def has_user_read_broadcast(broadcast_id: str, uid: str) -> bool:
    if supabase_srv is None:
        return True
    try:
        rows = (
            supabase_srv.table(READS_TABLE)
            .select("id")
            .eq("broadcast_id", broadcast_id)
            .eq("user_id", uid)
            .limit(1)
            .execute()
            .data
            or []
        )
        return len(rows) > 0
    except Exception:
        return False


def mark_broadcast_read(broadcast_id: str, uid: str):
    if supabase_srv is None:
        return
    try:
        # Unique(broadcast_id, user_id) prevents duplicates
        supabase_srv.table(READS_TABLE).insert(
            {"broadcast_id": broadcast_id, "user_id": uid}
        ).execute()
    except Exception:
        # If already exists, ignore
        pass


latest = get_latest_active_broadcast()
if latest:
    bid = latest.get("id")
    if bid and not has_user_read_broadcast(bid, user_id):
        st.toast("📣 New announcement from TalentIQ", icon="📣")

        with st.container(border=True):
            st.markdown("## 📣 Announcement")
            st.markdown(f"### {_sanitize_text(latest.get('title') or 'Announcement')}")
            st.write(_sanitize_text(latest.get("message") or ""))

            att_url = latest.get("attachment_url")
            att_name = latest.get("attachment_name") or "Attachment"
            att_type = (latest.get("attachment_type") or "").lower()

            if att_url:
                # Video attachment -> show smaller (Dashboard only)
                if "video" in att_type or str(att_url).lower().endswith((".mp4", ".mov", ".webm")):
                    left, mid, right = st.columns([1, 2, 1])  # mid controls breadth
                    with mid:
                        video_height_px = 450  # reduce length (height) but keep breadth
                        components.html(
                            f"""
                            <div style="width:100%; display:flex; justify-content:center;">
                              <video controls style="width:100%; max-height:{video_height_px}px; border-radius:12px;">
                                <source src="{att_url}">
                                Your browser does not support the video tag.
                              </video>
                            </div>
                            """,
                            height=video_height_px + 70,
                        )

                # Image attachment
                elif str(att_url).lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                    st.image(att_url, use_container_width=True)

                # Anything else -> link button
                else:
                    st.link_button(f"📎 Open: {att_name}", att_url)

            if st.button("✅ Got it", key=f"ack_broadcast_{bid}", use_container_width=False):
                mark_broadcast_read(bid, user_id)
                st.success("Thanks — you won’t see this announcement again.")
                st.rerun()

        st.divider()




# ======================================================
# LOAD SUBSCRIPTION (ALWAYS SOURCE OF TRUTH = DATABASE)
# ======================================================

subscription = get_subscription(user_id)

# 🔄 Sync session with latest DB credits
if subscription:
    st.session_state.user["credits"] = subscription.get("credits", 0)


if subscription:
    plan = subscription.get("plan", "None")
    credits = subscription.get("credits", 0)
    status = subscription.get("subscription_status", "inactive")
    start_date = subscription.get("start_date")
    end_date = subscription.get("end_date")
else:
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
# ABOUT TALENTIQ — HOMEPAGE DESCRIPTION
# ======================================================
st.markdown("""
## 🌟 Welcome to **Chumcred TalentIQ**

**Chumcred TalentIQ** is an **AI-powered Career & Talent Intelligence Platform** designed to help job seekers **understand their true job fit, improve their competitiveness, and secure better roles faster**.

TalentIQ goes beyond job search. It combines **ATS-grade analytics**, **resume intelligence**, and **career automation tools** into one unified platform — so you no longer need multiple apps, websites, or guesswork.

---

### 🚀 What Makes TalentIQ Different?

Most platforms only show jobs.  
TalentIQ tells you **how well you fit**, **why you fit**, and **what to improve**.

With TalentIQ, you don’t just apply — you apply **strategically**.

---

### 🧠 Core Intelligence Engines Inside TalentIQ

#### 🔹 ATS SmartMatch™ *(Premium Intelligence)*  
Upload your resume and a job description to receive:
- An **overall ATS match score**
- Detailed **sub-scores** (skills, experience, role fit)
- Clear explanations of **what recruiters and ATS systems see**
- Actionable recommendations to **improve your chances**

#### 🔹 InterviewIQ™ *(AI Interview Preparation Engine)*  
Practice real interview scenarios before the actual interview:
- AI-generated **role-specific interview questions**
- Real-time **answer evaluation and scoring**
- Breakdown of **strengths, weaknesses, and gaps**
- Clear recommendations to **improve interview performance**
- Confidence-building through structured feedback

InterviewIQ helps you walk into interviews **prepared, confident, and informed**.

#### 🔹 Match Score Analyzer  
Instantly measures how closely your CV aligns with a specific role.

#### 🔹 AI Skills Extraction  
Identifies required skills, missing competencies, and strengths from any job description.

#### 🔹 Resume Rewrite Engine  
Transforms your CV into a **professional, ATS-optimized resume**.

#### 🔹 AI Cover Letter Generator  
Creates tailored, role-specific cover letters in seconds.

#### 🔹 Eligibility Checker  
Determines whether you qualify for a role and explains the reasoning.

#### 🔹 Job Search & Recommendations  
Discover, review, and save opportunities that match your career profile.

---

### 🎯 Who TalentIQ Is Built For

- Job seekers who want **clarity**, not guesswork  
- Professionals targeting **competitive roles**  
- Graduates preparing for their first major opportunity  
- Anyone tired of applying blindly without feedback  

---

### 🏆 The Result

TalentIQ helps you:
- Apply with confidence  
- Improve your employability  
- Understand recruiter expectations  
- Maximize every job application  

**One platform. One dashboard. Total career intelligence.**
""")


# ======================================================
# HOW TO USE THE APP
# ======================================================
with st.expander("📘 How to Use This App"):
    st.markdown("""
### **1️⃣ Log in or create your account**  
Your dashboard keeps all your info and subscription details.

### **2️⃣ Subscribe to a plan**  
AI actions require credits.  
Pricing starts from **₦25,000 for 500 credits**.

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
- Automated **Match Score**
- AI-powered **resume rewrites**
- AI-generated **cover letters**
- AI-driven **interview preparation**
- Personalized **job recommendations**
- Real-time **credit tracking**
- Saves job postings inside the app  

This is the **only Nigerian-built platform** combining AI + job search + career intelligence in one place.
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
# CREDIT COST PER AI FUNCTION
# ======================================================
st.markdown("## 🔢 Credit Cost Per Feature")

st.markdown("""
| Feature | Credits per run |
|---|---:|
| Job Search (per search) | **3** |
| Match Score | **5** |
| Skills Extraction | **5** |
| Cover Letter | **5** |
| Eligibility Check | **5** |
| Resume Writer | **5** |
| Job Recommendations | **3** |
| ATS SmartMatch | **10** |
| InterviewIQ | **10** |
""")

st.caption("Tip: Your remaining credit balance is shown on your Dashboard and is deducted automatically when you run a tool.")


# ======================================================
# LOW CREDIT WARNING
# ======================================================
if is_low_credit(subscription, 20):
    st.warning("⚠️ You are running low on credits (<20). Please renew or buy more credits.")


# ======================================================
# DEMO VIDEO YOUTUBE LINK (TOP OF DASHBOARD)
# ======================================================
st.markdown("### 🎥 TalentIQ Demo Video")
st.video("https://www.youtube.com/watch?v=57lO3K_3E0c")
st.divider()

# ======================================================
# FOOTER
# ======================================================
st.write("---")
st.caption("Chumcred TalentIQ © 2025")
