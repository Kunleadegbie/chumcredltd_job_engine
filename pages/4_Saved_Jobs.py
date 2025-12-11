import streamlit as st
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from components.sidebar import render_sidebar
from config.supabase_client import supabase

st.set_page_config(page_title="Saved Jobs", page_icon="💾")

# AUTH CHECK
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

render_sidebar()

user = st.session_state["user"]
user_id = user["id"]

st.title("💾 Saved Jobs")

jobs = supabase.table("saved_jobs").select("*").eq("user_id", user_id).execute().data or []

if not jobs:
    st.info("You have not saved any jobs yet.")
    st.stop()

for job in jobs:
    st.markdown(f"""
    ### **{job['title']}**
    **Company:** {job['company']}  
    🔗 [Apply Here]({job['apply_link']})  

    {job['description']}

    """)
    
    if st.button(f"❌ Remove", key=job["job_id"]):
        supabase.table("saved_jobs").delete().eq("job_id", job["job_id"]).execute()
        st.success("Job removed!")
        st.rerun()
    
    st.write("---")
