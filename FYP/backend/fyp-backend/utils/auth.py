import jwt
import requests
from functools import wraps
from flask import request, jsonify

SUPABASE_JWKS_URL = "https://mabqofrtdrmuyhmfzoof.supabase.co/auth/v1/.well-known/jwks.json"


def get_public_keys():
    return requests.get(SUPABASE_JWKS_URL).json()["keys"]


def verify_token(token):
    try:
        headers = jwt.get_unverified_header(token)
        kid = headers["kid"]

        keys = get_public_keys()

        public_key = None
        for key in keys:
            if key["kid"] == kid:
                public_key = jwt.algorithms.ECAlgorithm.from_jwk(key)
                break

        if not public_key:
            return None

        decoded = jwt.decode(
            token,
            public_key,
            algorithms=["ES256"],
            audience="authenticated"
        )

        return decoded

    except Exception as e:
        print("JWT error:", e)
        return None


def protected(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization")

        if not auth:
            return jsonify({"message": "Missing token"}), 401

        try:
            token = auth.split(" ")[1]
        except:
            return jsonify({"message": "Invalid header format"}), 401

        user = verify_token(token)

        if not user:
            return jsonify({"message": "Invalid token"}), 401

        request.user = user
        return f(*args, **kwargs)

    return wrapper