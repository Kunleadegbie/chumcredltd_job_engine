import os
import csv
import secrets
import string
from datetime import datetime, timedelta, timezone

from supabase import create_client
from supabase.lib.client_options import ClientOptions

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

# input CSV (rename yours to this if possible)
INPUT_CSV = "talentiq_users.csv"  # put in scripts/
OUTPUT_CSV = "talentiq_temp_passwords_output.csv"  # generated in scripts/

FREEMIUM_CREDITS = 50
FREEMIUM_DAYS = 7


def utc_now():
    return datetime.now(timezone.utc)


def strong_temp_password(length: int = 14) -> str:
    # strong, URL-safe, includes mixed chars
    alphabet = string.ascii_letters + string.digits + "!@#$%&*_-"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def build_auth_email_to_id_map(sb_admin) -> dict:
    # list users in pages; safe for existing users
    email_to_id = {}
    page = 1
    per_page = 1000

    while True:
        resp = sb_admin.auth.admin.list_users(page=page, per_page=per_page)  # :contentReference[oaicite:1]{index=1}
        users = getattr(resp, "users", None) or (resp.get("users") if isinstance(resp, dict) else None) or []

        if not users:
            break

        for u in users:
            email = (getattr(u, "email", None) or u.get("email") or "").strip().lower()
            uid = getattr(u, "id", None) or u.get("id")
            if email and uid:
                email_to_id[email] = uid

        if len(users) < per_page:
            break
        page += 1

    return email_to_id


def upsert_users_app(sb_admin, user_id: str, email: str, full_name: str, role: str):
    payload = {
        "id": user_id,
        "email": email,
        "full_name": full_name or email,
        "role": (role or "user").strip().lower(),
        "is_active": True,
    }
    sb_admin.table("users_app").upsert(payload, on_conflict="id").execute()


def ensure_subscription(sb_admin, user_id: str):
    # Create freemium only if user has no subscription yet (won't overwrite paid plans)
    existing = sb_admin.table("subscriptions").select("user_id").eq("user_id", user_id).limit(1).execute()
    if existing.data:
        return

    now = utc_now()
    payload = {
        "user_id": user_id,
        "plan": "FREEMIUM",
        "credits": FREEMIUM_CREDITS,
        "amount": 0,
        "subscription_status": "active",
        "start_date": now.isoformat(),
        "end_date": (now + timedelta(days=FREEMIUM_DAYS)).isoformat(),
    }
    sb_admin.table("subscriptions").insert(payload).execute()


def main():
    sb_admin = create_client(
        SUPABASE_URL,
        SERVICE_ROLE_KEY,
        options=ClientOptions(auto_refresh_token=False, persist_session=False),
    )

    email_to_id = build_auth_email_to_id_map(sb_admin)

    out_rows = []
    ok = 0
    skipped_existing = 0
    failed = 0

    with open(INPUT_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    for r in rows:
        email = (r.get("email") or "").strip().lower()
        name = (r.get("name") or "").strip()
        role = (r.get("role") or "user").strip().lower()

        if not email:
            continue

        try:
            # If already exists in Auth, skip creating (don’t overwrite password)
            existing_id = email_to_id.get(email)
            if existing_id:
                # Still ensure users_app + subscription exist
                upsert_users_app(sb_admin, existing_id, email, name or email, role)
                ensure_subscription(sb_admin, existing_id)
                skipped_existing += 1
                continue

            temp_pw = strong_temp_password()

            # Create Auth user with password, auto-confirm email, and must-change flag
            resp = sb_admin.auth.admin.create_user(  # :contentReference[oaicite:2]{index=2}
                {
                    "email": email,
                    "password": temp_pw,
                    "email_confirm": True,
                    "user_metadata": {
                        "full_name": name or email,
                        "must_change_password": True,
                    },
                }
            )

            user = getattr(resp, "user", None) or (resp.get("user") if isinstance(resp, dict) else None)
            user_id = getattr(user, "id", None) or (user.get("id") if isinstance(user, dict) else None)

            if not user_id:
                raise RuntimeError("Create user succeeded but no user id returned.")

            # Provision app tables
            upsert_users_app(sb_admin, user_id, email, name or email, role)
            ensure_subscription(sb_admin, user_id)

            out_rows.append({"email": email, "name": name, "role": role, "temp_password": temp_pw})
            ok += 1
            email_to_id[email] = user_id

        except Exception as e:
            failed += 1
            out_rows.append({"email": email, "name": name, "role": role, "temp_password": "", "error": str(e)})

    # Write output credentials CSV (share securely!)
    fieldnames = ["email", "name", "role", "temp_password", "error"]
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in out_rows:
            if "error" not in row:
                row["error"] = ""
            w.writerow(row)

    print("===== DONE =====")
    print(f"Created new Auth users: {ok}")
    print(f"Existing Auth users provisioned (no password change): {skipped_existing}")
    print(f"Failed: {failed}")
    print(f"Output file: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
