from flask import Blueprint, request, g, jsonify
from services.supabase_service import supabase_client
from services.gemini_service import generate_theme
from auth import protected, role_required

store_bp = Blueprint("stores", __name__)


@store_bp.route("/stores", methods=["POST"])
@role_required("store_owner", "super_admin")
def create_store():
    try:
        body = request.get_json() or {}
        store_name = body.get("store_name")
        business_type = body.get("business_type", "general")
        region = body.get("region", "")
        style = body.get("style", "modern")

        user_id = g.user["id"]
        if not store_name:
            return jsonify({"success": False, "error": "store_name required"}), 400

        store_res = supabase_client.table("stores").insert({
            "name": store_name,
            "business_type": business_type,
            "user_id": user_id,
            "region": region,
        }).execute()
        store = store_res.data[0]

        theme = generate_theme(business_type, region=region, style=style)
        component_config = {
            **(theme.get("component_config") or {}),
            "page_content": theme.get("page_content") or {},
            "ai_generated": theme.get("ai_generated", False),
            "background_image_url": theme.get("background_image_url", ""),
            "background_image_prompt": theme.get("background_image_prompt", ""),
            "background_ai_generated": theme.get("background_ai_generated", False),
        }
        theme_res = supabase_client.table("generated_themes").insert({
            "store_id": store["id"],
            "theme_name": theme["theme_name"],
            "color_palette": theme["color_palette"],
            "layout_style": theme["layout_style"],
            "font_style": theme["font_style"],
            "component_config": component_config,
        }).execute()

        supabase_client.table("users").update({"store_id": store["id"]}).eq("id", user_id).execute()

        return jsonify({
            "success": True,
            "message": "Store and theme created",
            "store": store,
            "theme": theme_res.data[0] if theme_res.data else theme,
            "preview_url": f"/store-live/{store['id']}",
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@store_bp.route("/stores/<store_id>", methods=["PATCH"])
@role_required("store_owner", "super_admin")
def update_store(store_id):
    try:
        body = request.get_json() or {}
        allowed = ["name", "business_type", "region", "currency", "payment_options", "bank_account_title", "bank_account_number", "bank_name"]
        payload = {k: v for k, v in body.items() if k in allowed and v is not None}

        if not payload:
            return jsonify({"success": False, "error": "Nothing to update"}), 400

        existing = supabase_client.table("stores").select("*").eq("id", store_id).execute()
        if not existing.data:
            return jsonify({"success": False, "error": "Store not found"}), 404
        

        new_currency = payload.get("currency")
        old_currency = existing.data[0].get("currency")
        conversion_rate = body.get("conversion_rate")

        if new_currency and old_currency and new_currency != old_currency:
            if not conversion_rate:
                return jsonify({"success": False, "message": f"Please provide a conversion rate to convert prices from {old_currency} to {new_currency}."}), 400
            try:
                rate = float(conversion_rate)
                if rate <= 0:
                    raise ValueError()
            except ValueError:
                return jsonify({"success": False, "message": "Conversion rate must be a positive number."}), 400

            products = supabase_client.table("products").select("id, price").eq("store_id", store_id).execute()
            for p in products.data:
                new_price = round(float(p["price"]) * rate, 2)
                supabase_client.table("products").update({"price": new_price}).eq("id", p["id"]).execute()

        new_payment_opts = payload.get("payment_options")
        if new_payment_opts in ("online", "both"):
            current = existing.data[0]
            title = payload.get("bank_account_title") or current.get("bank_account_title")
            number = payload.get("bank_account_number") or current.get("bank_account_number")
            bank = payload.get("bank_name") or current.get("bank_name")
            if not (title and number and bank):
                return jsonify({"success": False, "message": "Bank account title, number, and bank name are required to enable online payments."}), 400

        if g.user.get("role") == "store_owner" and existing.data[0].get("user_id") != g.user["id"]:
            return jsonify({"success": False, "error": "Unauthorized"}), 403

        result = supabase_client.table("stores").update(payload).eq("id", store_id).execute()
        return jsonify({"success": True, "store": result.data[0] if result.data else None})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@store_bp.route("/stores", methods=["GET"])
@protected
def list_stores():
    try:
        role = g.user.get("role")
        if role == "super_admin":
            result = supabase_client.table("stores").select("*").execute()
        elif role == "store_owner":
            result = supabase_client.table("stores").select("*").eq("user_id", g.user["id"]).execute()
        else:
            result = supabase_client.table("stores").select("*").execute()
        return jsonify({"success": True, "data": result.data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@store_bp.route("/store-dashboard/<store_id>", methods=["GET"])
@protected
def store_dashboard(store_id):
    store_res = supabase_client.table("stores").select("*").eq("id", store_id).execute()
    if not store_res.data:
        return jsonify({"success": False, "message": "Store not found"}), 404

    store = store_res.data[0]
    role = g.user.get("role")
    if role == "store_owner" and store.get("user_id") != g.user["id"]:
        return jsonify({"success": False, "message": "Unauthorized"}), 403

    theme_res = supabase_client.table("generated_themes").select("*").eq("store_id", store_id).execute()
    products_res = supabase_client.table("products").select("*").eq("store_id", store_id).execute()

    return jsonify({
        "success": True,
        "store": store,
        "generated_theme": theme_res.data[0] if theme_res.data else None,
        "products": products_res.data,
    })


@store_bp.route("/dashboard", methods=["GET"])
@protected
def dashboard():
    try:
        user_id = g.user["id"]
        store_res = supabase_client.table("stores").select("*").eq("user_id", user_id).execute()
        if not store_res.data:
            return jsonify({"success": False, "message": "No store found"}), 404

        store = store_res.data[0]
        theme_res = supabase_client.table("generated_themes").select("*").eq("store_id", store["id"]).execute()
        products_res = supabase_client.table("products").select("*").eq("store_id", store["id"]).execute()
        orders_res = supabase_client.table("orders").select("*").eq("store_id", store["id"]).execute()

        order_ids = [o["id"] for o in orders_res.data]
        sold_map = {}
        if order_ids:
            items_res = supabase_client.table("order_items").select("product_id, quantity").in_("order_id", order_ids).execute()
            for item in items_res.data:
                pid = item["product_id"]
                sold_map[pid] = sold_map.get(pid, 0) + item["quantity"]

        for p in products_res.data:
            p["units_sold"] = sold_map.get(p["id"], 0)

        low_stock = [p for p in products_res.data if (p.get("stock") or 0) <= 5]

        return jsonify({
            "success": True,
            "store": store,
            "theme": theme_res.data[0] if theme_res.data else None,
            "products": products_res.data,
            "orders": orders_res.data,
            "stats": {
                "product_count": len(products_res.data),
                "order_count": len(orders_res.data),
                "low_stock_count": len(low_stock),
            },
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@store_bp.route("/stores/<store_id>/payment-info", methods=["GET"])
@protected
def store_payment_info(store_id):
    try:
        res = supabase_client.table("stores").select(
            "currency, payment_options, bank_account_title, bank_account_number, bank_name"
        ).eq("id", store_id).execute()
        if not res.data:
            return jsonify({"success": False, "message": "Store not found"}), 404
        s = res.data[0]
        info = {"currency": s.get("currency", "USD"), "payment_options": s.get("payment_options", "cod")}
        if s.get("payment_options") in ("online", "both"):
            info["bank_account_title"] = s.get("bank_account_title")
            info["bank_account_number"] = s.get("bank_account_number")
            info["bank_name"] = s.get("bank_name")
        return jsonify({"success": True, "data": info})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500