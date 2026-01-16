
# ==============================================================
# Dashboard.py — Professional Dashboard (Minor UI Fix)
# ==============================================================

import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime

from config.supabase_client import supabase  # kept as-is
from services.utils import get_subscription, is_low_credit
from components.sidebar import render_sidebar
from components.ui import hide_streamlit_sidebar

# --------------------------------------------------------------
# PAGE CONFIG (must be first Streamlit call)
# --------------------------------------------------------------
st.set_page_config(
    page_title="Dashboard – TalentIQ",
    page_icon="📊",
    layout="wide"
)

# --------------------------------------------------------------
# AUTH CHECK
# --------------------------------------------------------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")
    st.stop()

user = st.session_state.get("user")
if not user:
    st.error("Session expired. Please log in again.")
    st.switch_page("app.py")
    st.stop()

# --------------------------------------------------------------
# SIDEBAR
# --------------------------------------------------------------
hide_streamlit_sidebar()
render_sidebar()

# --------------------------------------------------------------
# USER CONTEXT (FIXED NAME HANDLING)
# --------------------------------------------------------------
user_id = user.get("id")

full_name = user.get("full_name")
email = user.get("email", "")

# Fallback: derive readable name ONLY if full_name is missing
if not full_name or not full_name.strip():
    if "@" in email:
        full_name = email.split("@")[0].replace(".", " ").title()
    else:
        full_name = "User"

# --------------------------------------------------------------
# BROADCAST POPUP (unchanged)
# --------------------------------------------------------------
try:
    from config.supabase_client import supabase_admin as supabase_srv
except Exception:
    supabase_srv = None

BROADCAST_TABLE = "broadcast_messages"
READS_TABLE = "broadcast_reads"


def _sanitize_text(x):
    return str(x).replace("\x00", "").strip() if x else ""


def get_latest_active_broadcast():
    if not supabase_srv:
        return None
    try:
        rows = (
            supabase_srv.table(BROADCAST_TABLE)
            .select("*")
            .eq("is_active", True)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
            .data or []
        )
        return rows[0] if rows else None
    except Exception:
        return None


def has_user_read_broadcast(bid, uid):
    if not supabase_srv:
        return True
    rows = (
        supabase_srv.table(READS_TABLE)
        .select("id")
        .eq("broadcast_id", bid)
        .eq("user_id", uid)
        .limit(1)
        .execute()
        .data or []
    )
    return len(rows) > 0


def mark_broadcast_read(bid, uid):
    if not supabase_srv:
        return
    try:
        supabase_srv.table(READS_TABLE).insert(
            {"broadcast_id": bid, "user_id": uid}
        ).execute()
    except Exception:
        pass


latest = get_latest_active_broadcast()
if latest:
    bid = latest.get("id")
    if bid and not has_user_read_broadcast(bid, user_id):
        st.toast("📣 New announcement from TalentIQ", icon="📣")

        with st.container(border=True):
            st.markdown("## 📣 Announcement")
            st.markdown(f"### {_sanitize_text(latest.get('title'))}")
            st.write(_sanitize_text(latest.get("message")))

            att_url = latest.get("attachment_url")
            att_type = (latest.get("attachment_type") or "").lower()

            if att_url and "video" in att_type:
                components.video(att_url)

            if st.button("✅ Got it", key=f"ack_{bid}"):
                mark_broadcast_read(bid, user_id)
                st.rerun()

        st.divider()

# --------------------------------------------------------------
# HEADER (FIXED — NAME NOT EMAIL)
# --------------------------------------------------------------
st.markdown(f"""
# 👋 Welcome back, **{full_name}**
Your AI-powered, one-stop career acceleration platform.
""")
st.write("---")

# --------------------------------------------------------------
# SUBSCRIPTION SUMMARY
# --------------------------------------------------------------
subscription = get_subscription(user_id)

if subscription:
    plan = subscription.get("plan", "None")
    credits = subscription.get("credits", 0)
    end_date = subscription.get("end_date")
else:
    plan = "None"
    credits = 0
    end_date = None

expiry_str = (
    datetime.fromisoformat(end_date).strftime("%d %b %Y")
    if end_date else "—"
)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("🧩 Subscription Plan", plan)

with col2:
    st.metric("💳 Credits Remaining", credits)

with col3:
    st.metric("⏳ Subscription Expires", expiry_str)

st.write("---")

# --------------------------------------------------------------
# MAIN CONTENT (UNCHANGED)
# --------------------------------------------------------------
st.markdown("""
## 🌟 Welcome to **Chumcred TalentIQ**

Chumcred TalentIQ is an **AI-powered Career & Talent Intelligence Platform**
designed to help job seekers understand their fit, improve competitiveness,
and secure better roles faster.

You don’t just apply — you apply **strategically**.
""")

# (rest of your long explanatory sections remain unchanged)
# --------------------------------------------------------------

# --------------------------------------------------------------
# MOVE DEMO VIDEO TO THE BOTTOM (FIX)
# --------------------------------------------------------------
st.write("---")
st.markdown("### 🎥 TalentIQ Demo Video")
st.video("https://www.youtube.com/watch?v=57lO3K_3E0c")

# --------------------------------------------------------------
# LOW CREDIT WARNING
# --------------------------------------------------------------
if is_low_credit(subscription, 20):
    st.warning("⚠️ You are running low on credits. Please top up.")

# --------------------------------------------------------------
# FOOTER
# --------------------------------------------------------------
st.write("---")
st.caption("Chumcred TalentIQ © 2025")
