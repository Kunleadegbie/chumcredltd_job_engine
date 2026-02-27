# =========================================================
# UNLOCK USAGE SUMMARY
# =========================================================

CURRENT_YEAR = 2026

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