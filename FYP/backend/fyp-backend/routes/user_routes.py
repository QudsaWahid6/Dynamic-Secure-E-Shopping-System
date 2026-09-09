from flask import Blueprint, jsonify, g, request
from auth import protected, role_required
from services.user_services import get_user_profile
from services.supabase_service import supabase_client

user_bp = Blueprint("user_bp", __name__)


@user_bp.route("/profile", methods=["GET"])
@protected
def profile():
    profile_data = get_user_profile(g.user["id"])
    if not profile_data:
        return jsonify({"success": False, "message": "Profile not found"}), 404
    return jsonify({"success": True, "profile": profile_data})


@user_bp.route("/profile", methods=["PUT"])
@protected
def update_profile():
    data = request.get_json() or {}
    allowed = {}
    if "name" in data:
        allowed["name"] = data["name"]
    if "profile_image_url" in data:
        allowed["profile_image_url"] = data["profile_image_url"]
    if "phone" in data:
        allowed["phone"] = data["phone"]
    if "address" in data:
        allowed["address"] = data["address"]
    if not allowed:
        return jsonify({"success": False, "message": "No valid fields to update"}), 400

    response = (
        supabase_client.table("users")
        .update(allowed)
        .eq("id", g.user["id"])
        .execute()
    )
    return jsonify({"success": True, "profile": response.data[0] if response.data else None})
@user_bp.route("/users/change-password", methods=["POST"])
@protected
def change_password():
    try:
        import bcrypt
        data = request.get_json() or {}
        current_password = data.get("current_password", "")
        new_password = data.get("new_password", "")

        if not current_password or not new_password:
            return jsonify({"success": False, "error": "Both fields required"}), 400
        if len(new_password) < 6:
            return jsonify({"success": False, "error": "Password must be at least 6 characters"}), 400

        user_res = (
            supabase_client.table("users")
            .select("password")
            .eq("id", g.user["id"])
            .execute()
        )
        if not user_res.data:
            return jsonify({"success": False, "error": "User not found"}), 404

        stored_hash = user_res.data[0]["password"]
        if not bcrypt.checkpw(current_password.encode("utf-8"), stored_hash.encode("utf-8")):
            return jsonify({"success": False, "error": "Current password is incorrect"}), 401

        new_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        supabase_client.table("users").update({"password": new_hash}).eq("id", g.user["id"]).execute()

        return jsonify({"success": True, "message": "Password changed successfully"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500