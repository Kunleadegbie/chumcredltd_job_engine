import streamlit as st
from components.sidebar import show_sidebar
from services.supabase_client import supabase_rest_query, supabase_rest_update

# ===============================
# ACCESS CONTROL
# ===============================
if "user" not in st.session_state or not st.session_state.user:
    st.error("Access denied. Please log in as admin.")
    st.stop()

user = st.session_state.user
show_sidebar(user)

if user.get("role") != "admin":
    st.error("Only admin can view this page.")
    st.stop()

# ===============================
# PAGE HEADER
# ===============================
st.title("🛠 Admin Panel — Manage Activations & Credits")
st.write("---")

# ===============================
# FETCH ALL SUBSCRIPTIONS
# ===============================
subscriptions = supabase_rest_query("subscriptions")

if isinstance(subscriptions, dict) and "error" in subscriptions:
    st.error("Error loading subscriptions table")
    st.json(subscriptions)
    st.stop()

# ===============================
# PENDING ACTIVATION REQUESTS
# ===============================
st.subheader("📌 Pending Activation Requests")

pending = [s for s in subscriptions if s.get("status") == "pending"]

if not pending:
    st.info("No pending activation requests.")
else:
    for sub in pending:
        st.write("---")
        st.markdown(f"### {sub.get('full_name', 'Unknown User')}")
        st.write(f"📧 **Email:** {sub.get('email')}")
        st.write(f"📦 **Plan:** {sub.get('plan_name')}")
        st.write(f"💳 **Amount Paid:** ₦{sub.get('amount')}")
        st.write(f"🕒 **Requested:** {sub.get('created_at')}")

        # APPROVE BUTTON
        if st.button(f"Approve Activation — {sub['id']}", key=f"approve_{sub['id']}"):
            supabase_rest_update(
                "subscriptions",
                {"id": sub["id"]},
                {
                    "status": "active",
                    "credits": sub.get("credits", 0),
                }
            )
            st.success("Activation Approved Successfully!")
            st.rerun()

# ===============================
# ACTIVE SUBSCRIPTIONS LIST
# ===============================
st.subheader("🟢 Active Subscriptions")

active = [s for s in subscriptions if s.get("status") == "active"]

if not active:
    st.info("No active subscriptions.")
else:
    for sub in active:
        st.write("---")
        st.markdown(f"### {sub.get('full_name')} ({sub.get('email')})")
        st.write(f"🔥 **Credits Remaining:** {sub.get('credits', 0)}")
        st.write(f"⏳ **Expires:** {sub.get('expiry_date')}")

# ===============================
# EXPIRED SUBSCRIPTIONS LIST
# ===============================
st.subheader("🔴 Expired Subscriptions")

expired = [s for s in subscriptions if s.get("status") == "expired"]

if not expired:
    st.info("No expired subscriptions.")
else:
    for sub in expired:
        st.write("---")
        st.markdown(f"### {sub.get('full_name')} ({sub.get('email')})")
        st.write(f"❌ **Expired On:** {sub.get('expiry_date')}")
