
import streamlit as st
from services.supabase_client import supabase   # ✅ SINGLE UNIFIED CLIENT


# -----------------------------
# PAGE CONFIGURATION
# -----------------------------
st.set_page_config(page_title="Chumcred Job Engine", page_icon="🚀")


# -----------------------------
# INITIALIZE SESSION STATE
# -----------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "user" not in st.session_state:
    st.session_state.user = None


# -----------------------------
# AUTH FUNCTIONS
# -----------------------------
def login_user(email, password):
    """Authenticate user via Supabase."""
    try:
        res = (
            supabase.table("users")
            .select("*")
            .eq("email", email)
            .eq("password", password)
            .execute()
        )
        if res.data:
            return res.data[0]
        return None
    except Exception as e:
        st.error("Login error: " + str(e))
        return None


def register_user(name, email, password):
    """Register new user using unified Supabase client."""
    try:
        # Check if email already exists
        check = supabase.table("users").select("*").eq("email", email).execute()
        if check.data:
            return False, "Email already registered."

        data = {
            "full_name": name,
            "email": email,
            "password": password,
            "role": "user",
        }

        supabase.table("users").insert(data).execute()
        return True, "Registration successful."
    except Exception as e:
        return False, "Registration error: " + str(e)


# -----------------------------
# AUTH PAGE UI (TABS)
# -----------------------------
st.title("🔐 Welcome to Chumcred Job Engine")
st.write("Please sign in or register to continue.")

tab1, tab2 = st.tabs(["🔓 Sign In", "📝 Register"])


# -----------------------------
# TAB 1 — SIGN IN
# -----------------------------
with tab1:
    st.subheader("Login to your account")

    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Sign In", key="login_btn"):
        user = login_user(email, password)

        if user:
            st.session_state.authenticated = True
            st.session_state.user = user

            st.success("Login successful! Redirecting...")
            st.rerun()
        else:
            st.error("Invalid email or password")


# -----------------------------
# TAB 2 — REGISTER
# -----------------------------
with tab2:
    st.subheader("Create a new account")

    full_name = st.text_input("Full Name", key="reg_name")
    reg_email = st.text_input("Email", key="reg_email")
    reg_password = st.text_input("Password", type="password", key="reg_password")
    reg_confirm = st.text_input("Confirm Password", type="password", key="reg_confirm")

    if st.button("Register", key="reg_btn"):
        if reg_password != reg_confirm:
            st.error("Passwords do not match.")
        else:
            success, msg = register_user(full_name, reg_email, reg_password)
            if success:
                st.success(msg)
                st.info("Please sign in using the Login tab.")
            else:
                st.error(msg)


# -----------------------------
# AUTO REDIRECT IF LOGGED IN
# -----------------------------
if st.session_state.authenticated:
    st.switch_page("pages/2_Dashboard.py")


# -----------------------------
# FOOTER
# -----------------------------
st.write("---")
st.caption("Powered by Chumcred Limited © 2025")

