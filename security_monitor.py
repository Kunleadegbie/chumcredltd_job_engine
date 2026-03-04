from datetime import datetime, timezone, timedelta

since = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
events = (
    supabase_admin.table("security_events")
    .select("created_at,event_type,severity,actor_email,metadata")
    .gte("created_at", since)
    .order("created_at", desc=True)
    .limit(500)
    .execute()
    .data
    or []
)

st.dataframe(events, use_container_width=True)