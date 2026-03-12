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

    matric = matric.strip()

    student = (
        supabase_admin
        .table("users_app")     # corrected table
        .select("*")
        .eq("matric_number", matric)
        .execute()
    )

    rows = student.data or []

    if not rows:
        st.error("Matric number not found.")
        st.stop()

    supabase_admin.table("users_app").update({
        "email": email.strip(),
        "password": password,
        "status": "active",
        "is_active": True
    }).eq("matric_number", matric).execute()

    st.success("Account activated. You can now login.")