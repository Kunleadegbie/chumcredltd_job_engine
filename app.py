import streamlit as st
import sys
import os
from datetime import datetime, timezone, timedelta

# ==========================================================
# ENSURE IMPORTS WORK (Render / Railway / Streamlit Cloud)
# ==========================================================
sys.path.append(os.path.dirname(__file__))

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
        [data-testid="stSidebarNav"] { display: none !important; }
        section[data-testid="stSidebar"] > div:first-child { padding-top: 0rem; }
    </style>
    """,
    unsafe_allow_html=True
)

# ==========================================================
# SESSION INITIALIZATION
# ==========================================================
st.session_state.setdefault("authenticated", False)
st.session_state.setdefault("user", None)
st.session_state.setdefault("sb_access_token", None)
st.session_state.setdefault("sb_refresh_token", None)
st.session_state.setdefault("force_pw_change", False)

# ==========================================================
# ADMIN EMAILS (prevents accidental role downgrade)
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
    return 9 <= len(phone) <= 16


def _extract_session_tokens(auth_res) -> tuple[str | None, str | None]:
    """
    Supabase session can be dict-like or object-like depending on sdk version.
    Return (access_token, refresh_token) safely.
    """
    sess = getattr(auth_res, "session", None)

    if not sess:
        return None, None

    if isinstance(sess, dict):
        return sess.get("access_token"), sess.get("refresh_token")

    at = getattr(sess, "access_token", None)
    rt = getattr(sess, "refresh_token", None)
    return at, rt


def restore_supabase_session() -> bool:
    """Restore Supabase Auth session for RLS-protected reads/writes."""
    at = st.session_state.get("sb_access_token")
    rt = st.session_state.get("sb_refresh_token")
    if at and rt:
        try:
            supabase.auth.set_session(at, rt)
            return True
        except Exception:
            return False
    return False


def user_must_change_password(auth_user) -> bool:
    """
    Restored users were created with user_metadata.must_change_password = True.
    New users should NOT have this flag.
    """
    try:
        meta = getattr(auth_user, "user_metadata", None) or {}
        return bool(meta.get("must_change_password"))
    except Exception:
        return False


def ensure_users_app_row(auth_user_id: str, email: str, full_name: str):
    """
    Ensure there's a users_app row for this Auth user id.
    Uses only known fields: id, email, full_name, role.
    """
    email_clean = (email or "").strip().lower()
    role_default = "admin" if email_clean in ADMIN_EMAILS else "user"
    full_name_clean = (full_name or email_clean or "User").strip()

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
            "full_name": full_name_clean,
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
    Does NOT overwrite existing subscription rows.
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
        return None

    return None


# ==========================================================
# IF ALREADY LOGGED IN: send to dashboard (unless forcing pw change)
# ==========================================================
if st.session_state.get("authenticated") and st.session_state.get("user"):
    # Try restore session quietly
    restore_supabase_session()

    # If we are forcing password change, go to My Account
    if st.session_state.get("force_pw_change"):
        st.switch_page("pages/1_My_Account.py")
        st.stop()

    # Otherwise go to dashboard
    st.switch_page("pages/2_Dashboard.py")
    st.stop()

# ==========================================================
# LOGIN / REGISTER UI
# ==========================================================
st.title("Welcome to TalentIQ")
tab1, tab2 = st.tabs(["Login", "Register"])

# ==========================================================
# LOGIN TAB
# ==========================================================
with tab1:
    st.subheader("Sign In")
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Login"):
        if not email.strip() or not password:
            st.error("Email and password are required.")
            st.stop()

        try:
            auth_res = supabase.auth.sign_in_with_password(
                {"email": email.strip(), "password": password}
            )

            if not auth_res or not getattr(auth_res, "user", None):
                st.error("Invalid email or password.")
                st.stop()

            # Save tokens safely
            at, rt = _extract_session_tokens(auth_res)
            st.session_state.sb_access_token = at
            st.session_state.sb_refresh_token = rt

            # Restore immediately for RLS reads
            if not restore_supabase_session():
                # Not fatal; but often indicates token mismatch
                pass

            auth_user = auth_res.user
            auth_user_id = auth_user.id
            auth_email = auth_user.email

            # Full name from metadata
            try:
                full_name = (auth_user.user_metadata or {}).get("full_name") or auth_email
            except Exception:
                full_name = auth_email

            # Ensure users_app row exists + read role
            profile = ensure_users_app_row(auth_user_id, auth_email, full_name)
            if not profile:
                st.error("Login ok, but profile provisioning failed. Please contact admin.")
                st.stop()

            # Ensure subscription exists (FREEMIUM auto-credit if missing)
            ensure_subscription_row(profile["id"])

            # Save session user
            st.session_state.authenticated = True
            st.session_state.user = {
                "id": profile.get("id") or auth_user_id,
                "email": profile.get("email") or auth_email,
                "full_name": profile.get("full_name") or full_name or auth_email,
                "role": profile.get("role", "user"),
            }

            # ✅ Must-change-password enforcement (restored users only)
            if user_must_change_password(auth_user):
                st.session_state.force_pw_change = True
                st.success("Login successful — please change your temporary password.")
                st.switch_page("pages/1_My_Account.py")
                st.stop()

            st.session_state.force_pw_change = False
            st.success("Login successful!")
            st.switch_page("pages/2_Dashboard.py")
            st.stop()

        except Exception:
            st.error("Login error: Invalid login credentials")

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
                supabase.auth.reset_password_email(reset_email.strip())
                st.success("Password reset email sent. Please check your inbox.")
            except Exception:
                st.error("Unable to send reset email.")

# ==========================================================
# REGISTER TAB
# ==========================================================
with tab2:
    st.subheader("Create Account")

    full_name = st.text_input("Full Name", key="reg_full_name")
    phone = st.text_input(
        "Phone Number (International Format)",
        placeholder="+447911123456",
        key="reg_phone"
    )
    reg_email = st.text_input("Email", key="reg_email")
    reg_password = st.text_input("Password", type="password", key="reg_password")
    confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm_password")

    if st.button("Register"):
        if not full_name.strip():
            st.error("Full Name is required.")
            st.stop()

        if not is_valid_international_phone(phone):
            st.error("Invalid phone number. Use international format, e.g. +447911123456")
            st.stop()

        if not reg_email.strip():
            st.error("Email is required.")
            st.stop()

        if not reg_password.strip():
            st.error("Password is required.")
            st.stop()

        if reg_password != confirm_password:
            st.error("Passwords do not match.")
            st.stop()

        try:
            # ✅ New users should NOT be flagged must_change_password
            signup_res = supabase.auth.sign_up({
                "email": reg_email.strip(),
                "password": reg_password,
                "options": {
                    "data": {
                        "full_name": full_name.strip(),
                        "phone": phone.strip()
                    }
                }
            })

            if not signup_res or not getattr(signup_res, "user", None):
                st.error("Registration failed.")
                st.stop()

            # Some setups return no session until email confirmation
            auth_user = signup_res.user

            # Provision users_app immediately (non-RLS tables can still be written; if RLS blocks, it will fail safely)
            profile = ensure_users_app_row(auth_user.id, reg_email.strip(), full_name.strip())
            if not profile:
                st.error("Account created, but user profile provisioning failed.")
                st.stop()

            # ✅ Auto-create FREEMIUM subscription (7 days) if missing
            ensure_subscription_row(profile["id"])

            st.success("Registration successful! You can now sign in.")

        except Exception as e:
            st.error(f"Registration error: {e}")

st.write("---")
st.caption("Powered by Chumcred Limited © 2025")
