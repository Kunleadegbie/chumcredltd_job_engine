import streamlit as st
from components.sidebar import render_sidebar
from config.supabase_client import supabase

# -------------------------------
# AUTH CHECK
# -------------------------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state["user"]
user_id = user["id"]

st.set_page_config(page_title="Settings", page_icon="⚙️")
st.title("⚙️ User Settings")

render_sidebar()

# -------------------------------
# LOAD USER SETTINGS OR STATS
# (Using user_stats for now based on your choice)
# -------------------------------

try:
    res = supabase.table("user_stats").select("*").eq("user_id", user_id).execute()
    user_data = res.data[0] if res.data else None

except Exception as e:
    st.error(f"Error loading settings: {e}")
    st.stop()

if not user_data:
    st.info("No settings or stats found for this user.")
    st.stop()


# -------------------------------
# DISPLAY SETTINGS / STATS
# -------------------------------
st.subheader("📊 User Stats")

st.write(f"**Total Jobs Viewed:** {user_data.get('jobs_viewed', 0)}")
st.write(f"**Total Jobs Saved:** {user_data.get('jobs_saved', 0)}")
st.write(f"**Total Searches Made:** {user_data.get('searches_made', 0)}")

st.write("---")
st.success("Settings page loaded successfully.")


# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------
st.caption("Chumcred Job Engine — Admin Analytics © 2025")

