from flask import Blueprint, request, jsonify, g
from auth import protected, role_required
from services.supabase_service import supabase_client
from services.gemini_service import suggest_product_category

product_category_bp = Blueprint("product_category_bp", __name__, url_prefix="")

def _owner_store_id():
    store = (
        supabase_client.table("stores")
        .select("id")
        .eq("user_id", g.user["id"])
        .execute()
    )
    if not store.data:
        return None
    return store.data[0]["id"]


@product_category_bp.route("/product-categories", methods=["GET"])
def get_product_categories():
    try:
        store_id = request.args.get("store_id")
        if not store_id:
            return jsonify({"success": False, "error": "store_id is required"}), 400

        response = (
            supabase_client.table("product_categories")
            .select("*")
            .eq("store_id", store_id)
            .order("name")
            .execute()
        )
        return jsonify({"success": True, "data": response.data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@product_category_bp.route("/product-categories", methods=["POST"])
@role_required("store_owner", "super_admin")
def add_product_category():
    try:
        data = request.get_json() or {}
        name = (data.get("name") or "").strip()
        if not name:
            return jsonify({"success": False, "error": "Category name is required"}), 400

        store_id = data.get("store_id") or _owner_store_id()
        if not store_id:
            return jsonify({"success": False, "error": "No store found for user"}), 400

        existing = (
            supabase_client.table("product_categories")
            .select("*")
            .eq("store_id", store_id)
            .execute()
        )
        for row in existing.data or []:
            if row["name"].strip().lower() == name.lower():
                return jsonify({"success": True, "data": row, "message": "Category already exists"})

        response = (
            supabase_client.table("product_categories")
            .insert({"store_id": store_id, "name": name})
            .execute()
        )
        return jsonify({"success": True, "data": response.data[0] if response.data else None})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@product_category_bp.route("/product-categories/<category_id>", methods=["DELETE"])
@role_required("store_owner", "super_admin")
def delete_product_category(category_id):
    try:
        store_id = _owner_store_id()
        existing = (
            supabase_client.table("product_categories")
            .select("*")
            .eq("id", category_id)
            .execute()
        )
        if not existing.data:
            return jsonify({"success": False, "message": "Category not found"}), 404

        if g.user.get("role") == "store_owner" and existing.data[0].get("store_id") != store_id:
            return jsonify({"success": False, "message": "Unauthorized"}), 403

        category_name = existing.data[0]["name"]
        cat_store_id = existing.data[0]["store_id"]
        in_use = (
            supabase_client.table("products")
            .select("id")
            .eq("store_id", cat_store_id)
            .eq("category", category_name)
            .execute()
        )
        if in_use.data:
            return jsonify({
                "success": False,
                "error": f'Cannot delete "{category_name}" — {len(in_use.data)} product(s) are using it. Reassign them first.'
            }), 400

        supabase_client.table("product_categories").delete().eq("id", category_id).execute()
        return jsonify({"success": True, "message": "Category deleted"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@product_category_bp.route("/products/suggest-category", methods=["POST"])
@role_required("store_owner", "super_admin")
def suggest_category():
    try:
        data = request.get_json() or {}
        name = (data.get("name") or "").strip()
        description = (data.get("description") or "").strip()
        if not name and not description:
            return jsonify({"success": False, "error": "Product name or description is required"}), 400

        store_id = data.get("store_id") or _owner_store_id()
        existing_names = []
        if store_id:
            existing = (
                supabase_client.table("product_categories")
                .select("name")
                .eq("store_id", store_id)
                .execute()
            )
            existing_names = [row["name"] for row in (existing.data or [])]

        suggestion = suggest_product_category(name, description, existing_names)
        return jsonify({"success": True, "data": suggestion})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500