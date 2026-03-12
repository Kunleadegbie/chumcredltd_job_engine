import streamlit as st
from config.supabase_client import supabase_admin

from components.ui import hide_streamlit_sidebar
from components.sidebar import render_sidebar

st.set_page_config(page_title="Activate Your TalentIQ Account", layout="wide")
hide_streamlit_sidebar()
render_sidebar()

st.title("🎓 Activate Your TalentIQ Account")

matric = st.text_input("Matric Number")
email = st.text_input("Email Address")
password = st.text_input("Create Password", type="password")

if st.button("Activate Account"):

    matric = (matric or "").strip()
    email = (email or "").strip().lower()
    password = (password or "").strip()

    if not matric or not email or not password:
        st.error("Matric number, email and password are required.")
        st.stop()

    # 1. Find imported placeholder student profile
    student = (
        supabase_admin
        .table("users_app")
        .select("*")
        .eq("matric_number", matric)
        .limit(1)
        .execute()
    )

    rows = student.data or []

    if not rows:
        st.error("Matric number not found.")
        st.stop()

    student_row = rows[0]

    # Optional: prevent double activation
    if (student_row.get("status") or "").lower() == "active":
        st.warning("This account has already been activated. You can login directly.")
        st.stop()

    # 2. Create real Supabase Auth account
    try:
        auth_res = supabase_admin.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": True
        })

        auth_user = getattr(auth_res, "user", None)

        if not auth_user:
            st.error("Failed to create authentication account.")
            st.stop()

    except Exception as e:
        st.error(f"Activation failed while creating login account: {e}")
        st.stop()

    # 3. Update users_app profile to match auth user
    try:
        supabase_admin.table("users_app").update({
            "id": auth_user.id,
            "email": email,
            "status": "active",
            "is_active": True
        }).eq("matric_number", matric).execute()

        st.success("Account activated successfully. You can now login.")

    except Exception as e:
        st.error(f"Activation failed while updating profile: {e}")