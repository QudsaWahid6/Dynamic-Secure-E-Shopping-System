from flask import Flask, jsonify, request, g, send_from_directory
from flask_cors import CORS
from routes.store_routes import store_bp
from routes.product_routes import product_bp
from routes.user_routes import user_bp
from routes.order_routes import order_bp
from routes.theme_routes import theme_bp
from routes.admin_routes import admin_bp
from routes.wishlist_routes import wishlist_bp
from routes.product_category_routes import product_category_bp
from routes.chat_routes import chat_bp
from services.gemini_service import generate_theme
from services.supabase_service import supabase_client
from security import create_security_record, verify_chain
from auth import protected
import bcrypt
import jwt
import datetime
import os
from pathlib import Path
import webbrowser
import threading

SECRET_KEY = os.getenv("SECRET_KEY", "dev_secret_key_123")
FRONTEND_DIR = str(Path(__file__).resolve().parents[2] / "frontend")

app = Flask(__name__, static_folder=None)
CORS(app, supports_credentials=True)

app.register_blueprint(store_bp)
app.register_blueprint(product_bp)
app.register_blueprint(user_bp)
app.register_blueprint(order_bp)
app.register_blueprint(theme_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(wishlist_bp)
app.register_blueprint(product_category_bp)
app.register_blueprint(chat_bp)

@app.route("/")
def home():
    return {"message": "FYP Backend Running"}


@app.route("/health")
def health():
    return {"status": "ok"}


@app.route("/auth", methods=["GET"])
@protected
def test_auth():
    return jsonify({
        "success": True,
        "message": "Authenticated",
        "user": {
            "id": g.user["id"],
            "name": g.user.get("name"),
            "email": g.user.get("email"),
            "role": g.user.get("role"),
            "profile_image_url": g.user.get("profile_image_url"),
        },
    })


@app.route("/generate-theme", methods=["POST", "GET"])
def test_theme():
    try:
        if request.method == "POST":
            data = request.get_json() or {}
            result = generate_theme(
                data.get("business_type", "fashion"),
                region=data.get("region", ""),
                style=data.get("style", "modern"),
                aesthetic=data.get("aesthetic", ""),
            )
        else:
            result = generate_theme("fashion")
        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/signup", methods=["POST"])
def signup():
    try:
        data = request.get_json() or {}
        name = data.get("name")
        email = data.get("email")
        password = data.get("password")
        role = data.get("role", "customer")

        if role not in ("customer", "store_owner", "super_admin"):
            role = "customer"

        # store owners must be approved by a super admin before they can log in
        initial_status = "pending" if role == "store_owner" else "active"

        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        supabase_client.table("users").insert({
            "name": name,
            "email": email,
            "password": hashed_password.decode("utf-8"),
            "role": role,
            "status": initial_status,
        }).execute()

        msg = (
            "Your store owner account has been created and is pending approval by an admin."
            if role == "store_owner"
            else "User created successfully"
        )
        return jsonify({"success": True, "message": msg})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No JSON body found"}), 400

        email = data.get("email")
        password = data.get("password")
        if not email or not password:
            return jsonify({"success": False, "error": "Email or password missing"}), 400

        user = supabase_client.table("users").select("*").eq("email", email).execute()
        if not user.data:
            return jsonify({"success": False, "error": "User not found"}), 404

        db_user = user.data[0]
        if not db_user.get("password"):
            return jsonify({"success": False, "error": "Database password missing"}), 500

        if not bcrypt.checkpw(password.encode("utf-8"), db_user["password"].encode("utf-8")):
            return jsonify({"success": False, "error": "Invalid password"}), 401

        if db_user["role"] == "store_owner" and db_user.get("status") != "active":
            return jsonify({
                "success": False,
                "pending_approval": True,
                "error": "Your store owner account is pending approval by an admin."
            }), 403

        token = jwt.encode({
            "user_id": db_user["id"],
            "email": db_user["email"],
            "role": db_user["role"],
            "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24),
        }, SECRET_KEY, algorithm="HS256")

# #################security log 2
        create_security_record(
            event_type="USER_LOGIN",
            event_data={"email": email},
            user_id=db_user["id"],
            ip_address=request.remote_addr
        )     

        return jsonify({
            "success": True,
            "token": token,
            "user": {
                "id": db_user["id"],
                "name": db_user.get("name") or db_user["email"].split("@")[0],
                "email": db_user["email"],
                "role": db_user["role"],
                "profile_image_url": db_user.get("profile_image_url"),
            },
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    

# ############## security log 3
@app.route("/verify-chain", methods=["GET"])
def verify_blockchain():
    is_valid, message = verify_chain()

    return jsonify({
        "success": is_valid,
        "message": message
    })

@app.route("/categories", methods=["GET"])
def categories():
    try:
        result = supabase_client.table("categories").select("*").execute()
        return jsonify({"success": True, "data": result.data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/")
def serve_index():
    return send_from_directory(FRONTEND_DIR, "login.html")

@app.route("/<path:filename>")
def serve_frontend(filename):
    # if a real file exists in frontend/, always serve it first
    filepath = Path(FRONTEND_DIR) / filename
    if filepath.exists() and filepath.is_file():
        return send_from_directory(FRONTEND_DIR, filename)

    API_PREFIXES = ("product-categories", "products/", "stores", "orders", "users", "themes", "admin", "wishlist", "auth", "dashboard", "health", "categories", "generate-theme", "verify-chain")
    if filename.startswith(API_PREFIXES):
        return jsonify({"error": "Not found"}), 404

    return jsonify({"error": "Not found"}), 404
# @app.route("/<path:filename>")
# def serve_frontend(filename):
#     # API_PREFIXES = ("product-categories", "products/", "stores", "orders", "users", "themes", "admin", "wishlist", "login", "signup", "auth", "dashboard", "health", "categories", "generate-theme")
#     API_PREFIXES = ("product-categories", "products/", "stores", "orders", "users", "themes", "admin", "wishlist", "auth", "dashboard", "health", "categories", "generate-theme","verify-chain")
#     if filename.startswith(API_PREFIXES):
#         return jsonify({"error": "Not found"}), 404
#     filepath = Path(FRONTEND_DIR) / filename
#     if filepath.exists() and filepath.is_file():
#         return send_from_directory(FRONTEND_DIR, filename)
#     return jsonify({"error": "Not found"}), 404

def _open_browser():
    webbrowser.open("http://127.0.0.1:5000/index.html")


if __name__ == "__main__":
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        threading.Timer(1.5, _open_browser).start()
    app.run(host="0.0.0.0", port=5000, debug=True)

