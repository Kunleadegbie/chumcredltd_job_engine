# ==========================================================
#  Admin Revenue Dashboard — Full Option C Implementation
# ==========================================================

import streamlit as st
from datetime import datetime
from config.supabase_client import supabase

# ====================================================
# PAGE CONFIG
# ====================================================
st.set_page_config(page_title="Admin – Payments & Revenue", page_icon="💰", layout="wide")

# ====================================================
# AUTH CHECK (ADMIN ONLY)
# ====================================================
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")

user = st.session_state.get("user")

if not user:
    st.error("Session expired. Please log in again.")
    st.switch_page("app.py")
    st.stop()

# Only admin should view this page
if user.get("role") != "admin":
    st.error("Access denied. Admins only.")
    st.stop()

admin_name = user.get("full_name", "Admin")


# ====================================================
# HELPER FUNCTIONS
# ====================================================
def get_payments():
    try:
        res = supabase.table("subscription_payments").select("*").order("paid_on", desc=True).execute()
        return res.data or []
    except Exception as e:
        st.error(f"Error fetching payments: {e}")
        return []


def approve_payment(payment_id, approved_by):
    try:
        supabase.table("subscription_payments").update({
            "approved": True,
            "approved_by": approved_by,
            "approval_date": datetime.utcnow().isoformat()
        }).eq("id", payment_id).execute()
        return True
    except Exception as e:
        st.error(f"Approval failed: {e}")
        return False


# ====================================================
# DISPLAY A PAYMENT BLOCK
# ====================================================
def display_payment_block(payment, show_approve=False, prefix=""):
    st.markdown(f"""
    ### 🧾 Payment ID: `{payment.get('id')}`
    **User ID:** {payment.get('user_id')}  
    **Plan:** {payment.get('plan')}  
    **Amount:** ₦{payment.get('amount'):,.0f}  
    **Credits:** {payment.get('credits')}  
    **Paid On:** {payment.get('paid_on')}  
    **Approved:** {"✅ Yes" if payment.get("approved") else "❌ No"}  
    """)

    # If already approved, show metadata
    if payment.get("approved"):
        st.markdown(f"""
        **Approved By:** {payment.get('approved_by')}  
        **Approval Date:** {payment.get('approval_date')}
        """)
    else:
        # Approve button with unique key
        if show_approve:
            key = f"{prefix}_approve_{payment['id']}"
            if st.button("Approve Payment", key=key):
                if approve_payment(payment["id"], admin_name):
                    st.success("Payment approved successfully!")
                    st.rerun()

    st.write("---")


# ====================================================
# PAGE TITLE + DESCRIPTION
# ====================================================
st.title("💰 Admin Dashboard — Revenue & Payments")
st.write("Manage user subscription payments, approve pending transactions, and monitor revenue growth.")

payments = get_payments()

pending = [p for p in payments if not p.get("approved")]
approved = [p for p in payments if p.get("approved")]

# ====================================================
# TABS LAYOUT
# ====================================================
tab_all, tab_pending, tab_approved, tab_stats = st.tabs([
    "📦 All Payments",
    "⏳ Pending Approval",
    "✅ Approved Payments",
    "📈 Revenue Stats"
])

# ====================================================
# TAB 1 — ALL PAYMENTS
# ====================================================
with tab_all:
    st.subheader("📦 All Payments")
    if not payments:
        st.info("No payment records found.")
    else:
        for p in payments:
            display_payment_block(p, show_approve=not p.get("approved"), prefix="all")


# ====================================================
# TAB 2 — PENDING APPROVAL
# ====================================================
with tab_pending:
    st.subheader("⏳ Pending Payments")
    if not pending:
        st.success("No pending approvals.")
    else:
        for p in pending:
            display_payment_block(p, show_approve=True, prefix="pending")


# ====================================================
# TAB 3 — APPROVED PAYMENTS
# ====================================================
with tab_approved:
    st.subheader("✅ Approved Payments")
    if not approved:
        st.info("No approved transactions yet.")
    else:
        for p in approved:
            display_payment_block(p, show_approve=False, prefix="approved")


# ====================================================
# TAB 4 — REVENUE STATS
# ====================================================
with tab_stats:

    st.subheader("📈 Revenue Summary")

    if not approved:
        st.info("No approved transactions yet — revenue stats unavailable.")
    else:
        total_revenue = sum(p["amount"] for p in approved)
        total_credits = sum(p["credits"] for p in approved)

        st.metric("💰 Total Revenue (₦)", f"{total_revenue:,.0f}")
        st.metric("🎟️ Total Credits Issued", total_credits)

        # Monthly breakdown
        st.write("---")
        st.write("### 📅 Monthly Revenue Breakdown")

        monthly = {}
        for p in approved:
            month = p["paid_on"][:7]  # e.g. "2025-12"
            monthly.setdefault(month, 0)
            monthly[month] += p["amount"]

        for month, revenue in monthly.items():
            st.write(f"**{month}:** ₦{revenue:,.0f}")


# ------------------------------------------------------------
# END
# ------------------------------------------------------------
st.caption("Chumcred Job Engine — Admin Revenue © 2025")
