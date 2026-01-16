import streamlit as st
import sys
import os
from datetime import datetime, timezone, timedelta

# ==========================================================
# ENSURE IMPORTS WORK (Render / Railway / Streamlit Cloud)
# ==========================================================
sys.path.append(os.path.dirname(__file__))

from components.sidebar import render_sidebar
from config.supabase_client import supabase

# ==========================================================
# PAGE CONFIG
# ==========================================================
st.set_page_config(
    page_title="Chumcred TalentIQ",
    page_icon="assets/talentiq_logo.png",
    layout="wide"
)

# ==========================================================
# HIDE STREAMLIT DEFAULT SIDEBAR / PAGE NAVIGATION
# ==========================================================
st.image("assets/talentiq_logo.png", width=280)
st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"] { display: none; }
        section[data-testid="stSidebar"] > div:first-child { padding-top: 0rem; }
    </style>
    """,
    unsafe_allow_html=True
)

# ==========================================================
# SESSION INITIALIZATION
# ==========================================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "user" not in st.session_state:
    st.session_state.user = None

if "sb_access_token" not in st.session_state:
    st.session_state.sb_access_token = None

if "sb_refresh_token" not in st.session_state:
    st.session_state.sb_refresh_token = None

# ==========================================================
# ADMIN EMAILS (prevents accidental role downgrade on first insert)
# ==========================================================
ADMIN_EMAILS = {
    "chumcred@gmail.com",
    "admin@talentiq.com",
    "kunle@chumcred.com",
}

# ==========================================================
# HELPERS
# ==========================================================
def is_valid_international_phone(phone: str) -> bool:
    """
    Accepts international phone numbers in E.164-like format.
    Examples:
      +447911123456
      +14165551234
    """
    if not phone:
        return False
    phone = phone.strip()
    if not phone.startswith("+"):
        return False
    if not phone[1:].isdigit():
        return False
    if len(phone) < 9 or len(phone) > 16:
        return False
    return True


def _extract_session_tokens(auth_res) -> tuple[str | None, str | None]:
    """
    Supabase session can be a dict-like or an object with attributes.
    Return (access_token, refresh_token) safely.
    """
    sess = getattr(auth_res, "session", None)

    if not sess:
        return None, None

    # dict-like
    if isinstance(sess, dict):
        return sess.get("access_token"), sess.get("refresh_token")

    # object-like
    access_token = getattr(sess, "access_token", None)
    refresh_token = getattr(sess, "refresh_token", None)
    return access_token, refresh_token


def restore_supabase_session() -> bool:
    """Restore Supabase Auth session for RLS-protected pages."""
    at = st.session_state.get("sb_access_token")
    rt = st.session_state.get("sb_refresh_token")
    if at and rt:
        try:
            supabase.auth.set_session(at, rt)
            return True
        except Exception:
            return False
    return False


def ensure_users_app_row(auth_user_id: str, email: str, full_name: str):
    """
    Ensure there's a users_app row for this Auth user id.
    Uses only fields already used across your pages: id, email, full_name, role.
    - If row exists -> returns it.
    - If not -> inserts a minimal row.
    """
    email_clean = (email or "").strip().lower()
    role_default = "admin" if email_clean in ADMIN_EMAILS else "user"

    # 1) Try fetch by id
    try:
        existing = (
            supabase.table("users_app")
            .select("id, email, full_name, role")
            .eq("id", auth_user_id)
            .limit(1)
            .execute()
        )
        if existing.data:
            return existing.data[0]
    except Exception:
        pass

    # 2) Insert minimal row (no phone assumptions)
    try:
        payload = {
            "id": auth_user_id,
            "email": email_clean,
            "full_name": (full_name or email_clean or "User"),
            "role": role_default,
        }
        ins = supabase.table("users_app").insert(payload).execute()
        if ins.data:
            return ins.data[0]
    except Exception:
        pass

    # 3) Fallback fetch by email
    try:
        existing2 = (
            supabase.table("users_app")
            .select("id, email, full_name, role")
            .ilike("email", email_clean)
            .limit(1)
            .execute()
        )
        if existing2.data:
            return existing2.data[0]
    except Exception:
        pass

    return None


def ensure_subscription_row(user_id: str):
    """
    Ensure user has a subscription row. FREEMIUM = 50 credits, 7 days.
    Uses only known columns from your subscriptions schema.
    """
    try:
        sub = (
            supabase.table("subscriptions")
            .select("user_id, plan, credits, subscription_status, start_date, end_date")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        if sub.data:
            return sub.data[0]

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
            return ins.data[0]
    except Exception:
        pass
    return None


def fetch_user_role(user_id: str) -> str:
    """
    Fetch role from users_app (source of truth).
    If blocked by RLS or missing, fall back to 'user'.
    """
    try:
        r = (
            supabase.table("users_app")
            .select("role")
            .eq("id", user_id)
            .limit(1)
            .execute()
        )
        if r.data:
            return (r.data[0].get("role") or "user")
    except Exception:
        pass
    return "user"


# ==========================================================
# IF LOGGED IN → RESTORE SESSION + REDIRECT
# ==========================================================
if st.session_state.authenticated and st.session_state.user:
    restore_supabase_session()
    render_sidebar()
    st.switch_page("pages/2_Dashboard.py")
    st.stop()


# ==========================================================
# LOGIN / REGISTER UI
# ==========================================================
st.title("🔐 Welcome to Chumcred TalentIQ")
st.caption("AI-powered tools for job seekers, career growth, and talent acceleration.")

tab1, tab2 = st.tabs(["🔓 Sign In", "📝 Register"])


# ==========================================================
# LOGIN TAB (AUTH = Supabase)
# ==========================================================
with tab1:
    st.subheader("Sign In")

    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Sign In"):
        email_clean = (email or "").strip().lower()
        password_clean = (password or "").strip()

        if not email_clean or not password_clean:
            st.error("Email and password are required.")
            st.stop()

        try:
            auth_res = supabase.auth.sign_in_with_password(
                {"email": email_clean, "password": password_clean}
            )

            if not auth_res or not getattr(auth_res, "user", None):
                st.error("Invalid email or password.")
                st.stop()

            # Save tokens (robust extraction)
            access_token, refresh_token = _extract_session_tokens(auth_res)
            st.session_state.sb_access_token = access_token
            st.session_state.sb_refresh_token = refresh_token

            # Restore immediately (enables RLS reads in same run)
            restore_supabase_session()

            auth_user = auth_res.user
            auth_user_id = auth_user.id
            auth_email = (auth_user.email or email_clean).strip().lower()

            full_name = None
            try:
                full_name = (getattr(auth_user, "user_metadata", None) or {}).get("full_name")
            except Exception:
                full_name = None

            # Ensure users_app exists
            profile = ensure_users_app_row(auth_user_id, auth_email, full_name or auth_email)
            if not profile:
                st.error("Login ok, but profile provisioning failed. Please contact admin.")
                st.stop()

            # Fetch role from users_app (source of truth)
            role = fetch_user_role(profile.get("id") or auth_user_id)

            # Ensure subscription exists
            ensure_subscription_row(profile["id"])

            # Save session user
            st.session_state.authenticated = True
            st.session_state.user = {
                "id": profile.get("id") or auth_user_id,
                "email": profile.get("email") or auth_email,
                "full_name": profile.get("full_name") or full_name or auth_email,
                "role": role,
            }

            st.success("Login successful!")
            st.rerun()

        except Exception as e:
            # IMPORTANT: show the real Supabase error to stop guesswork
            st.error(f"Login error: {e}")


    # --------------------------------------------------
    # FORGOT PASSWORD (EMAIL ONLY)
    # --------------------------------------------------
    st.divider()
    st.markdown("### 🔁 Forgot Password")

    reset_email = st.text_input(
        "Enter your registered email",
        placeholder="you@example.com",
        key="reset_email"
    )

    if st.button("Send Password Reset Email"):
        if not reset_email.strip():
            st.error("Please enter your email.")
        else:
            try:
                supabase.auth.reset_password_email(reset_email.strip().lower())
                st.success("Password reset email sent. Please check your inbox.")
            except Exception as e:
                st.error(f"Unable to send reset email: {e}")


# ==========================================================
# REGISTER TAB (AUTH + users_app + subscriptions)
# ==========================================================
with tab2:
    st.subheader("Create Account")

    full_name = st.text_input("Full Name")
    phone = st.text_input(
        "Phone Number (International Format)",
        placeholder="+447911123456"
    )
    reg_email = st.text_input("Email")
    reg_password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")

    if st.button("Register"):
        full_name_clean = (full_name or "").strip()
        phone_clean = (phone or "").strip()
        reg_email_clean = (reg_email or "").strip().lower()

        if not full_name_clean:
            st.error("Full Name is required.")
            st.stop()

        if not is_valid_international_phone(phone_clean):
            st.error("Invalid phone number. Use international format, e.g. +447911123456")
            st.stop()

        if not reg_email_clean:
            st.error("Email is required.")
            st.stop()

        if not reg_password.strip():
            st.error("Password is required.")
            st.stop()

        if reg_password != confirm_password:
            st.error("Passwords do not match.")
            st.stop()

        try:
            signup_res = supabase.auth.sign_up({
                "email": reg_email_clean,
                "password": reg_password,
                "options": {"data": {"full_name": full_name_clean, "phone": phone_clean}}
            })

            if not signup_res or not getattr(signup_res, "user", None):
                st.error("Registration failed.")
                st.stop()

            auth_user = signup_res.user

            # Ensure users_app row exists
            profile = ensure_users_app_row(auth_user.id, reg_email_clean, full_name_clean)
            if not profile:
                st.error("Account created, but user profile provisioning failed.")
                st.stop()

            # Ensure subscription exists
            ensure_subscription_row(profile["id"])

            st.success("Registration successful! You can now sign in.")

        except Exception as e:
            st.error(f"Registration error: {e}")


st.write("---")
st.caption("Powered by Chumcred Limited © 2025")
