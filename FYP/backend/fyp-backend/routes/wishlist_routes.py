from flask import Blueprint, request, jsonify, g
from auth import role_required
from services.supabase_service import supabase_client

wishlist_bp = Blueprint("wishlist_bp", __name__)


@wishlist_bp.route("/wishlist", methods=["GET"])
@role_required("customer")
def get_wishlist():
    try:
        result = (
            supabase_client.table("wishlists")
            .select("*, products(*)")
            .eq("user_id", g.user["id"])
            .execute()
        )
        return jsonify({"success": True, "data": result.data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@wishlist_bp.route("/wishlist", methods=["POST"])
@role_required("customer")
def add_wishlist():
    try:
        data = request.get_json() or {}
        product_id = data.get("product_id")
        if not product_id:
            return jsonify({"success": False, "message": "product_id required"}), 400

        existing = (
            supabase_client.table("wishlists")
            .select("*")
            .eq("user_id", g.user["id"])
            .eq("product_id", product_id)
            .execute()
        )
        if existing.data:
            return jsonify({"success": True, "data": existing.data[0], "message": "Already in wishlist"})

        response = supabase_client.table("wishlists").insert({
            "user_id": g.user["id"],
            "product_id": product_id,
        }).execute()
        return jsonify({"success": True, "data": response.data[0] if response.data else None})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@wishlist_bp.route("/wishlist/<item_id>", methods=["DELETE"])
@role_required("customer")
def remove_wishlist(item_id):
    try:
        supabase_client.table("wishlists").delete().eq("id", item_id).eq("user_id", g.user["id"]).execute()
        return jsonify({"success": True, "message": "Removed from wishlist"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
