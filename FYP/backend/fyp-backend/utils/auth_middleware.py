import requests
from functools import wraps
from flask import request, jsonify

SUPABASE_URL = "https://mabqofrtdrmuyhmfzoof.supabase.co"


def verify_token(token):
    """
    Validates Supabase JWT by calling Supabase Auth API
    (Correct method for ES256 projects)
    """
    try:
        res = requests.get(
            f"{SUPABASE_URL}/auth/v1/user",
            headers={
                "Authorization": f"Bearer {token}",
                "apikey": request.headers.get("apikey", "")
            }
        )

        if res.status_code != 200:
            return None

        return res.json()

    except Exception:
        return None


def protected(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return jsonify({
                "success": False,
                "message": "Missing Authorization header"
            }), 401

        try:
            token = auth_header.split(" ")[1]  # Bearer <token>
        except:
            return jsonify({
                "success": False,
                "message": "Invalid token format"
            }), 401

        user = verify_token(token)

        if not user:
            return jsonify({
                "success": False,
                "message": "Invalid or expired token"
            }), 401

        # attach user to request context
        request.user = user

        return f(*args, **kwargs)

    return decorated