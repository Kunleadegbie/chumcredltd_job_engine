from config.supabase_client import supabase

def login_user(email, password):
    print("\n=== LOGIN DEBUG START ===")
    print("Email received:", repr(email))
    print("Password received:", repr(password))

    try:
        response = (
            supabase.table("users")
            .select("*")
            .eq("email", email)
            .eq("password", password)
            .limit(1)
            .execute()
        )

        print("Supabase raw response:", response)

        # Supabase v2 returns .data
        data = response.data
        print("Parsed data:", data)

        if data and len(data) > 0:
            print("LOGIN SUCCESS:", data[0])
            print("=== LOGIN DEBUG END ===\n")
            return data[0]

        print("LOGIN FAILED: No user matched.")
        print("=== LOGIN DEBUG END ===\n")
        return None

    except Exception as e:
        print("LOGIN ERROR:", e)
        print("=== LOGIN DEBUG END ===\n")
        return None
