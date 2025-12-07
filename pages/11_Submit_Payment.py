import streamlit as st
from components.sidebar import render_sidebar
from services.supabase_client import supabase_rest_insert

st.set_page_config(page_title="Submit Payment | Chumcred", page_icon="💸")

# ----------------------------------------------------
# AUTH CHECK
# ----------------------------------------------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state.get("user")
if not isinstance(user, dict):
    st.session_state.authenticated = False
    st.session_state.user = None
    st.switch_page("app.py")

user_id = user.get("id")

render_sidebar()

# ----------------------------------------------------
# SELECTED PLAN
# ----------------------------------------------------
selected = st.session_state.get("selected_plan")

if not selected:
    st.error("No plan selected. Please choose a plan first.")
    st.stop()

plan = selected["plan"]
amount = selected["amount"]
credits = selected["credits"]
days = selected["days"]

# ----------------------------------------------------
# PAGE UI
# ----------------------------------------------------
st.title("💸 Submit Payment")
st.write("Complete your subscription request.")
st.write("---")

st.markdown(f"""
### Selected Plan: **{plan}**
**Amount:** ₦{amount}  
**Credits:** {credits}  
**Duration:** {days} days  
""")

payment_ref = st.text_input("Enter Your Payment Reference")

if st.button("Submit Payment"):
    if not payment_ref.strip():
        st.warning("Please enter a valid payment reference.")
        st.stop()

    # Insert request
    supabase_rest_insert("payment_requests", {
        "user_id": user_id,
        "plan": plan,
        "amount": amount,
        "payment_reference": payment_ref,
        "credits": credits,
        "days": days,
        "status": "pending"
    })

    st.success("Payment submitted! Pending admin approval.")
    st.info("You will receive access once your payment is approved.")
    st.stop()
