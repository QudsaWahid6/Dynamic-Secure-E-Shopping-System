import os
import jwt
from functools import wraps
from flask import jsonify, request, g
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret_key_123")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def verify_token(token):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None
    except Exception:
        return None


def protected(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"success": False, "message": "Missing token"}), 401

        token = auth_header.replace("Bearer ", "").strip()
        payload = verify_token(token)
        if not payload:
            return jsonify({"success": False, "message": "Invalid or expired token"}), 401

        user_id = payload.get("user_id")
        if not user_id:
            return jsonify({"success": False, "message": "Invalid user in token"}), 401

        result = supabase.table("users").select("*").eq("id", user_id).execute()
        if not result.data:
            return jsonify({"success": False, "message": "User not found"}), 401

        g.user = result.data[0]
        g.token_payload = payload
        return f(*args, **kwargs)

    return decorated


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        @protected
        def wrapped(*args, **kwargs):
            if g.user.get("role") not in roles:
                return jsonify({"success": False, "message": "Unauthorized access"}), 403
            return f(*args, **kwargs)
        return wrapped
    return decorator
