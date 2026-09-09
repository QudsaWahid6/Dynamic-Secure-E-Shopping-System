import json
from flask import Blueprint, request, jsonify, g, Response
from auth import protected, role_required
from services.supabase_service import supabase_client
from services.gemini_service import generate_theme
from services.template_renderer import render_store_template

theme_bp = Blueprint("theme_bp", __name__)


def _owner_store_id():
    store = supabase_client.table("stores").select("id").eq("user_id", g.user["id"]).execute()
    return store.data[0]["id"] if store.data else None


def _pack_component_config(theme):
    return {
        **(theme.get("component_config") or {}),
        "page_content": theme.get("page_content") or {},
        "ai_generated": theme.get("ai_generated", False),
        "style_category": theme.get("style_category", "modern"),
        "background_image_url": theme.get("background_image_url", ""),
        "background_image_prompt": theme.get("background_image_prompt", ""),
        "background_ai_generated": theme.get("background_ai_generated", False),
    }


def _unpack_theme(row):
    component = row.get("component_config") or {}
    if isinstance(component, str):
        try:
            component = json.loads(component)
        except Exception:
            component = {}
    return {
        **row,
        "page_content": component.get("page_content", {}),
        "component_config": component,
        "ai_generated": component.get("ai_generated", False),
        "background_image_url": component.get("background_image_url", row.get("background_image_url", "")),
        "background_image_prompt": component.get("background_image_prompt", ""),
        "background_ai_generated": component.get("background_ai_generated", False),
        "hero_layout": row.get("hero_layout") or component.get("hero_layout", "image-right"),
    }


def _save_theme(store_id, theme):
    component_config = _pack_component_config(theme)
    existing = supabase_client.table("generated_themes").select("id").eq("store_id", store_id).execute()
    payload = {
        "store_id": store_id,
        "theme_name": theme["theme_name"],
        "color_palette": theme["color_palette"],
        "layout_style": theme["layout_style"],
        "font_style": theme["font_style"],
        "component_config": component_config,
        "hero_layout": theme.get("hero_layout", "image-right"),
    }
    if existing.data:
        response = supabase_client.table("generated_themes").update(payload).eq("store_id", store_id).execute()
    else:
        response = supabase_client.table("generated_themes").insert(payload).execute()
    saved = response.data[0] if response.data else theme
    return _unpack_theme(saved) if isinstance(saved, dict) and "store_id" in saved else theme


@theme_bp.route("/themes", methods=["GET"])
@protected
def list_themes():
    try:
        store_id = request.args.get("store_id")
        query = supabase_client.table("generated_themes").select("*")
        if store_id:
            query = query.eq("store_id", store_id)
        result = query.execute()
        data = [_unpack_theme(t) for t in result.data]
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@theme_bp.route("/themes/generate", methods=["POST"])
@role_required("store_owner", "super_admin")
def generate_new_theme():
    try:
        data = request.get_json() or {}
        business_type = data.get("business_type") or "general"
        region = data.get("region", "")
        style = data.get("style", "modern")
        aesthetic = data.get("aesthetic", "")
        store_id = data.get("store_id") or _owner_store_id()
        store_name_override = data.get("store_name", "")

        if not store_id:
            return jsonify({"success": False, "message": "No store found. Create a store first."}), 400

        store_res = supabase_client.table("stores").select("*").eq("id", store_id).execute()
        if not store_res.data:
            return jsonify({"success": False, "message": "Store not found"}), 404

        store = store_res.data[0]
        if not business_type or business_type == "general":
            business_type = store.get("business_type") or "general"

        theme = generate_theme(business_type, region=region or store.get("region", ""), style=style, aesthetic=aesthetic, store_name=data.get("store_name") or store.get("name", ""))
        saved = _save_theme(store_id, theme)

        products = supabase_client.table("products").select("*").eq("store_id", store_id).execute().data

        return jsonify({
            "success": True,
            "data": saved,
            "preview_url": f"/store-live/{store_id}",
            "template": "dynamic-store.html",
            "ai_generated": saved.get("ai_generated", False),
            "background_image_url": saved.get("background_image_url", ""),
            "message": "Theme JSON applied to store template" + (
                " with Gemini AI" if saved.get("ai_generated") else " (smart fallback)"
            ),
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@theme_bp.route("/themes/<theme_id>", methods=["PATCH"])
@role_required("store_owner", "super_admin")
def update_theme(theme_id):
    try:
        body = request.get_json() or {}
        # allowed = ["background_image_url", "color_palette", "hero_layout", "page_content", "component_config_updates"]
        # allowed = ["background_image_url", "color_palette", "hero_layout", "page_content", "hero_text_color"]
        # payload = {}
        # comp_updates = {}
        # for k, v in body.items():
        #     if k == "color_palette":
        #         comp_updates["color_palette"] = v
        #     elif k in allowed:
        #         comp_updates[k] = v
        
        allowed = ["background_image_url", "color_palette", "hero_layout", "page_content", "hero_text_color"]
        payload = {}
        comp_updates = {}
        for k, v in body.items():
            if k == "color_palette":
                comp_updates["color_palette"] = v
            elif k == "component_config_updates" and isinstance(v, dict):
                comp_updates.update(v)
            elif k in allowed:
                comp_updates[k] = v


        if not comp_updates:
            return jsonify({"success": False, "error": "Nothing to update"}), 400
        row = supabase_client.table("generated_themes").select("*").eq("id", theme_id).execute()
        if not row.data:
            return jsonify({"success": False, "error": "Theme not found"}), 404
        existing_config = row.data[0].get("component_config") or {}

        # Build the DB-level update payload
        db_payload = {}

        # color_palette goes to both the real column AND component_config
        if "color_palette" in comp_updates:
            db_payload["color_palette"] = comp_updates.pop("color_palette")
            existing_config["color_palette"] = db_payload["color_palette"]

        # hero_layout goes to its own column
        if "hero_layout" in comp_updates:
            db_payload["hero_layout"] = comp_updates.pop("hero_layout")
            existing_config["hero_layout"] = db_payload["hero_layout"]

        # page_content goes into component_config
        if "page_content" in comp_updates:
            existing_config["page_content"] = comp_updates.pop("page_content")


        if "component_config_updates" in comp_updates:
            for k, v in comp_updates.pop("component_config_updates").items():
                existing_config[k] = v
            if "font_style" in existing_config:
                db_payload["font_style"] = existing_config["font_style"]

        # hero_text_color also saved to its own column for backward compat
        if "hero_text_color" in comp_updates:
            db_payload["hero_text_color"] = comp_updates["hero_text_color"]
        existing_config.update(comp_updates)
        db_payload["component_config"] = existing_config

        result = supabase_client.table("generated_themes").update(db_payload).eq("id", theme_id).execute()
        
        return jsonify({"success": True, "theme": result.data[0] if result.data else None})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    

@theme_bp.route("/themes/<theme_id>", methods=["GET"])
@protected
def get_theme(theme_id):
    try:
        result = supabase_client.table("generated_themes").select("*").eq("id", theme_id).execute()
        if not result.data:
            return jsonify({"success": False, "message": "Theme not found"}), 404
        return jsonify({"success": True, "data": _unpack_theme(result.data[0])})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@theme_bp.route("/store-theme-data/<store_id>", methods=["GET"])
def store_theme_data(store_id):
    """Return JSON used to theme the template (for debugging / API clients)."""
    try:
        store_res = supabase_client.table("stores").select("*").eq("id", store_id).execute()
        if not store_res.data:
            return jsonify({"success": False, "message": "Store not found"}), 404
        store = store_res.data[0]
        theme_res = supabase_client.table("generated_themes").select("*").eq("store_id", store_id).execute()
        if theme_res.data:
            theme = _unpack_theme(theme_res.data[-1])
        else:
            from services.gemini_service import _fallback_theme
            theme = _fallback_theme(store.get("business_type", "general"), store.get("region", ""), "modern", store_name=store.get("name", ""))
        products = supabase_client.table("products").select("*").eq("store_id", store_id).execute().data
        return jsonify({
            "success": True,
            "template": "dynamic-store.html",
            "store": store,
            "products": products,
            "theme": theme,
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@theme_bp.route("/store-live/<store_id>", methods=["GET"])
def store_live_html(store_id):
    """Return a complete dynamically built HTML storefront at runtime."""
    try:
        store_res = supabase_client.table("stores").select("*").eq("id", store_id).execute()
        if not store_res.data:
            return Response("<h1>Store not found</h1>", status=404, mimetype="text/html")

        store = store_res.data[0]
        theme_res = supabase_client.table("generated_themes").select("*").eq("store_id", store_id).execute()

        if theme_res.data:
            theme = _unpack_theme(theme_res.data[-1])
        else:
            from services.gemini_service import _fallback_theme
            theme = _fallback_theme(store.get("business_type", "general"), store.get("region", ""), "modern", store_name=store.get("name", ""))

        products = supabase_client.table("products").select("*").eq("store_id", store_id).execute().data
        html = render_store_template(store, products, theme)
        return Response(html, mimetype="text/html")
    except Exception as e:
        return Response(f"<h1>Error loading store</h1><p>{e}</p>", status=500, mimetype="text/html")
