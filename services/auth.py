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


def register_user(full_name, email, password):
    print("\n=== REGISTER DEBUG START ===")
    print("Full Name:", repr(full_name))
    print("Email:", repr(email))
    print("Password:", repr(password))

    try:
        # Check if email already exists
        exists = (
            supabase.table("users")
            .select("id")
            .eq("email", email)
            .execute()
        )

        print("Existing user check:", exists.data)

        if exists.data:
            print("REGISTER FAILED: Email already exists.")
            print("=== REGISTER DEBUG END ===\n")
            return False, "Email already registered."

        # Create new user
        response = (
            supabase.table("users")
            .insert({
                "full_name": full_name,
                "email": email,
                "password": password,
                "role": "user",
                "status": "active",
                "is_active": True
            })
            .execute()
        )

        print("Insert response:", response.data)
        print("REGISTER SUCCESS")
        print("=== REGISTER DEBUG END ===\n")
        return True, "Account created successfully!"

    except Exception as e:
        print("REGISTER ERROR:", e)
        print("=== REGISTER DEBUG END ===\n")
        return False, "Registration failed due to an error."

