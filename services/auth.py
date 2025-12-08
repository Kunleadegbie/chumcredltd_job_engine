from services.supabase_client import supabase

def login_user(email, password):
    try:
        res = supabase.table("users").select("*").eq("email", email).eq("password", password).single().execute()
        return res.data
    except:
        return None


def register_user(full_name, email, password):
    try:
        exists = supabase.table("users").select("id").eq("email", email).execute()
        if exists.data:
            return False, "Email already exists."

        supabase.table("users").insert({
            "full_name": full_name,
            "email": email,
            "password": password,
            "role": "user"
        }).execute()

        return True, "Registration successful!"
    except Exception as e:
        return False, str(e)
