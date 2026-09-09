from flask import Blueprint, request, jsonify, g
from auth import protected, role_required
from services.supabase_service import supabase_client

product_bp = Blueprint("product_bp", __name__)


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


@product_bp.route("/products", methods=["GET"])
def get_products():
    try:
        store_id = request.args.get("store_id")
        search = request.args.get("search", "").strip()
        category = request.args.get("category", "").strip()
        page = max(int(request.args.get("page", 1)), 1)
        limit = min(max(int(request.args.get("limit", 20)), 1), 100)
        offset = (page - 1) * limit

        query = supabase_client.table("products").select("*")
        if store_id:
            query = query.eq("store_id", store_id)
        if category:
            query = query.eq("category", category)
        if search:
            query = query.ilike("name", f"%{search}%")

        response = query.range(offset, offset + limit - 1).execute()
        return jsonify({
            "success": True,
            "data": response.data,
            "page": page,
            "limit": limit,
            "total": len(response.data),
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@product_bp.route("/products/<product_id>", methods=["GET"])
def get_product(product_id):
    try:
        response = supabase_client.table("products").select("*").eq("id", product_id).execute()
        if not response.data:
            return jsonify({"success": False, "message": "Product not found"}), 404
        return jsonify({"success": True, "data": response.data[0]})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@product_bp.route("/products", methods=["POST"])
@role_required("store_owner", "super_admin")
def add_product():
    try:
        data = request.get_json() or {}
        store_id = data.get("store_id") or _owner_store_id()
        if not store_id:
            return jsonify({"success": False, "error": "No store found for user"}), 400

        response = supabase_client.table("products").insert({
            "store_id": store_id,
            "name": data["name"],
            "description": data.get("description", ""),
            "price": data["price"],
            "image_url": data.get("image_url", ""),
            "images": data.get("images", []),
            "description": data.get("description", ""),
            "category": data.get("category", ""),
            "stock": data.get("stock", 0),
        }).execute()

        return jsonify({"success": True, "data": response.data[0] if response.data else None})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@product_bp.route("/products/<product_id>", methods=["PUT"])
@role_required("store_owner", "super_admin")
def update_product(product_id):
    try:
        data = request.get_json() or {}
        store_id = _owner_store_id()
        existing = supabase_client.table("products").select("*").eq("id", product_id).execute()
        if not existing.data:
            return jsonify({"success": False, "message": "Product not found"}), 404

        if g.user.get("role") == "store_owner" and existing.data[0].get("store_id") != store_id:
            return jsonify({"success": False, "message": "Unauthorized"}), 403

        allowed = {}
        for field in ("name", "description", "price", "image_url", "images", "category", "stock"):
            if field in data:
                allowed[field] = data[field]

        response = supabase_client.table("products").update(allowed).eq("id", product_id).execute()
        return jsonify({"success": True, "data": response.data[0] if response.data else None})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@product_bp.route("/products/<product_id>", methods=["DELETE"])
@role_required("store_owner", "super_admin")
def delete_product(product_id):
    try:
        store_id = _owner_store_id()
        existing = supabase_client.table("products").select("*").eq("id", product_id).execute()
        if not existing.data:
            return jsonify({"success": False, "message": "Product not found"}), 404

        if g.user.get("role") == "store_owner" and existing.data[0].get("store_id") != store_id:
            return jsonify({"success": False, "message": "Unauthorized"}), 403

        supabase_client.table("products").delete().eq("id", product_id).execute()
        return jsonify({"success": True, "message": "Product deleted"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@product_bp.route("/inventory", methods=["GET"])
@role_required("store_owner", "super_admin")
def inventory():
    try:
        store_id = request.args.get("store_id") or _owner_store_id()
        if not store_id and g.user.get("role") != "super_admin":
            return jsonify({"success": False, "message": "No store found"}), 404

        query = supabase_client.table("products").select("*")
        if store_id:
            query = query.eq("store_id", store_id)
        products = query.execute().data

        low_stock = [p for p in products if 0 < (p.get("stock") or 0) <= 5]
        out_of_stock = [p for p in products if (p.get("stock") or 0) == 0]
        in_stock = [p for p in products if (p.get("stock") or 0) > 5]

        return jsonify({
            "success": True,
            "data": products,
            "stats": {
                "total": len(products),
                "in_stock": len(in_stock),
                "low_stock": len(low_stock),
                "out_of_stock": len(out_of_stock),
            },
            "low_stock": low_stock,
            "out_of_stock": out_of_stock,
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
