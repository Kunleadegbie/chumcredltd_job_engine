from datetime import datetime, timezone, timedelta

def rate_limited(supabase_admin, key: str, limit: int = 8, window_minutes: int = 15) -> bool:
    """
    Returns True if the key exceeded limit within the window.
    """
    try:
        window_start = (datetime.now(timezone.utc) - timedelta(minutes=window_minutes)).isoformat()

        recent = (
            supabase_admin.table("security_rate_limits")
            .select("id,count,created_at")
            .eq("key", key)
            .gte("created_at", window_start)
            .execute()
            .data
            or []
        )
        total = sum(int(r.get("count") or 0) for r in recent)
        if total >= limit:
            return True

        supabase_admin.table("security_rate_limits").insert({"key": key, "count": 1}).execute()
        return False
    except Exception:
        # fail-open to avoid blocking legit users if DB hiccups
        return False