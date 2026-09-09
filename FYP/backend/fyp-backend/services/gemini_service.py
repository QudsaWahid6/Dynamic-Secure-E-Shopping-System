import os
import json
import re
import time
import urllib.parse
from google import genai
from google.genai import errors as genai_errors
from dotenv import load_dotenv

load_dotenv()

# MODELS = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-2.5-flash"]
# IMAGE_MODELS = ["imagen-3.0-generate-002", "imagen-3.0-fast-generate-001"]
MODELS = ["gemini-2.5-flash", "gemini-2.5-flash-lite"]
IMAGE_MODELS = []  # Imagen 3.0 retired June 24 2026
_client = None


def _get_client():
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set in .env")
        _client = genai.Client(api_key=api_key)
    return _client


def _call_gemini(prompt, max_retries=2):
    client = _get_client()
    last_error = None
    for model in MODELS:
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(model=model, contents=prompt)
                if response.text and response.text.strip():
                    return response.text
            except genai_errors.ServerError as e:
                last_error = e
                time.sleep(1 + attempt)
            except Exception as e:
                last_error = e
                break
    raise last_error or Exception("All Gemini models failed")


def _parse_json(text):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group())
    return json.loads(text)


def _variety_seed(*parts):
    import hashlib
    key = "|".join(str(p or "") for p in parts)
    return int(hashlib.md5(key.encode()).hexdigest(), 16)

_IMAGE_POOLS = {
    "food": [
        "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=1600&q=80&fit=crop",
        "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=1600&q=80&fit=crop",
        "https://images.unsplash.com/photo-1466637574441-749b8f19452f?w=1600&q=80&fit=crop",
        "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=1600&q=80&fit=crop",
    ],
    "clothing": [
        "https://images.unsplash.com/photo-1445205170230-053b83016050?w=1600&q=80&fit=crop",
        "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=1600&q=80&fit=crop",
        "https://images.unsplash.com/photo-1483985988355-763728e1935b?w=1600&q=80&fit=crop",
        "https://images.unsplash.com/photo-1490481651871-ab68de25d43d?w=1600&q=80&fit=crop",
    ],
    "fashion": [
        "https://images.unsplash.com/photo-1445205170230-053b83016050?w=1600&q=80&fit=crop",
        "https://images.unsplash.com/photo-1483985988355-763728e1935b?w=1600&q=80&fit=crop",
    ],
    "general": [
        "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=1600&q=80&fit=crop",
        "https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?w=1600&q=80&fit=crop",
    ],
}
def suggest_product_category(name, description="", existing_categories=None):
    existing_categories = existing_categories or []
    existing_list = ", ".join(existing_categories) if existing_categories else "(none yet)"

    prompt = f"""You are helping categorize a product for an online store. Return ONLY valid JSON.

Product name: {name or "(not given)"}
Product description: {description or "(not given)"}
Store's existing categories: {existing_list}

Rules:
- If one of the existing categories clearly fits, reuse it exactly as written.
- Only suggest a brand-new category name if none of the existing ones fit.
- Category names should be short (1-3 words), e.g. "Shoes", "Desserts", "Home Decor".

Schema:
{{
  "category": "string",
  "is_new": true or false,
  "reason": "one short sentence explaining the pick"
}}"""

    try:
        raw = _call_gemini(prompt)
        result = _parse_json(raw)
        category = (result.get("category") or "").strip()
        if not category:
            raise ValueError("Empty category from Gemini")
        return {
            "category": category,
            "is_new": bool(result.get("is_new", category not in existing_categories)),
            "reason": result.get("reason", ""),
            "ai_generated": True,
        }
    except Exception as e:
        print(f"Gemini category suggestion fallback used: {e}")
        text = f"{name} {description}".lower()
        keyword_map = {
            "Shoes": ["shoe", "sneaker", "boot", "sandal"],
            "Tops": ["shirt", "t-shirt", "blouse", "top"],
            "Bottoms": ["pant", "jeans", "trouser", "short"],
            "Electronics": ["phone", "laptop", "charger", "headphone", "electronic"],
            "Furniture": ["chair", "table", "sofa", "desk", "furniture"],
            "Desserts": ["cake", "dessert", "sweet", "pastry"],
            "Beverages": ["drink", "juice", "coffee", "tea", "beverage"],
            "Accessories": ["bag", "watch", "jewel", "accessory"],
        }
        for cat, keywords in keyword_map.items():
            if any(k in text for k in keywords):
                return {"category": cat, "is_new": cat not in existing_categories, "reason": "Matched by keyword (AI unavailable)", "ai_generated": False}
        fallback_cat = existing_categories[0] if existing_categories else "General"
        return {"category": fallback_cat, "is_new": fallback_cat not in existing_categories, "reason": "Default fallback (AI unavailable)", "ai_generated": False}
    
    
def generate_background_image(prompt, business_type="general", style="modern", seed_extra=""):
    biz = (business_type or "general").lower()
    pool = next((urls for key, urls in _IMAGE_POOLS.items() if key in biz), _IMAGE_POOLS["general"])
    idx = _variety_seed(business_type, style, seed_extra) % len(pool)
    return pool[idx], False

def _fallback_theme(business_type, region="", style="modern", aesthetic="", store_name=""):
    palette_variants = {
        "modern": [
            {"primary": "#2563eb", "secondary": "#06b6d4", "accent": "#38bdf8", "background": "#0f172a", "text": "#f1f5f9", "surface": "#1e293b"},
            {"primary": "#4f46e5", "secondary": "#7c3aed", "accent": "#a78bfa", "background": "#0c0a1d", "text": "#f5f3ff", "surface": "#1e1b3a"},
            {"primary": "#0d9488", "secondary": "#14b8a6", "accent": "#5eead4", "background": "#042f2e", "text": "#ecfeff", "surface": "#134e4a"},
        ],
        "traditional": [
            {"primary": "#92400e", "secondary": "#b45309", "accent": "#fbbf24", "background": "#1c1917", "text": "#fef3c7", "surface": "#292524"},
            {"primary": "#7c2d12", "secondary": "#9a3412", "accent": "#fb923c", "background": "#1a0f0a", "text": "#ffedd5", "surface": "#2c1810"},
        ],
        "luxury": [
            {"primary": "#1c1917", "secondary": "#a8a29e", "accent": "#d4af37", "background": "#0a0a0a", "text": "#fafafa", "surface": "#171717"},
            {"primary": "#1e1b16", "secondary": "#8a7968", "accent": "#c9a96a", "background": "#0b0a08", "text": "#f5f0e8", "surface": "#1a1712"},
        ],
        "minimal": [
            {"primary": "#334155", "secondary": "#64748b", "accent": "#94a3b8", "background": "#f8fafc", "text": "#1e293b", "surface": "#ffffff"},
            {"primary": "#3f3f46", "secondary": "#71717a", "accent": "#a1a1aa", "background": "#fafafa", "text": "#18181b", "surface": "#ffffff"},
        ],
        "aesthetic": [
            {"primary": "#be185d", "secondary": "#ec4899", "accent": "#f9a8d4", "background": "#1a0a14", "text": "#fce7f3", "surface": "#2d1020"},
            {"primary": "#9333ea", "secondary": "#c084fc", "accent": "#e9d5ff", "background": "#180a24", "text": "#f5f0fc", "surface": "#2a1240"},
        ],
        "regional": [
            {"primary": "#15803d", "secondary": "#22c55e", "accent": "#86efac", "background": "#052e16", "text": "#ecfdf5", "surface": "#14532d"},
            {"primary": "#0e7490", "secondary": "#06b6d4", "accent": "#67e8f9", "background": "#082f33", "text": "#ecfeff", "surface": "#134e4a"},
        ],
    }
    regional_flavor = {
        "pakistan": {"greeting": "Khush Aamdeed", "font_style": "Poppins"},
        "middle east": {"greeting": "Ahlan wa Sahlan", "font_style": "Poppins"},
        "europe": {"greeting": "Welcome", "font_style": "Inter"},
        "usa": {"greeting": "Welcome", "font_style": "Inter"},
        "asia": {"greeting": "Welcome", "font_style": "Roboto"},
    }
    flavor = regional_flavor.get((region or "").lower(), {"greeting": "Welcome", "font_style": "Poppins"})

    name = store_name or business_type.title()
    variants = palette_variants.get(style, palette_variants["modern"])
    seed = _variety_seed(business_type, region, style, store_name)
    palette = variants[seed % len(variants)]
    bg_prompt = f"{style} {business_type} storefront atmosphere for {region or 'global market'}"
    bg_url, _ = generate_background_image(bg_prompt, business_type, style, seed_extra=store_name)

    hero_layouts = ["image-right", "image-left", "split", "centered"]
    hero_layout = hero_layouts[seed % len(hero_layouts)]

    return {
        "theme_name": f"{style.title()} {business_type.title()} — {region or 'Global'}",
        "color_palette": palette,
        "layout_style": ["grid", "list", "compact"][seed % 3],
        "hero_layout": hero_layout,
        "font_style": flavor["font_style"],
        "component_config": {
            "hero_banner": True,
            "promo_slider": seed % 2 == 0,
            "category_grid": True,
            "featured_products": True,
            "regional_personalization": bool(region),
            "hero_overlay": 0.55,
            "card_radius": ["12px", "16px", "20px"][seed % 3],
            "nav_style": ["glass", "solid", "minimal"][seed % 3],
        },
        "style_category": style,
        "page_content": {
            "store_tagline": f"{flavor['greeting']} to {name}",
            "hero_title": f"{name} — {style.title()} {business_type.title()}",
            "hero_subtitle": f"Personalized for {region or 'your region'} — {aesthetic or style + ' style'}".strip(),
            "cta_text": "Shop Collection",
            "about_text": f"{name} is a {style} {business_type} store tailored to {region or 'you'}.",
        },
        "background_image_prompt": bg_prompt,
        "background_image_url": bg_url,
        "ai_generated": False,
    }

# def generate_theme(business_type, region="", style="modern", aesthetic=""):
def generate_theme(business_type, region="", style="modern", aesthetic="", store_name=""):
    prompt = f"""You are a UI/UX designer for ecommerce. Return ONLY valid JSON.

Business: {business_type}
Store name: {store_name or "(not given — use the business type as the name)"}
Region: {region or "global"}
Style: {style}
Notes: {aesthetic or "none"}

Schema:
{{
  "theme_name": "string",
  "color_palette": {{
    "primary": "#hex", "secondary": "#hex", "accent": "#hex",
    "background": "#hex", "text": "#hex", "surface": "#hex"
  }},
  "layout_style": "grid or list or compact",
  "font_style": "Poppins or Roboto or Inter",
  "style_category": "{style}",
  "component_config": {{
    "hero_banner": true,
    "promo_slider": false,
    "category_grid": true,
    "featured_products": true,
    "regional_personalization": true,
    "hero_overlay": 0.45,
    "card_radius": "12px or 16px or 20px",
    "nav_style": "glass or solid or minimal"
  }},
  "page_content": {{
    "store_tagline": "short badge text mentioning the store name",
    "hero_title": "headline that uses the store name naturally",
    "hero_subtitle": "subtitle",
    "cta_text": "button label",
    "about_text": "about paragraph"
  }},
  "background_image_prompt": "detailed scene description for hero background",
  "background_image_url": "valid https://images.unsplash.com/photo-... URL matching {business_type} {style} store atmosphere — must be a real unsplash image URL"
}}"""

    try:
        raw = _call_gemini(prompt)
        theme = _parse_json(raw)

        bg_prompt = theme.get("background_image_prompt") or f"{style} {business_type} hero banner {region}"
        bg_url = theme.get("background_image_url") or ""
        bg_url, img_ai = generate_background_image(bg_prompt, business_type, style, seed_extra=store_name)
        # if not bg_url or "unsplash.com" not in bg_url:
        #     bg_url, img_ai = generate_background_image(bg_prompt, business_type, style)
        # else:
        #     img_ai = False

        theme["background_image_prompt"] = bg_prompt
        theme["background_image_url"] = bg_url
        theme["background_ai_generated"] = img_ai
        theme["ai_generated"] = True
        # Guarantee every required top-level field exists, even if Gemini
        # forgot one — pull defaults from the fallback theme rather than crash.
        defaults = None
        for key, default_val in [("theme_name", None), ("color_palette", None), ("layout_style", None), ("font_style", None)]:
            if key not in theme or not theme[key]:
                defaults = defaults or _fallback_theme(business_type, region, style, aesthetic, store_name)
                theme[key] = defaults[key]
                
        if "page_content" not in theme:
            theme["page_content"] = _fallback_theme(business_type, region, style, aesthetic, store_name)["page_content"]
        if "component_config" not in theme:
            theme["component_config"] = _fallback_theme(business_type, region, style, aesthetic , store_name)["component_config"]

        return theme
    except Exception as e:
        print(f"Gemini fallback used: {e}")
        return _fallback_theme(business_type, region, style, aesthetic, store_name)
