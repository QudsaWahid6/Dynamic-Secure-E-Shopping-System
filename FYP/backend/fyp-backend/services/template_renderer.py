import os
import json
import re
import urllib.parse
from pathlib import Path

FRONTEND_DIR = Path(__file__).resolve().parents[3] / "frontend"
TEMPLATE_PATH = FRONTEND_DIR / "templates" / "dynamic-store.html"
APPLY_SCRIPT_PATH = FRONTEND_DIR / "templates" / "apply-theme.js"


def _normalize_theme(theme):
    palette = theme.get("color_palette") or {}
    if isinstance(palette, str):
        try:
            palette = json.loads(palette)
        except Exception:
            palette = {}

    component = theme.get("component_config") or {}
    if isinstance(component, str):
        try:
            component = json.loads(component)
        except Exception:
            component = {}

    page_content = theme.get("page_content") or component.get("page_content") or {}
    if isinstance(page_content, str):
        try:
            page_content = json.loads(page_content)
        except Exception:
            page_content = {}

    return {
        "theme_name": theme.get("theme_name", "Store Theme"),
        "hero_layout": theme.get("hero_layout") or component.get("hero_layout") or "image-right","hero_layout": theme.get("hero_layout") or component.get("hero_layout") or "image-right",
        "color_palette": palette,
        "layout_style": theme.get("layout_style", "grid"),
        "font_style": theme.get("font_style", "Poppins"),
        "style_category": theme.get("style_category") or component.get("style_category", "modern"),
        "component_config": component,
        "page_content": page_content,
        "background_image_url": (
            theme.get("background_image_url")
            or component.get("background_image_url")
            or ""
        ),
        "background_image_prompt": (
            theme.get("background_image_prompt")
            or component.get("background_image_prompt")
            or ""
        ),
        "ai_generated": theme.get("ai_generated", component.get("ai_generated", False)),
    }


def render_store_template(store, products, theme):
    """Serve fixed HTML template with Gemini JSON injected — no full page generation."""
    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"Template missing: {TEMPLATE_PATH}")

    template_html = TEMPLATE_PATH.read_text(encoding="utf-8")
    apply_js = APPLY_SCRIPT_PATH.read_text(encoding="utf-8") if APPLY_SCRIPT_PATH.exists() else ""

    normalized = _normalize_theme(theme)
    payload = {
        "store": {
            "id": store.get("id"),
            "name": store.get("name", "My Store"),
            "business_type": store.get("business_type", "general"),
            "region": store.get("region", "Global"),
            "currency": store.get("currency", "USD"),
        },
        "products": products,
        "theme": normalized,
    }

    data_json = json.dumps(payload, ensure_ascii=False)
    data_json = data_json.replace("</", "<\\/")

    injection = f"""<script>
window.__STORE_DATA__ = {data_json};
</script>
<script>
{apply_js}
</script>"""

    if "<!-- THEME_INJECT -->" in template_html:
        return template_html.replace("<!-- THEME_INJECT -->", injection)

    return template_html.replace("</body>", injection + "\n</body>")
