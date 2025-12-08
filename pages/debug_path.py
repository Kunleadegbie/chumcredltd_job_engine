import os, sys
import streamlit as st

st.write("### Current Working Directory:")
st.write(os.getcwd())

st.write("### sys.path:")
st.write(sys.path)

st.write("### Files in Root:")
st.write(os.listdir("."))

st.write("### Files in services/:")
try:
    st.write(os.listdir("./services"))
except Exception as e:
    st.write("services not found:", e)

st.write("### Files in components/:")
try:
    st.write(os.listdir("./components"))
except Exception as e:
    st.write("components not found:", e)
