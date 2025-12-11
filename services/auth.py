from config.supabase_client import supabase

def login_user(email, password):
    print("\n========== LOGIN DEBUG START ==========")
    print("Email received:", repr(email))
    print("Password received:", repr(password))

    try:
        # 1️⃣ Query Supabase for the user
        response = (
            supabase.table("users")
            .select("*")
            .eq("email", email)
            .execute()
        )

        print("Raw Supabase response:", response)
        print("Response data:", response.data)

        # 2️⃣ If no user found
        if not response.data:
            print("❌ No user found with that email")
            print("========== LOGIN DEBUG END ==========\n")
            return None

        user = response.data[0]
        print("User row fetched:", user)

        # 3️⃣ Check password
        if user.get("password") != password:
            print("❌ Password mismatch!")
            print("DB password:", repr(user.get("password")))
            print("Input password:", repr(password))
            print("========== LOGIN DEBUG END ==========\n")
            return None

        print("✅ LOGIN SUCCESS — USER AUTHENTICATED")
        print("========== LOGIN DEBUG END ==========\n")
        return user

    except Exception as e:
        print("🔥 LOGIN ERROR:", e)
        print("========== LOGIN DEBUG END ==========\n")
        return None
