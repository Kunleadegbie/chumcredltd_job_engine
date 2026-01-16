import streamlit as st
from datetime import datetime, timezone, timedelta
from config.supabase_client import supabase
from components.sidebar import render_sidebar  # ✅ IMPORTANT

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="My Account – TalentIQ",
    page_icon="👤",
    layout="centered"
)

# Hide Streamlit default multipage nav (keep only your custom sidebar)
st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"] { display: none !important; }
        section[data-testid="stSidebar"] > div:first-child { padding-top: 0rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ✅ Render your custom sidebar on this page
render_sidebar()

st.title("👤 My Account")

# -------------------------------------------------
# SESSION RESTORE (RLS)
# -------------------------------------------------
def restore_supabase_session() -> bool:
    at = st.session_state.get("sb_access_token")
    rt = st.session_state.get("sb_refresh_token")
    if at and rt:
        try:
            supabase.auth.set_session(at, rt)
            return True
        except Exception:
            return False
    return False


def ensure_subscription_row(user_id: str):
    """Auto-create FREEMIUM (50 credits, 7 days) only if missing."""
    try:
        existing = (
            supabase.table("subscriptions")
            .select("plan, credits, subscription_status, end_date")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        if existing.data:
            return existing.data[0]

        now = datetime.now(timezone.utc)
        payload = {
            "user_id": user_id,
            "plan": "FREEMIUM",
            "credits": 50,
            "amount": 0,
            "subscription_status": "active",
            "start_date": now.isoformat(),
            "end_date": (now + timedelta(days=7)).isoformat(),
        }
        ins = supabase.table("subscriptions").insert(payload).execute()
        if ins.data:
            return {
                "plan": ins.data[0].get("plan", "FREEMIUM"),
                "credits": ins.data[0].get("credits", 50),
                "subscription_status": ins.data[0].get("subscription_status", "active"),
                "end_date": ins.data[0].get("end_date"),
            }
    except Exception:
        return None
    return None


def parse_date_safe(value):
    if not value:
        return None
    try:
        s = str(value).replace("Z", "+00:00")
        return datetime.fromisoformat(s)
    except Exception:
        return None


# -------------------------------------------------
# AUTH GUARD
# -------------------------------------------------
if not st.session_state.get("user"):
    st.error("You must be logged in to view this page.")
    st.stop()

if not restore_supabase_session():
    st.error("Authentication error. Please log in again.")
    st.stop()

session_user = st.session_state.user
session_user_id = session_user.get("id")
session_email = (session_user.get("email") or "").strip()

if not session_email:
    st.error("Invalid session state. Please log in again.")
    st.stop()

# -------------------------------------------------
# FETCH USER PROFILE (ID → EMAIL FALLBACK)
# -------------------------------------------------
profile = None

try:
    if session_user_id:
        resp = (
            supabase.table("users_app")
            .select("id, full_name, email, role")
            .eq("id", session_user_id)
            .limit(1)
            .execute()
        )
        if resp.data:
            profile = resp.data[0]

    if not profile:
        resp = (
            supabase.table("users_app")
            .select("id, full_name, email, role")
            .ilike("email", session_email)
            .limit(1)
            .execute()
        )
        if resp.data:
            profile = resp.data[0]
            st.session_state.user["id"] = profile["id"]

except Exception:
    st.error("Authentication error. Please log in again.")
    st.stop()

if not profile:
    st.error(
        "Your user profile has not been fully provisioned.\n\n"
        "Please contact the administrator to complete account setup."
    )
    st.stop()

# -------------------------------------------------
# MUST CHANGE PASSWORD STATUS
# -------------------------------------------------
must_change = bool(st.session_state.get("force_pw_change"))

try:
    current = supabase.auth.get_user()
    auth_user = getattr(current, "user", None) or (current.get("user") if isinstance(current, dict) else None)
    meta = getattr(auth_user, "user_metadata", None) or {} if auth_user else {}
    if meta.get("must_change_password") is True:
        must_change = True
except Exception:
    pass

if must_change:
    st.warning("🔐 You are using a temporary password. Please change your password now to continue.")

# -------------------------------------------------
# FETCH / ENSURE SUBSCRIPTION (auto-credit if missing)
# -------------------------------------------------
subscription = None
try:
    sub_resp = (
        supabase.table("subscriptions")
        .select("plan, credits, subscription_status, end_date")
        .eq("user_id", profile["id"])
        .limit(1)
        .execute()
    )
    if sub_resp.data:
        subscription = sub_resp.data[0]
except Exception:
    subscription = None

if not subscription:
    subscription = ensure_subscription_row(profile["id"])

# -------------------------------------------------
# ACCOUNT SUMMARY
# -------------------------------------------------
st.subheader("📊 Account Summary")

if subscription:
    end_dt = parse_date_safe(subscription.get("end_date"))
    expiry_display = end_dt.strftime("%d %b %Y") if end_dt else "N/A"

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Plan", subscription.get("plan", ""))
        st.metric("Credits Available", int(subscription.get("credits", 0) or 0))
    with col2:
        st.metric("Status", subscription.get("subscription_status", ""))
        st.metric("Subscription Expiry", expiry_display)
else:
    st.warning("Subscription data not found.")

# -------------------------------------------------
# PROFILE INFORMATION
# -------------------------------------------------
st.divider()
st.subheader("👤 Profile Information")
st.text_input("Full Name", value=str(profile.get("full_name") or ""), disabled=True)
st.text_input("Email", value=str(profile.get("email") or ""), disabled=True)
st.text_input("Role", value=str(profile.get("role") or "user"), disabled=True)

# -------------------------------------------------
# CHANGE PASSWORD
# -------------------------------------------------
st.divider()
st.subheader("🔐 Change Password")

with st.form("change_password_form"):
    new_password = st.text_input("New Password", type="password")
    confirm_password = st.text_input("Confirm New Password", type="password")
    submit = st.form_submit_button("Update Password")

    if submit:
        if not new_password or not confirm_password:
            st.error("All fields are required.")
            st.stop()

        if new_password != confirm_password:
            st.error("Passwords do not match.")
            st.stop()

        if len(new_password) < 8:
            st.error("Password must be at least 8 characters.")
            st.stop()

        try:
            # ✅ Update password AND clear must_change_password flag
            res = supabase.auth.update_user(
                {"password": new_password, "data": {"must_change_password": False}}
            )

            if res and getattr(res, "user", None):
                st.session_state.force_pw_change = False
                st.success("Password updated successfully.")
                st.switch_page("pages/2_Dashboard.py")
                st.stop()

            st.error("Password update failed.")

        except Exception:
            st.error("Password update failed. Please log in again and retry.")
            st.stop()
