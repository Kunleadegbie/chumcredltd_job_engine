
# ============================================================
# pages/15_Admin_Users.py — Admin Users (Registrations + Status + Activity)
# ============================================================

import streamlit as st
import pandas as pd
import sys
import os
from datetime import datetime, timezone, timedelta

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from components.ui import hide_streamlit_sidebar
from components.sidebar import render_sidebar
from services.utils import is_admin
from config.supabase_client import supabase_admin as supabase  # service-role client


# ======================================================
# PAGE CONFIG
# ======================================================
st.set_page_config(page_title="Admin — Users", page_icon="👥", layout="wide")

hide_streamlit_sidebar()
st.session_state["_sidebar_rendered"] = False
render_sidebar()

# ======================================================
# AUTH + ADMIN CHECK
# ======================================================
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")
    st.stop()

me = st.session_state.get("user") or {}
me_id = me.get("id")

if not me_id or not is_admin(me_id):
    st.error("Access denied — Admins only.")
    st.stop()


# ======================================================
# HELPERS
# ======================================================
def safe_dt(v):
    """
    Convert anything (string, datetime, pandas Timestamp) into a tz-aware UTC datetime.
    Returns None if parsing fails.
    """
    if v is None or v == "":
        return None

    try:
        # pandas Timestamp -> python datetime
        if hasattr(v, "to_pydatetime"):
            v = v.to_pydatetime()

        # already a datetime
        if isinstance(v, datetime):
            dt = v
        else:
            s = str(v).strip()
            # normalize common "Z" form
            s = s.replace("Z", "+00:00")
            dt = datetime.fromisoformat(s)

        # force tz-aware UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)

        return dt
    except Exception:
        return None


def pick_first(cols, candidates):
    for c in candidates:
        if c in cols:
            return c
    return None


def chunked(lst, n=150):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


# ======================================================
# LOAD USERS
# ======================================================
st.title("👥 Admin — Users")
st.caption("View all registered users, subscription status, and recent activity signals.")

try:
    users = (
        supabase.table("users")
        .select("*")
        .order("created_at", desc=True)
        .limit(5000)
        .execute()
        .data
        or []
    )
except Exception as e:
    st.error(f"Failed to load users table: {e}")
    st.stop()

if not users:
    st.info("No registered users found yet.")
    st.stop()

dfu = pd.DataFrame(users)

# Detect common columns (your schema may vary)
cols = set(dfu.columns)
col_id = pick_first(cols, ["id", "user_id"])
col_email = pick_first(cols, ["email", "user_email"])
col_name = pick_first(cols, ["full_name", "name", "username"])
col_role = pick_first(cols, ["role"])
col_created = pick_first(cols, ["created_at", "timestamp"])

if not col_id:
    st.error("Your users table has no obvious ID column (expected id).")
    st.stop()

# ======================================================
# LOAD SUBSCRIPTIONS (BATCH)
# ======================================================
user_ids = dfu[col_id].dropna().astype(str).tolist()

subs_rows = []
try:
    for batch in chunked(user_ids, 150):
        res = (
            supabase.table("subscriptions")
            .select("*")
            .in_("user_id", batch)
            .execute()
        )
        subs_rows.extend(res.data or [])
except Exception:
    subs_rows = []

dfs = pd.DataFrame(subs_rows) if subs_rows else pd.DataFrame([])

# Normalize subscription per user (pick the most recent by end_date/created_at if available)
sub_map = {}
if not dfs.empty and "user_id" in dfs.columns:
    rec_col = pick_first(set(dfs.columns), ["end_date", "updated_at", "created_at"])
    if rec_col:
        dfs["_rec"] = dfs[rec_col].apply(safe_dt)
        dfs = dfs.sort_values("_rec", ascending=False, na_position="last")

    for _, r in dfs.iterrows():
        uid = str(r.get("user_id"))
        if uid and uid not in sub_map:
            sub_map[uid] = r.to_dict()

# ======================================================
# LOAD ACTIVITY SIGNALS (OPTIONAL, SAFE)
# ======================================================
def load_activity_table(table, time_candidates=("created_at", "timestamp", "time"), user_candidates=("user_id",)):
    try:
        rows = (
            supabase.table(table)
            .select("*")
            .order("created_at", desc=True)
            .limit(5000)
            .execute()
            .data
            or []
        )
        if not rows:
            return {}

        dfa = pd.DataFrame(rows)
        tcol = pick_first(set(dfa.columns), list(time_candidates))
        ucol = pick_first(set(dfa.columns), list(user_candidates))
        if not tcol or not ucol:
            return {}

        dfa["_t"] = dfa[tcol].apply(safe_dt)
        dfa = dfa.dropna(subset=[ucol, "_t"])

        latest = dfa.sort_values("_t", ascending=False).drop_duplicates(subset=[ucol])
        return {str(r[ucol]): r["_t"] for _, r in latest.iterrows()}
    except Exception:
        return {}

activity_maps = [
    load_activity_table("ai_usage_logs"),
    load_activity_table("ai_outputs"),
    load_activity_table("saved_jobs"),
    load_activity_table("support_feedback"),
]

# Merge activity timestamps safely (always tz-aware UTC)
last_activity = {}
for amap in activity_maps:
    for uid, dtv in (amap or {}).items():
        dtv = safe_dt(dtv)
        if not dtv:
            continue
        prev = safe_dt(last_activity.get(uid))
        if prev is None or dtv > prev:
            last_activity[uid] = dtv

# ======================================================
# BUILD DISPLAY TABLE
# ======================================================
def compute_status(uid: str):
    sub = sub_map.get(uid)
    if not sub:
        return "inactive", None, 0, None

    status = sub.get("subscription_status") or sub.get("status") or "inactive"
    plan = sub.get("plan")
    credits = sub.get("credits") or 0
    end_date = safe_dt(sub.get("end_date"))

    now = datetime.now(timezone.utc)

    if end_date and end_date < now:
        return "inactive", plan, int(credits or 0), end_date

    if str(status).lower() == "active":
        return "active", plan, int(credits or 0), end_date

    return "inactive", plan, int(credits or 0), end_date


rows_out = []
for _, u in dfu.iterrows():
    uid = str(u.get(col_id))
    email = u.get(col_email) if col_email else ""
    name = u.get(col_name) if col_name else ""
    role = u.get(col_role) if col_role else "user"
    created = safe_dt(u.get(col_created)) if col_created else None

    acct_status, plan, credits, expiry = compute_status(uid)
    last_seen = safe_dt(last_activity.get(uid))

    rows_out.append(
        {
            "user_id": uid,
            "name": name,
            "email": email,
            "role": role,
            "registered": created.isoformat() if created else "",
            "subscription_status": acct_status,
            "plan": plan or "",
            "credits": int(credits or 0),
            "expires": expiry.isoformat() if expiry else "",
            "last_activity": last_seen.isoformat() if last_seen else "",
        }
    )

df = pd.DataFrame(rows_out)

# ======================================================
# FILTERS
# ======================================================
st.divider()
c1, c2, c3, c4 = st.columns([1, 1, 1, 2])

with c1:
    status_filter = st.selectbox("Filter: Status", ["all", "active", "inactive"], index=0)
with c2:
    role_filter = st.selectbox("Filter: Role", ["all", "admin", "user"], index=0)
with c3:
    inactivity_days = st.selectbox("Inactive if no activity in (days)", [7, 14, 30, 60, 90], index=2)
with c4:
    search = st.text_input("Search (name/email)", placeholder="e.g., kunle@gmail.com or Adekunle").strip().lower()

df_view = df.copy()

if status_filter != "all":
    df_view = df_view[df_view["subscription_status"] == status_filter]

if role_filter != "all":
    df_view = df_view[df_view["role"] == role_filter]

if search:
    df_view = df_view[
        df_view["email"].fillna("").str.lower().str.contains(search)
        | df_view["name"].fillna("").str.lower().str.contains(search)
    ]

# Inactivity filter (based on last_activity)
cutoff = datetime.now(timezone.utc) - timedelta(days=int(inactivity_days))

def is_inactive_last_seen(val):
    dtv = safe_dt(val)
    return (dtv is None) or (dtv < cutoff)

show_inactive_only = st.checkbox("Show only users with no recent activity", value=False)
if show_inactive_only:
    df_view = df_view[df_view["last_activity"].apply(is_inactive_last_seen)]

# ======================================================
# METRICS
# ======================================================
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Users", int(len(df)))
m2.metric("Active (Subscription)", int((df["subscription_status"] == "active").sum()))
m3.metric("Admins", int((df["role"] == "admin").sum()))
m4.metric("Shown (Filtered)", int(len(df_view)))

st.divider()

# ======================================================
# DISPLAY
# ======================================================
st.subheader("Users List")
st.dataframe(df_view.sort_values("registered", ascending=False), use_container_width=True)

st.download_button(
    "⬇️ Download Users CSV",
    data=df_view.to_csv(index=False).encode("utf-8"),
    file_name="talentiq_users.csv",
    mime="text/csv",
)

st.caption("Tip: Use the filters to find inactive users and reach out to understand why they didn’t activate.")
st.caption("Chumcred TalentIQ — Admin Analytics © 2025")
