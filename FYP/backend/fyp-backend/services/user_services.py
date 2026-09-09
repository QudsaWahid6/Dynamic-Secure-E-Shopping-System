from services.supabase_service import supabase_client


def get_user_profile(user_id):
    try:
        response = (
            supabase_client.table("users")
            .select("id, name, email, role, status, profile_image_url, store_id, created_at, phone, address")
            .eq("id", user_id)
            .execute()
        )
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        print("PROFILE ERROR:", e)
        return None
