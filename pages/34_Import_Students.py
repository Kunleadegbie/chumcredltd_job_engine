import streamlit as st
import pandas as pd
from config.supabase_client import supabase_admin
from components.ui import hide_streamlit_sidebar
from components.sidebar import render_sidebar

st.set_page_config(page_title="Import Students", layout="wide")
hide_streamlit_sidebar()
render_sidebar()

st.title("📥 Import Students (CSV)")

user = st.session_state.get("user")

if not user:
    st.error("Please login.")
    st.stop()

user_id = user.get("id")
user_role = (user.get("role") or "").lower()


# =========================================================
# BATCH INSERT STUDENTS
# =========================================================

def batch_insert_students(records, batch_size=1000):

    total = len(records)
    inserted = 0

    for i in range(0, total, batch_size):

        batch = records[i:i + batch_size]

        try:
            supabase_admin.table("users_app").insert(batch).execute()
            inserted += len(batch)

        except Exception as e:
            st.error(f"Batch insert failed: {e}")
            return inserted

    return inserted


# --------------------------------------------------
# ADMIN OVERRIDE
# --------------------------------------------------

admin_override = user_role == "admin"

if admin_override:
    institution_id = None

else:

    membership = (
        supabase_admin.table("institution_members")
        .select("institution_id, member_role")
        .eq("user_id", user_id)
        .execute()
    )

    members = membership.data or []

    if not members:
        st.error("You are not assigned to any institution.")
        st.stop()

    institution_id = members[0]["institution_id"]
    role = (members[0]["member_role"] or "").lower()

    if role not in ["admin", "recruiter"]:
        st.error("Only institution admins can import students.")
        st.stop()


# --------------------------------------------------
# FILE UPLOAD
# --------------------------------------------------

st.subheader("Upload Student CSV")

uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])

if uploaded_file:

    try:

        # --------------------------------------------------
        # READ CSV
        # --------------------------------------------------

        df = pd.read_csv(uploaded_file)

        # --------------------------------------------------
        # CLEAN HEADER NAMES
        # --------------------------------------------------

        df.columns = df.columns.str.strip()

        # --------------------------------------------------
        # MAP HEADER VARIANTS (UPPER + LOWER CASE)
        # --------------------------------------------------

        column_map = {
            "Matric_Number": "matric_number",
            "matric_number": "matric_number",

            "Full_Name": "full_name",
            "full_name": "full_name",

            "Faculty": "faculty",
            "faculty": "faculty",

            "Department": "department",
            "department": "department",

            "Program": "program",
            "program": "program",

            "Level": "level",
            "level": "level",

            "Email": "email",
            "email": "email"
        }

        df = df.rename(columns=column_map)

        # --------------------------------------------------
        # REQUIRED COLUMNS
        # --------------------------------------------------

        required_columns = ["matric_number", "full_name", "faculty"]

        missing = [c for c in required_columns if c not in df.columns]

        if missing:
            st.error(f"Missing required columns: {missing}")
            st.stop()

        # --------------------------------------------------
        # CLEAN DATA
        # --------------------------------------------------

        df["matric_number"] = df["matric_number"].astype(str).str.strip()
        df["full_name"] = df["full_name"].astype(str).str.strip()
        df["faculty"] = df["faculty"].astype(str).str.strip()

        if "email" in df.columns:
            df["email"] = df["email"].astype(str).str.strip()

        # Prevent Excel scientific notation corruption
        df["matric_number"] = df["matric_number"].astype(str)

        # Remove duplicates
        df = df.drop_duplicates(subset=["matric_number"])

    except Exception:
        st.error("Failed to read CSV file.")
        st.stop()

    st.write("Preview of uploaded file:")
    st.dataframe(df.head())

    total_rows = len(df)

    st.info(f"{total_rows} students ready for import.")

    # --------------------------------------------------
    # IMPORT BUTTON
    # --------------------------------------------------

    if st.button("Import Students"):

        records = []

        for _, row in df.iterrows():

            records.append({

                "full_name": row["full_name"],
                "email": row.get("email"),

                "role": "student",

                "faculty": row.get("faculty"),
                "department": row.get("department"),
                "program": row.get("program"),
                "level": row.get("level"),

                "matric_number": row["matric_number"],

                "institution_id": institution_id,

                "status": "pending_activation",
                "is_active": True,

                "credit_balance": 0,
                "subscription_plan": "FREEMIUM"

            })

        inserted = batch_insert_students(records)

        skipped = total_rows - inserted

        st.success(f"{inserted} students imported successfully.")
        st.warning(f"{skipped} rows skipped (duplicates or errors).")