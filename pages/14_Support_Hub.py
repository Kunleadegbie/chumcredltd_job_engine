# ============================================================
# pages/14_Support_Hub.py — Help • Feedback • Testimonials (Combined)
# ============================================================

import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from components.ui import hide_streamlit_sidebar
from components.sidebar import render_sidebar
from services.utils import is_admin
from config.supabase_client import supabase_admin as supabase  # service role for safe admin ops


# ======================================================
# PAGE CONFIG
# ======================================================
st.set_page_config(page_title="Support Hub", page_icon="🆘", layout="wide")


# ======================================================
# HIDE STREAMLIT DEFAULT SIDEBAR + SHOW CUSTOM SIDEBAR
# ======================================================
hide_streamlit_sidebar()
st.session_state["_sidebar_rendered"] = False
render_sidebar()


# ======================================================
# AUTH CHECK
# ======================================================
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("app.py")
    st.stop()

user = st.session_state.get("user") or {}
user_id = user.get("id")
role = user.get("role", "user")

if not user_id:
    st.switch_page("app.py")
    st.stop()

is_admin_user = is_admin(user_id)


# ======================================================
# HELPERS
# ======================================================
TABLE = "support_feedback"

CATEGORY_LABELS = {
    "help": "Help / Support",
    "feedback": "Feedback / Suggestions",
    "testimonial": "Testimonial (for social proof)",
}

STATUS_BADGE = {
    "open": "🟢 OPEN",
    "replied": "🟡 REPLIED",
    "resolved": "✅ RESOLVED",
}


def sanitize_text(text: str) -> str:
    """Prevents Postgres \\u0000 (null byte) insertion errors."""
    if text is None:
        return ""
    return str(text).replace("\x00", "").strip()


def fmt_dt(val) -> str:
    if not val:
        return ""
    return str(val).replace("T", " ").replace("Z", "")


def fetch_my_tickets(uid: str):
    try:
        return (
            supabase.table(TABLE)
            .select("*")
            .eq("user_id", uid)
            .order("created_at", desc=True)
            .limit(500)
            .execute()
            .data
            or []
        )
    except Exception:
        return []


def fetch_all_tickets(status_filter="all", category_filter="all", search=""):
    q = supabase.table(TABLE).select("*").order("created_at", desc=True).limit(1000)

    if status_filter != "all":
        q = q.eq("status", status_filter)
    if category_filter != "all":
        q = q.eq("category", category_filter)

    search = sanitize_text(search)
    if search:
        # Try match name/email (best-effort)
        q = q.or_(f"user_email.ilike.%{search}%,user_name.ilike.%{search}%")

    try:
        return q.execute().data or []
    except Exception:
        return []


def insert_ticket(payload: dict):
    supabase.table(TABLE).insert(payload).execute()


def update_ticket(ticket_id: str, payload: dict):
    supabase.table(TABLE).update(payload).eq("id", ticket_id).execute()


# ======================================================
# PAGE HEADER
# ======================================================
st.title("🆘 Support Hub")
st.caption("Help • Feedback • Testimonials — send a message and get a response from Admin.")
st.divider()


# ======================================================
# USER VIEW (EVERYONE CAN SUBMIT)
# ======================================================
left, right = st.columns([1.05, 1.0], gap="large")

with left:
    st.subheader("✉️ Send a message")

    with st.form("support_hub_form", clear_on_submit=True):
        category = st.selectbox(
            "Category",
            options=list(CATEGORY_LABELS.keys()),
            format_func=lambda k: CATEGORY_LABELS.get(k, k),
        )

        subject = st.text_input("Subject", placeholder="e.g., I need help understanding my Match Score")
        message = st.text_area("Message", placeholder="Type your message clearly…", height=160)

        testimonial_public_ok = False
        if category == "testimonial":
            testimonial_public_ok = st.checkbox(
                "✅ I allow TalentIQ to feature this testimonial publicly (LinkedIn/website/marketing).",
                value=False,
            )

        submitted = st.form_submit_button("Send", use_container_width=True)

    if submitted:
        subject = sanitize_text(subject) or "General enquiry"
        message = sanitize_text(message)

        if not message:
            st.error("Please enter your message before sending.")
        else:
            payload = {
                "user_id": user_id,
                "user_name": sanitize_text(user.get("full_name") or user.get("username") or ""),
                "user_email": sanitize_text(user.get("email") or ""),
                "category": category,
                "subject": subject,
                "message": message,
                "status": "open",
                "testimonial_public_ok": bool(testimonial_public_ok),
                "testimonial_approved": False,
            }

            try:
                insert_ticket(payload)
                st.success("✅ Sent successfully. Admin will respond here.")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Failed to send message: {e}")

with right:
    st.subheader("📩 My messages")
    my_rows = fetch_my_tickets(user_id)

    if not my_rows:
        st.info("No messages yet.")
    else:
        for r in my_rows:
            tid = r.get("id")
            subj = r.get("subject") or "General enquiry"
            cat = r.get("category", "help")
            status = r.get("status", "open")
            created_at = fmt_dt(r.get("created_at"))

            badge = STATUS_BADGE.get(status, status.upper())
            cat_label = CATEGORY_LABELS.get(cat, cat)

            title = f"{cat_label} — {subj} — {badge} — {created_at}"

            with st.expander(title, expanded=False):
                st.markdown("**Your message:**")
                st.write(r.get("message", ""))

                st.markdown("---")

                reply = r.get("admin_reply")
                if reply:
                    st.markdown("**Admin reply:**")
                    st.write(reply)
                    if r.get("replied_at"):
                        st.caption(f"Replied at: {fmt_dt(r.get('replied_at'))}")
                else:
                    st.info("No reply yet.")

                # User can mark resolved (optional)
                if status != "resolved" and reply:
                    if st.button("✅ Mark as Resolved", key=f"resolve_{tid}", use_container_width=True):
                        try:
                            update_ticket(tid, {"status": "resolved"})
                            st.success("Marked as resolved.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed: {e}")


# ======================================================
# ADMIN VIEW (INBOX + REPLY + TESTIMONIAL CONTROLS)
# ======================================================
if is_admin_user:
    st.divider()
    st.header("🛡️ Admin Inbox")
    st.caption("Filter tickets, reply, resolve, and approve testimonials for marketing use.")

    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        status_filter = st.selectbox("Status", ["all", "open", "replied", "resolved"], index=1)
    with c2:
        category_filter = st.selectbox("Category", ["all", "help", "feedback", "testimonial"], index=0,
                                      format_func=lambda k: "All" if k == "all" else CATEGORY_LABELS.get(k, k))
    with c3:
        search = st.text_input("Search (name/email)", placeholder="e.g., kunle@gmail.com or Adekunle")

    rows = fetch_all_tickets(status_filter=status_filter, category_filter=category_filter, search=search)

    if not rows:
        st.info("No tickets match your filters.")
    else:
        # Select ticket
        options = []
        for r in rows:
            tid = r.get("id")
            cat_label = CATEGORY_LABELS.get(r.get("category", "help"), r.get("category", "help"))
            badge = STATUS_BADGE.get(r.get("status", "open"), r.get("status", "open"))
            who = (r.get("user_email") or r.get("user_name") or r.get("user_id") or "")[:45]
            subj = (r.get("subject") or "General")[:60]
            created = fmt_dt(r.get("created_at"))
            options.append((tid, f"{cat_label} | {badge} | {who} | {subj} | {created}"))

        selected_tid = st.selectbox(
            "Select a ticket",
            options=[x[0] for x in options],
            format_func=lambda tid: dict(options).get(tid, str(tid)),
        )

        selected = next((r for r in rows if r.get("id") == selected_tid), None)

        if not selected:
            st.error("Could not load selected ticket.")
        else:
            tid = selected.get("id")
            st.markdown(f"### Ticket: `{tid}`")

            st.write(f"**User:** {selected.get('user_name','')}  ")
            st.write(f"**Email:** {selected.get('user_email','')}  ")
            st.write(f"**Category:** {CATEGORY_LABELS.get(selected.get('category','help'), selected.get('category','help'))}")
            st.write(f"**Status:** {selected.get('status','open')}")
            st.write(f"**Created:** {fmt_dt(selected.get('created_at'))}")

            st.markdown("**Message:**")
            st.write(selected.get("message", ""))

            st.markdown("---")

            existing_reply = selected.get("admin_reply") or ""
            reply = st.text_area("Admin reply", value=existing_reply, height=140, key=f"reply_{tid}")

            resolve = st.checkbox("Mark as resolved", value=False, key=f"resolve_chk_{tid}")

            # Testimonial controls
            if selected.get("category") == "testimonial":
                st.divider()
                st.subheader("⭐ Testimonial Controls")

                public_ok = bool(selected.get("testimonial_public_ok"))
                approved = bool(selected.get("testimonial_approved"))

                st.write(f"**User allowed public use:** {'✅ Yes' if public_ok else '❌ No'}")

                approved_new = st.checkbox(
                    "✅ Approve this testimonial for marketing (LinkedIn/website/social proof)",
                    value=approved,
                    key=f"approved_{tid}",
                )

                # Copy-ready block
                st.markdown("**Copy-ready testimonial (you can copy/paste):**")
                who = selected.get("user_name") or selected.get("user_email") or "TalentIQ user"
                copy_text = f"“{sanitize_text(selected.get('message',''))}”\n— {who}"
                st.code(copy_text)

            colA, colB = st.columns(2)
            with colA:
                if st.button("Send Reply", use_container_width=True, key=f"send_{tid}"):
                    if not sanitize_text(reply):
                        st.error("Reply cannot be empty.")
                    else:
                        try:
                            payload = {
                                "admin_reply": sanitize_text(reply),
                                "status": "resolved" if resolve else "replied",
                                "replied_at": fmt_dt(st.session_state.get("_now_iso")) or None,
                                "replied_by": user_id,
                            }

                            # Ensure replied_at has a proper timestamp
                            payload["replied_at"] = None  # let DB keep null if you prefer
                            # But we can set it explicitly in app:
                            payload["replied_at"] = st.session_state.get("_iso_now") or None

                            # safer: set replied_at to now using python string
                            import datetime as _dt
                            payload["replied_at"] = _dt.datetime.utcnow().isoformat() + "Z"

                            if selected.get("category") == "testimonial":
                                payload["testimonial_approved"] = bool(st.session_state.get(f"approved_{tid}", False))

                            update_ticket(tid, payload)
                            st.success("✅ Reply sent.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Failed: {e}")

            with colB:
                if st.button("Mark Resolved (no reply)", use_container_width=True, key=f"resolve_only_{tid}"):
                    try:
                        update_ticket(tid, {"status": "resolved"})
                        st.success("✅ Ticket resolved.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Failed: {e}")


st.divider()
st.caption("Chumcred TalentIQ © 2025")
