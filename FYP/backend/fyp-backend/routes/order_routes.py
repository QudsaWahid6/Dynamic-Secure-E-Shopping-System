from flask import Blueprint, request, jsonify, g
from auth import protected, role_required
from services.supabase_service import supabase_client
import uuid

order_bp = Blueprint("order_bp", __name__)


def _owner_store_id():
    store = supabase_client.table("stores").select("id").eq("user_id", g.user["id"]).execute()
    return store.data[0]["id"] if store.data else None


@order_bp.route("/orders", methods=["GET"])
@protected
def list_orders():
    try:
        role = g.user.get("role")
        if role == "customer":
            result = supabase_client.table("orders").select("*").eq("user_id", g.user["id"]).execute()
        elif role == "store_owner":
            store_id = _owner_store_id()
            if not store_id:
                return jsonify({"success": True, "data": []})
            result = supabase_client.table("orders").select("*").eq("store_id", store_id).execute()
        elif role == "super_admin":
            result = supabase_client.table("orders").select("*").execute()
        else:
            return jsonify({"success": False, "message": "Unauthorized"}), 403

        orders = result.data
        for order in orders:
            items = (
                supabase_client.table("order_items")
                .select("*, products(name, image_url)")
                .eq("order_id", order["id"])
                .execute()
            )
            order["items"] = items.data

        return jsonify({"success": True, "data": orders})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@order_bp.route("/orders", methods=["POST"])
@role_required("customer")
def create_order():
    try:
        data = request.get_json() or {}
        items = data.get("items", [])

        if not items:
            return jsonify({"success": False, "message": "items required"}), 400

        if not g.user.get("phone") or not g.user.get("address"):
            return jsonify({
                "success": False,
                "missing_profile_info": True,
                "message": "Please add your phone number and address before placing an order."
            }), 400

        payments = data.get("payments", {})  # { "<store_id>": {"payment_method": "cod"|"online", "receipt_image_url": "..."} }
        by_store = {}

        for item in items:
            product = supabase_client.table("products").select("*").eq("id", item["product_id"]).execute()
            if not product.data:
                return jsonify({"success": False, "message": f"Product {item['product_id']} not found"}), 404
            p = product.data[0]

            if not p.get("store_id"):
                return jsonify({"success": False, "message": f"{p.get('name','Product')} is not linked to a store and can't be ordered. Contact support."}), 400

            qty = int(item.get("quantity", 1))
            current_stock = p.get("stock") or 0

            if current_stock <= 0:
                return jsonify({"success": False, "out_of_stock": True,
                                 "message": f"{p['name']} is currently out of stock."}), 400
            if qty > current_stock:
                return jsonify({"success": False, "out_of_stock": True,
                                 "message": f"Only {current_stock} units of {p['name']} are available."}), 400

            by_store.setdefault(p["store_id"], []).append({"product": p, "quantity": qty})

        group_id = str(uuid.uuid4())
        created_orders = []

        for store_id, entries in by_store.items():
            total = sum(float(e["product"]["price"]) * e["quantity"] for e in entries)

            pay_info = payments.get(store_id, {"payment_method": "cod"})
            method = pay_info.get("payment_method", "cod")
            receipt_url = pay_info.get("receipt_image_url")

            store_row = supabase_client.table("stores").select("payment_options").eq("id", store_id).execute().data[0]
            allowed_methods = {"cod": ["cod"], "online": ["online"], "both": ["cod", "online"]}.get(store_row.get("payment_options", "cod"), ["cod"])
            if method not in allowed_methods:
                return jsonify({"success": False, "message": f"This store does not accept {method} payments."}), 400
            if method == "online" and not receipt_url:
                return jsonify({"success": False, "message": "Payment receipt image is required for online payment."}), 400

            order_res = supabase_client.table("orders").insert({
                "user_id": g.user["id"],
                "store_id": store_id,
                "order_group_id": group_id,
                "status": "pending",
                "total_amount": total,
                "shipping_phone": g.user.get("phone"),
                "shipping_address": g.user.get("address"),
                "payment_method": method,
                "receipt_image_url": receipt_url,
            }).execute()
            order = order_res.data[0]

            for e in entries:
                p, qty = e["product"], e["quantity"]
                supabase_client.table("order_items").insert({
                    "order_id": order["id"], "product_id": p["id"],
                    "quantity": qty, "price": p["price"]
                }).execute()
                new_stock = max((p.get("stock") or 0) - qty, 0)
                supabase_client.table("products").update({"stock": new_stock}).eq("id", p["id"]).execute()

            created_orders.append(order)

            if method == "online":
                convo = supabase_client.table("conversations").select("*").eq("customer_id", g.user["id"]).eq("store_id", store_id).execute()
                if convo.data:
                    conversation_id = convo.data[0]["id"]
                else:
                    new_convo = supabase_client.table("conversations").insert({"customer_id": g.user["id"], "store_id": store_id}).execute()
                    conversation_id = new_convo.data[0]["id"]
                supabase_client.table("messages").insert({
                    "conversation_id": conversation_id,
                    "sender_id": g.user["id"],
                    "content": f"Payment receipt for Order #{order['id'][:8]}",
                    "image_url": receipt_url,
                }).execute()

        return jsonify({"success": True, "data": created_orders, "order_group_id": group_id})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    

@order_bp.route("/orders/<order_id>/status", methods=["PATCH"])
@role_required("store_owner", "super_admin")
def update_order_status(order_id):
    try:
        data = request.get_json() or {}
        status = data.get("status")
        if not status:
            return jsonify({"success": False, "message": "status required"}), 400

        existing = supabase_client.table("orders").select("*").eq("id", order_id).execute()
        if not existing.data:
            return jsonify({"success": False, "message": "Order not found"}), 404

        if g.user.get("role") == "store_owner":
            store_id = _owner_store_id()
            if existing.data[0].get("store_id") != store_id:
                return jsonify({"success": False, "message": "Unauthorized"}), 403

        old_status = existing.data[0].get("status")

        # restore stock if order is being cancelled and wasn't already cancelled
        if status == "cancelled" and old_status != "cancelled":
            order_items = (
                supabase_client.table("order_items")
                .select("product_id, quantity")
                .eq("order_id", order_id)
                .execute()
            )
            for oi in order_items.data:
                product = supabase_client.table("products").select("stock").eq("id", oi["product_id"]).execute()
                if product.data:
                    restored_stock = (product.data[0].get("stock") or 0) + oi["quantity"]
                    supabase_client.table("products").update({"stock": restored_stock}).eq("id", oi["product_id"]).execute()

        response = supabase_client.table("orders").update({"status": status}).eq("id", order_id).execute()
        return jsonify({"success": True, "data": response.data[0] if response.data else None})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
