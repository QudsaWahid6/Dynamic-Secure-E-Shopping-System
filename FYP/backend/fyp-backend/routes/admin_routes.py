from flask import Blueprint, jsonify
from auth import role_required
from services.supabase_service import supabase_client
from security import clear_all_logs

admin_bp = Blueprint("admin_bp", __name__)


@admin_bp.route("/admin/clear-logs", methods=["POST"])
@role_required("super_admin")
def clear_logs():
    try:
        success, message = clear_all_logs()
        return jsonify({"success": success, "message": message})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    
@admin_bp.route("/admin/users", methods=["GET"])
@role_required("super_admin")
def admin_users():
    try:
        result = supabase_client.table("users").select("id, name, email, role, status, created_at, store_id").execute()
        return jsonify({"success": True, "data": result.data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@admin_bp.route("/admin/stores", methods=["GET"])
@role_required("super_admin")
def admin_stores():
    try:
        result = supabase_client.table("stores").select("*").execute()
        return jsonify({"success": True, "data": result.data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@admin_bp.route("/admin/stats", methods=["GET"])
@role_required("super_admin")
def admin_stats():
    try:
        themes = supabase_client.table("generated_themes").select("id").execute()
        users = supabase_client.table("users").select("id, created_at").execute()
        stores = supabase_client.table("stores").select("id, created_at").execute()
        products = supabase_client.table("products").select("id").execute()
        orders = supabase_client.table("orders").select("id, created_at, total_amount").execute()

        def _by_day(rows):
            from collections import Counter
            c = Counter((r.get("created_at") or "")[:10] for r in rows)
            return c
        growth = {"users": _by_day(users.data), "orders": _by_day(orders.data)}

        return jsonify({
            "success": True,
            "stats": {
                "users": len(users.data),
                "stores": len(stores.data),
                "products": len(products.data),
                "orders": len(orders.data),
                "themes": len(themes.data),
            },
            "growth": {
                "users": dict(growth["users"]),
                "orders": dict(growth["orders"]),
            },
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@admin_bp.route("/admin/activity", methods=["GET"])
@role_required("super_admin")
def admin_activity():
    try:
        recent_orders = supabase_client.table("orders").select("*").order("created_at", desc=True).limit(10).execute()
        recent_stores = supabase_client.table("stores").select("*").order("created_at", desc=True).limit(10).execute()
        return jsonify({
            "success": True,
            "recent_orders": recent_orders.data,
            "recent_stores": recent_stores.data,
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
@admin_bp.route("/admin/users/pending", methods=["GET"])
@role_required("super_admin")
def pending_store_owners():
    try:
        result = (
            supabase_client.table("users")
            .select("id, name, email, role, status, created_at")
            .eq("role", "store_owner")
            .eq("status", "pending")
            .order("created_at", desc=True)
            .execute()
        )
        return jsonify({"success": True, "data": result.data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@admin_bp.route("/admin/users/<user_id>/approve", methods=["PATCH"])
@role_required("super_admin")
def approve_store_owner(user_id):
    try:
        result = (
            supabase_client.table("users")
            .update({"status": "active"})
            .eq("id", user_id)
            .eq("role", "store_owner")
            .execute()
        )
        if not result.data:
            return jsonify({"success": False, "message": "User not found"}), 404
        return jsonify({"success": True, "data": result.data[0]})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@admin_bp.route("/admin/users/<user_id>/reject", methods=["PATCH"])
@role_required("super_admin")
def reject_store_owner(user_id):
    try:
        result = (
            supabase_client.table("users")
            .update({"status": "rejected"})
            .eq("id", user_id)
            .eq("role", "store_owner")
            .execute()
        )
        if not result.data:
            return jsonify({"success": False, "message": "User not found"}), 404
        return jsonify({"success": True, "data": result.data[0]})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    
@admin_bp.route("/admin/users/<user_id>/status", methods=["PATCH"])
@role_required("super_admin")
def update_user_status(user_id):
    try:
        from flask import request
        data = request.get_json() or {}
        new_status = data.get("status")
        if new_status not in ("active", "pending", "rejected"):
            return jsonify({"success": False, "message": "Invalid status"}), 400

        result = (
            supabase_client.table("users")
            .update({"status": new_status})
            .eq("id", user_id)
            .neq("role", "super_admin")
            .execute()
        )
        if not result.data:
            return jsonify({"success": False, "message": "User not found or cannot update super admin"}), 404
        return jsonify({"success": True, "data": result.data[0]})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500