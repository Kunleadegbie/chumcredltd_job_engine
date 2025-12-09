from services.supabase_client import supabase

def login_user(email, password):
    print("=== DEBUG LOGIN START ===")
    print("Input email:", email)
    print("Input password:", password)

    try:
        # Fetch user by email first
        response = supabase.table("users").select("*").eq("email", email).execute()
        print("Supabase raw response:", response.data)

        if not response.data:
            print("DEBUG: No user found with this email.")
            return None

        user = response.data[0]
        print("DEBUG: Stored user row:", user)
        print("DEBUG: Stored password:", repr(user.get("password")))

        # Compare passwords
        if user.get("password") == password:
            print("DEBUG: Password MATCHED.")
            print("=== DEBUG LOGIN END ===")
            return user
        else:
            print("DEBUG: Password MISMATCH:", repr(user.get("password")), "!=", repr(password))
            print("=== DEBUG LOGIN END ===")
            return None

    except Exception as e:
        print("DEBUG ERROR:", e)
        print("=== DEBUG LOGIN END ===")
        return None
