import html
import json


def _esc(value):
    return html.escape(str(value or ""))


def build_store_page(store, products, theme):
    """Build a complete standalone HTML storefront at runtime from DB data + theme."""
    palette = theme.get("color_palette") or {}
    if isinstance(palette, str):
        try:
            palette = json.loads(palette)
        except Exception:
            palette = {}

    content = theme.get("page_content") or {}
    if isinstance(content, str):
        try:
            content = json.loads(content)
        except Exception:
            content = {}

    component = theme.get("component_config") or {}
    if isinstance(component, str):
        try:
            component = json.loads(component)
        except Exception:
            component = {}

    primary = palette.get("primary", "#2563eb")
    secondary = palette.get("secondary", "#06b6d4")
    accent = palette.get("accent", "#38bdf8")
    background = palette.get("background", "#0f172a")
    text_color = palette.get("text", "#f1f5f9")
    font = theme.get("font_style", "Inter")
    layout = theme.get("layout_style", "grid")
    store_name = _esc(store.get("name", "My Store"))
    business = _esc(store.get("business_type", "ecommerce"))
    region = _esc(store.get("region", "Global"))
    theme_name = _esc(theme.get("theme_name", "AI Store Theme"))

    hero_title = _esc(content.get("hero_title", f"Welcome to {store.get('name', 'Our Store')}"))
    hero_subtitle = _esc(content.get("hero_subtitle", f"Premium {business} collection for {region}"))
    tagline = _esc(content.get("store_tagline", theme_name))
    cta = _esc(content.get("cta_text", "Shop Now"))
    about = _esc(content.get("about_text", f"Discover curated {business} products with AI-personalized shopping."))

    product_cards = ""
    for p in products:
        name = _esc(p.get("name"))
        desc = _esc((p.get("description") or "")[:120])
        price = float(p.get("price") or 0)
        img = _esc(p.get("image_url") or "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400")
        stock = p.get("stock", 0)
        pid = _esc(p.get("id"))
        product_cards += f"""
        <article class="product-card" data-id="{pid}">
          <img src="{img}" alt="{name}" loading="lazy">
          <div class="product-body">
            <h3>{name}</h3>
            <p>{desc}</p>
            <div class="product-footer">
              <span class="price">${price:.2f}</span>
              <span class="stock">{'In stock' if stock > 0 else 'Out of stock'}</span>
            </div>
            <button class="btn-add" data-pid="{pid}" data-pname="{name}" data-price="{price}" {'disabled' if stock <= 0 else ''}>
              Add to Cart
            </button>
          </div>
        </article>"""

    if not product_cards:
        product_cards = '<p class="empty">No products listed yet. Check back soon.</p>'

    grid_class = "products-list" if layout == "list" else "products-grid"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{store_name} — {theme_name}</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Poppins:wght@400;600;700&family=Roboto:wght@400;500;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --primary: {primary};
      --secondary: {secondary};
      --accent: {accent};
      --bg: {background};
      --text: {text_color};
      --font: '{font}', 'Segoe UI', sans-serif;
    }}
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: var(--font); background: var(--bg); color: var(--text); line-height: 1.6; }}
    .ai-badge {{
      background: linear-gradient(90deg, var(--primary), var(--secondary));
      color: #fff; text-align: center; padding: 10px; font-size: 0.85rem; font-weight: 600;
    }}
    nav {{
      display: flex; justify-content: space-between; align-items: center;
      padding: 18px 6%; background: rgba(0,0,0,0.25); backdrop-filter: blur(10px);
      position: sticky; top: 0; z-index: 100; border-bottom: 1px solid rgba(255,255,255,0.08);
    }}
    nav .logo {{ font-size: 1.4rem; font-weight: 700; color: var(--accent); }}
    nav ul {{ display: flex; gap: 24px; list-style: none; }}
    nav a {{ color: var(--text); text-decoration: none; font-weight: 500; opacity: 0.9; }}
    nav a:hover {{ color: var(--accent); }}
    .hero {{
      padding: 90px 6% 70px;
      background: linear-gradient(135deg, var(--primary), var(--secondary));
      display: flex; flex-wrap: wrap; align-items: center; gap: 40px;
    }}
    .hero-text {{ flex: 1; min-width: 280px; }}
    .hero-text .tag {{ display: inline-block; background: rgba(255,255,255,0.15); padding: 6px 14px;
      border-radius: 20px; font-size: 0.8rem; margin-bottom: 16px; }}
    .hero h1 {{ font-size: clamp(2rem, 5vw, 3.2rem); margin-bottom: 16px; line-height: 1.15; }}
    .hero p {{ font-size: 1.1rem; opacity: 0.92; max-width: 520px; margin-bottom: 28px; }}
    .hero-cta {{
      display: inline-block; padding: 14px 32px; background: #fff; color: var(--primary);
      border-radius: 12px; text-decoration: none; font-weight: 700; transition: 0.2s;
    }}
    .hero-cta:hover {{ transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.2); }}
    .hero-visual {{
      flex: 1; min-width: 260px; height: 280px; border-radius: 20px;
      background: rgba(255,255,255,0.12); display: flex; align-items: center; justify-content: center;
      font-size: 4rem; border: 1px solid rgba(255,255,255,0.2);
    }}
    section {{ padding: 70px 6%; }}
    section h2 {{ font-size: 2rem; margin-bottom: 12px; color: var(--accent); }}
    section .sub {{ color: rgba(255,255,255,0.65); margin-bottom: 36px; }}
    .products-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 24px; }}
    .products-list {{ display: flex; flex-direction: column; gap: 16px; }}
    .products-list .product-card {{ display: flex; flex-direction: row; }}
    .products-list .product-card img {{ width: 200px; height: 160px; flex-shrink: 0; }}
    .product-card {{
      background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1);
      border-radius: 16px; overflow: hidden; transition: 0.25s;
    }}
    .product-card:hover {{ transform: translateY(-6px); border-color: var(--accent); }}
    .product-card img {{ width: 100%; height: 200px; object-fit: cover; }}
    .product-body {{ padding: 18px; }}
    .product-body h3 {{ margin-bottom: 8px; }}
    .product-body p {{ font-size: 0.88rem; opacity: 0.75; margin-bottom: 12px; }}
    .product-footer {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }}
    .price {{ font-size: 1.25rem; font-weight: 700; color: var(--accent); }}
    .stock {{ font-size: 0.8rem; opacity: 0.7; }}
    .btn-add {{
      width: 100%; padding: 10px; border: none; border-radius: 10px; cursor: pointer;
      background: linear-gradient(90deg, var(--primary), var(--secondary)); color: #fff; font-weight: 600;
    }}
    .btn-add:disabled {{ opacity: 0.4; cursor: not-allowed; }}
    .about {{ background: rgba(255,255,255,0.03); text-align: center; }}
    .about p {{ max-width: 700px; margin: 0 auto; opacity: 0.85; }}
    .region-bar {{
      display: flex; gap: 12px; flex-wrap: wrap; justify-content: center; margin-top: 24px;
    }}
    .region-chip {{
      padding: 8px 18px; border-radius: 20px; border: 1px solid var(--accent);
      font-size: 0.85rem; color: var(--accent);
    }}
    footer {{
      text-align: center; padding: 30px; opacity: 0.6; font-size: 0.85rem;
      border-top: 1px solid rgba(255,255,255,0.08);
    }}
    .empty {{ text-align: center; opacity: 0.6; padding: 40px; }}
    .toast {{
      position: fixed; bottom: 24px; right: 24px; background: var(--primary);
      color: #fff; padding: 12px 20px; border-radius: 10px; display: none; z-index: 999;
    }}
    @media (max-width: 768px) {{
      nav ul {{ display: none; }}
      .products-list .product-card {{ flex-direction: column; }}
      .products-list .product-card img {{ width: 100%; }}
    }}
  </style>
</head>
<body>
  <div class="ai-badge">✨ AI-Generated Store · {theme_name} · {region}</div>
  <nav>
    <div class="logo">{store_name}</div>
    <ul>
      <li><a href="#home">Home</a></li>
      <li><a href="#products">Products</a></li>
      <li><a href="#about">About</a></li>
    </ul>
  </nav>

  <header class="hero" id="home">
    <div class="hero-text">
      <span class="tag">{tagline}</span>
      <h1>{hero_title}</h1>
      <p>{hero_subtitle}</p>
      <a class="hero-cta" href="#products">{cta}</a>
    </div>
    <div class="hero-visual">🛍️</div>
  </header>

  <section id="products">
    <h2>Featured Products</h2>
    <p class="sub">Live inventory from your store — updated at runtime</p>
    <div class="{grid_class}">
      {product_cards}
    </div>
  </section>

  <section class="about" id="about">
    <h2>About {store_name}</h2>
    <p>{about}</p>
    <div class="region-bar">
      <span class="region-chip">📍 {region}</span>
      <span class="region-chip">🏷️ {business}</span>
      <span class="region-chip">🎨 {theme_name}</span>
    </div>
  </section>

  <footer>
    <p>{store_name} · Powered by AI Dynamic ERP · Generated at runtime</p>
  </footer>

  <div class="toast" id="toast">Added to cart!</div>

  <script>
    const STORE_ID = "{_esc(store.get('id'))}";
    document.querySelectorAll(".btn-add").forEach(btn => {{
      btn.addEventListener("click", () => {{
        const id = btn.dataset.pid;
        const name = btn.dataset.pname;
        const price = parseFloat(btn.dataset.price);
        let cart = JSON.parse(localStorage.getItem("cart") || "[]");
        const existing = cart.find(i => i.product_id === id);
        if (existing) existing.quantity += 1;
        else cart.push({{ product_id: id, name, price, quantity: 1, store_id: STORE_ID }});
        localStorage.setItem("cart", JSON.stringify(cart));
        const t = document.getElementById("toast");
        t.style.display = "block";
        setTimeout(() => t.style.display = "none", 2000);
      }});
    }});
  </script>
</body>
</html>"""
