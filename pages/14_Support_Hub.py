# ============================================================
# pages/14_Support_Hub.py — Help • Feedback • Testimonials + Broadcasts
# ============================================================

import streamlit as st
import sys
import os
import datetime as _dt

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
BROADCAST_TABLE = "broadcast_messages"

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
    """Prevents Postgres \\u0000 (null byte) insertion errors and trims."""
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
        q = q.or_(f"user_email.ilike.%{search}%,user_name.ilike.%{search}%")

    try:
        return q.execute().data or []
    except Exception:
        return []


def insert_ticket(payload: dict):
    supabase.table(TABLE).insert(payload).execute()


def update_ticket(ticket_id: str, payload: dict):
    supabase.table(TABLE).update(payload).eq("id", ticket_id).execute()


# ---------------------------
# Broadcast helpers
# ---------------------------
def fetch_recent_broadcasts(limit: int = 20):
    try:
        return (
            supabase.table(BROADCAST_TABLE)
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
            .data
            or []
        )
    except Exception:
        return []


def create_broadcast(payload: dict):
    return supabase.table(BROADCAST_TABLE).insert(payload).execute()


def upload_broadcast_file(file) -> dict:
    """
    Uploads to Supabase Storage bucket 'broadcasts' and returns:
    {url, name, type}
    Requires bucket 'broadcasts' to exist (Public recommended).
    """
    if file is None:
        return {"url": None, "name": None, "type": None}

    filename = sanitize_text(getattr(file, "name", "attachment"))
    content_type = getattr(file, "type", None) or ""

    # Clean filename for storage path
    safe_name = "".join(c for c in filename if c.isalnum() or c in ("-", "_", ".", " ")).strip().replace(" ", "_")
    ts = _dt.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = f"broadcasts/{ts}_{safe_name}"

    # Read bytes
    data = file.read()

    # Upload (service role)
    try:
        supabase.storage.from_("broadcasts").upload(
            path=path,
            file=data,
            file_options={"content-type": content_type} if content_type else None,
        )
    except Exception as e:
        raise RuntimeError(f"Storage upload failed. Ensure bucket 'broadcasts' exists and is public. Error: {e}")

    # Public URL
    try:
        public_url = supabase.storage.from_("broadcasts").get_public_url(path)
    except Exception:
        public_url = None

    return {"url": public_url, "name": filename, "type": content_type}


# ======================================================
# PAGE HEADER
# ======================================================
st.title("🆘 Support Hub")
st.caption("Help • Feedback • Testimonials — send a message and get a response from Admin.")
st.divider()


# ======================================================
# BROADCASTS (VIEW FOR EVERYONE)
# ======================================================
st.subheader("📣 Announcements")
broadcasts = fetch_recent_broadcasts(limit=10)

if not broadcasts:
    st.info("No announcements yet.")
else:
    for b in broadcasts:
        title = b.get("title") or "Announcement"
        created = fmt_dt(b.get("created_at"))
        is_active = bool(b.get("is_active", True))
        status_badge = "🟢 ACTIVE" if is_active else "⚪ ARCHIVED"

        with st.expander(f"{status_badge} — {title} — {created}", expanded=False):
            st.write(b.get("message", ""))

            att_url = b.get("attachment_url")
            att_name = b.get("attachment_name") or "Attachment"
            att_type = (b.get("attachment_type") or "").lower()

            if att_url:
                if "video" in att_type or att_url.lower().endswith((".mp4", ".mov", ".webm")):
                    st.video(att_url)
                elif att_url.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                    st.image(att_url, use_container_width=True)
                else:
                    st.link_button(f"📎 Open: {att_name}", att_url)

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

                if status != "resolved" and reply:
                    if st.button("✅ Mark as Resolved", key=f"resolve_{tid}", use_container_width=True):
                        try:
                            update_ticket(tid, {"status": "resolved"})
                            st.success("Marked as resolved.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed: {e}")


# ======================================================
# ADMIN VIEW (INBOX + REPLY + TESTIMONIAL CONTROLS + BROADCAST CREATOR)
# ======================================================
if is_admin_user:
    st.divider()
    st.header("🛡️ Admin Panel")
    tabs = st.tabs(["📥 Inbox", "📣 Broadcast to All Users"])

    # ---------------------------
    # Inbox tab (unchanged logic)
    # ---------------------------
    with tabs[0]:
        st.caption("Filter tickets, reply, resolve, and approve testimonials for marketing use.")

        c1, c2, c3 = st.columns([1, 1, 2])
        with c1:
            status_filter = st.selectbox("Status", ["all", "open", "replied", "resolved"], index=1)
        with c2:
            category_filter = st.selectbox(
                "Category",
                ["all", "help", "feedback", "testimonial"],
                index=0,
                format_func=lambda k: "All" if k == "all" else CATEGORY_LABELS.get(k, k),
            )
        with c3:
            search = st.text_input("Search (name/email)", placeholder="e.g., kunle@gmail.com or Adekunle")

        rows = fetch_all_tickets(status_filter=status_filter, category_filter=category_filter, search=search)

        if not rows:
            st.info("No tickets match your filters.")
        else:
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

                    st.markdown("**Copy-ready testimonial:**")
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
                                    "replied_at": _dt.datetime.utcnow().isoformat() + "Z",
                                    "replied_by": user_id,
                                }

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

    # ---------------------------
    # Broadcast tab (new)
    # ---------------------------
    with tabs[1]:
        st.caption("Send an announcement to all users. It will pop up ONCE per user (tracked).")

        with st.form("broadcast_form", clear_on_submit=True):
            b_title = st.text_input("Title", placeholder="e.g., New Feature: InterviewIQ is live!")
            b_msg = st.text_area("Message", height=170, placeholder="Write the announcement message here…")

            b_file = st.file_uploader(
                "Optional attachment (PDF, image, or video)",
                type=["pdf", "png", "jpg", "jpeg", "webp", "mp4", "mov", "webm", "docx"],
            )

            b_active = st.checkbox("Active (show to users)", value=True)

            sent = st.form_submit_button("📣 Publish Broadcast", use_container_width=True)

        if sent:
            b_title = sanitize_text(b_title) or "Announcement"
            b_msg = sanitize_text(b_msg)

            if not b_msg:
                st.error("Message cannot be empty.")
            else:
                try:
                    att = {"url": None, "name": None, "type": None}
                    if b_file is not None:
                        att = upload_broadcast_file(b_file)

                    payload = {
                        "title": b_title,
                        "message": b_msg,
                        "attachment_url": att["url"],
                        "attachment_name": att["name"],
                        "attachment_type": att["type"],
                        "is_active": bool(b_active),
                        "created_by": user_id,
                    }

                    create_broadcast(payload)
                    st.success("✅ Broadcast published successfully.")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Failed to publish broadcast: {e}")

        # Admin can archive/unarchive existing broadcasts quickly
        st.divider()
        st.subheader("Manage broadcasts")
        b_rows = fetch_recent_broadcasts(limit=25)

        if not b_rows:
            st.info("No broadcasts yet.")
        else:
            for b in b_rows:
                bid = b.get("id")
                title = b.get("title") or "Announcement"
                is_active = bool(b.get("is_active", True))
                created = fmt_dt(b.get("created_at"))
                label = "🟢 Active" if is_active else "⚪ Archived"

                with st.expander(f"{label} — {title} — {created}", expanded=False):
                    st.write(b.get("message", ""))

                    c1, c2 = st.columns(2)
                    with c1:
                        if is_active:
                            if st.button("Archive", key=f"arch_{bid}", use_container_width=True):
                                try:
                                    supabase.table(BROADCAST_TABLE).update({"is_active": False}).eq("id", bid).execute()
                                    st.success("Archived.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Failed: {e}")
                        else:
                            if st.button("Re-activate", key=f"react_{bid}", use_container_width=True):
                                try:
                                    supabase.table(BROADCAST_TABLE).update({"is_active": True}).eq("id", bid).execute()
                                    st.success("Re-activated.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Failed: {e}")

                    with c2:
                        if st.button("Delete", key=f"del_{bid}", use_container_width=True):
                            try:
                                supabase.table(BROADCAST_TABLE).delete().eq("id", bid).execute()
                                st.success("Deleted.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Failed: {e}")


st.divider()
st.caption("Chumcred TalentIQ © 2025")
