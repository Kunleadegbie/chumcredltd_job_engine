import json
from datetime import datetime, timezone

def log_event(supabase_admin, user: dict | None, event_type: str, severity: str = "info", **metadata):
    try:
        payload = {
            "actor_user_id": (user or {}).get("id"),
            "actor_email": (user or {}).get("email"),
            "event_type": event_type,
            "severity": severity,
            "metadata": metadata or {},
        }
        supabase_admin.table("security_events").insert(payload).execute()
    except Exception:
        # logging must never break the app
        pass