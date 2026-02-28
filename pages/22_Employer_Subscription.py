# =========================================================
# RESOLVE EMPLOYER ID
# =========================================================

user = st.session_state.get("user") or {}
role = (user.get("role") or "").lower()
user_id = user.get("id")

employer_id = None

if role == "employer":
    emp = (
        supabase_admin
        .table("employers")
        .select("id")
        .eq("created_by", user_id)
        .limit(1)
        .execute()
        .data
    )
    employer_id = emp[0]["id"] if emp else None

elif role == "admin":
    employers = (
        supabase_admin
        .table("employers")
        .select("id,name")
        .order("name")
        .execute()
        .data or []
    )

    if employers:
        emp_map = {f"{e['name']} — {e['id']}": e["id"] for e in employers}
        selected = st.selectbox("Select Employer", list(emp_map.keys()))
        employer_id = emp_map[selected]

if not employer_id:
    st.error("Employer record not found.")
    st.stop()

# =========================================================
# UNLOCK USAGE SUMMARY
# =========================================================

CURRENT_YEAR = 2026

from config.supabase_client import supabase, supabase_admin

usage_res = supabase_admin.table("employer_unlock_usage") \
    .select("id") \
    .eq("employer_id", employer_id) \
    .eq("reporting_year", CURRENT_YEAR) \
    .execute()

used_unlocks = len(usage_res.data or [])

cap = subscription.get("unlock_cap", 0)

remaining_unlocks = max(cap - used_unlocks, 0)

st.subheader("🔓 Unlock Usage")

u1, u2, u3 = st.columns(3)
u1.metric("Unlocks Used", used_unlocks)
u2.metric("Unlock Cap", cap if cap < 999999 else "Unlimited")
u3.metric("Remaining Unlocks", remaining_unlocks if cap < 999999 else "Unlimited")