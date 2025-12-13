# ==========================================================
#  Admin Revenue Dashboard — Full Option C Implementation
# ==========================================================

import streamlit as st
from datetime import datetime
from config.supabase_client import supabase

st.set_page_config(page_title="Admin – Revenue Dashboard", page_icon="💰", layout="wide")

# ------------------------------------------------------------
# AUTH CHECK
# ------------------------------------------------------------
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state.get("user")
if not user or user.get("role") != "admin":
    st.error("Access denied. Admin only.")
    st.stop()

admin_name = user.get("full_name", "Admin")


# ------------------------------------------------------------
# FETCH PAYMENTS
# ------------------------------------------------------------
def fetch_payments():
    try:
        res = supabase.table("subscription_payments").select("*").order("paid_on", desc=True).execute()
        return res.data or []
    except Exception as e:
        st.error(f"Error fetching payments: {e}")
        return []


def approve_payment(payment_id, admin_name):
    try:
        supabase.table("subscription_payments").update({
            "approved": True,
            "approved_by": admin_name,
            "approval_date": datetime.utcnow().isoformat()
        }).eq("id", payment_id).execute()
        return True
    except Exception as e:
        st.error(f"Approval failed: {e}")
        return False


# ------------------------------------------------------------
# LOAD DATA
# ------------------------------------------------------------
payments = fetch_payments()

pending = [p for p in payments if not p.get("approved")]
approved = [p for p in payments if p.get("approved")]


# ------------------------------------------------------------
# SUMMARY CARDS
# ------------------------------------------------------------
total_revenue = sum(p.get("amount", 0) for p in approved)
total_payments = len(payments)
pending_count = len(pending)
approved_count = len(approved)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Revenue (₦)", f"₦{total_revenue:,.0f}")

with col2:
    st.metric("Total Payments", total_payments)

with col3:
    st.metric("Approved", approved_count)

with col4:
    st.metric("Pending Approval", pending_count)

st.write("---")


# ------------------------------------------------------------
# FILTER TABS
# ------------------------------------------------------------
tab_all, tab_pending, tab_approved = st.tabs(["📄 All Payments", "⏳ Pending", "✅ Approved"])


# ------------------------------------------------------------
# DISPLAY TABLE FUNCTION
# ------------------------------------------------------------
def display_table(data, show_approve=False):
    if not data:
        st.info("No records found.")
        return

    for p in data:
        st.markdown(f"""
        ### 🧾 Payment ID: `{p.get('id')}`
        **User ID:** {p.get('user_id')}  
        **Plan:** {p.get('plan')}  
        **Amount:** ₦{p.get('amount'):,.0f}  
        **Credits:** {p.get('credits')}  
        **Paid On:** {p.get('paid_on')}  
        **Approved:** {"✅ Yes" if p.get("approved") else "❌ No"}  
        """)

        if p.get("approved"):
            st.markdown(f"**Approved By:** {p.get('approved_by')} on {p.get('approval_date')}")
        else:
            if show_approve:
                if st.button(f"Approve Payment", key=f"approve_{p['id']}"):
                    if approve_payment(p["id"], admin_name):
                        st.success("Payment approved successfully!")
                        st.rerun()

        st.write("---")


# ------------------------------------------------------------
# ALL PAYMENTS TAB
# ------------------------------------------------------------
with tab_all:
    display_table(payments, show_approve=True)


# ------------------------------------------------------------
# PENDING TAB
# ------------------------------------------------------------
with tab_pending:
    display_table(pending, show_approve=True)


# ------------------------------------------------------------
# APPROVED TAB
# ------------------------------------------------------------
with tab_approved:
    display_table(approved, show_approve=False)


# ------------------------------------------------------------
# END
# ------------------------------------------------------------
st.caption("Chumcred Job Engine — Admin Revenue © 2025")
