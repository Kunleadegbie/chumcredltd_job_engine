from config.supabase_client import supabase

# ---------------------------------------
# LOGIN USER
# ---------------------------------------
def login_user(email, password):
    try:
        response = (
            supabase.table("users")
            .select("*")
            .eq("email", email)
            .eq("password", password)
            .single()
            .execute()
        )

        if response.data:
            print("LOGIN SUCCESS:", response.data)
            return response.data

        print("LOGIN FAILED: No matching user found")
        return None

    except Exception as e:
        print("Login Error:", e)
        return None


# ---------------------------------------
# REGISTER USER
# ---------------------------------------
def register_user(full_name, email, password):
    try:
        data = {
            "full_name": full_name,
            "email": email,
            "password": password,
            "is_active": True,
        }

        response = supabase.table("users").insert(data).execute()

        return True, "Account created successfully!"

    except Exception as e:
        print("Registration Error:", e)
        return False, f"Registration failed: {e}"
