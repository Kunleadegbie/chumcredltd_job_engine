import os

print("DEBUG: SUPABASE_URL =", repr(os.getenv("SUPABASE_URL")))
print("DEBUG: SUPABASE_KEY =", repr(os.getenv("SUPABASE_KEY")))
print("DEBUG: OPENAI_API_KEY =", repr(os.getenv("OPENAI_API_KEY")))

from supabase import create_client
import streamlit as st

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
