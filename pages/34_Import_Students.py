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

def batch_insert_students(records):
    """
    Insert many students at once using Supabase batch insert
    """

    from config.supabase_client import supabase

    try:

        response = (
            supabase
            .table("users_app")
            .insert(records)
            .execute()
        )

        if response.data:
            return len(response.data)

        return 0

    except Exception as e:
        st.error(f"Batch insert failed: {e}")
        return 0

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
        # Read CSV
        df = pd.read_csv(uploaded_file)

        # Normalize column names
        df.columns = df.columns.str.strip().str.lower()

        # Define required columns (lowercase)
        required_cols = ["matric_number", "full_name", "email", "faculty"]

        missing = [c for c in required_cols if c not in df.columns]

        if missing:
            st.error(f"Missing required columns: {missing}")
            st.stop()

    except Exception:
        st.error("Failed to read CSV file.")
        st.stop()

    st.write("Preview of uploaded file:")
    st.dataframe(df.head())

    required_columns = ["Matric_Number", "Full_Name", "Faculty"]
    missing = [c for c in required_columns if c not in df.columns]

    if missing:
        st.error(f"Missing required columns: {missing}")
        st.stop()

    df = df.drop_duplicates(subset=["Matric_Number"])
    df["Matric_Number"] = df["Matric_Number"].astype(str).str.strip()
    df["Full_Name"] = df["Full_Name"].astype(str).str.strip()
    df["Faculty"] = df["Faculty"].astype(str).str.strip()
    df["matric_number"] = df["matric_number"].astype(str)

    total_rows = len(df)
    st.info(f"{total_rows} students ready for import.")

    if st.button("Import Students"):

        inserted = 0
        skipped = 0


        records = []

        for _, row in df.iterrows():
            records.append({
                "full_name": row["full_name"],
                "email": row["email"],
                "role": "student",
                "faculty": row["faculty"],
                "department": row["department"],
                "program": row["program"],
                "matric_number": row["matric_number"],
                "level": row["level"],
                "institution_id": institution_id,
                "status": "pending_activation",
                "is_active": True,
                "credit_balance": 0,
                "subscription_plan": "FREEMIUM"
            })

        
        # ---------------------------------------
        # FAST BATCH INSERT
        # ---------------------------------------

        inserted = batch_insert_students(records)

        st.success(f"{inserted} students imported successfully.")

        st.warning(f"{skipped} rows skipped (duplicates or errors).")


def batch_insert_students(records, batch_size=1000):

    total = len(records)
    inserted = 0

    for i in range(0, total, batch_size):

        batch = records[i:i + batch_size]

        try:
            supabase_admin.table("users").insert(batch).execute()
            inserted += len(batch)

        except Exception as e:
            print("Batch failed:", e)

    return inserted