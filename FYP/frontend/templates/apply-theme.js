/**
 * Applies Gemini theme JSON to the fixed dynamic-store.html template.
 * Expects window.__STORE_DATA__ = { store, products, theme }
 */
(function () {
  const data = window.__STORE_DATA__;
  if (!data) return;

  const { store, products, theme } = data;
  
  const CURRENCY_SYMBOLS = { USD: "$", PKR: "Rs ", EUR: "€", GBP: "£", AED: "د.إ " };
  const currencySymbol = CURRENCY_SYMBOLS[store.currency] || (store.currency ? store.currency + " " : "$");
  const API_BASE_URL = (window.location.hostname === "127.0.0.1" || window.location.hostname === "localhost")
    ? "http://127.0.0.1:5000"
    : "";
  const palette = theme.color_palette || {};
  const content = theme.page_content || {};
  const config = theme.component_config || {};
  const root = document.documentElement;

  function setVar(name, value) {
    if (value != null && value !== "") root.style.setProperty(name, value);
  }

  setVar("--primary", palette.primary);
  setVar("--secondary", palette.secondary);
  setVar("--accent", palette.accent);
  setVar("--bg", palette.background);
  setVar("--text", palette.text);
  setVar("--surface", palette.surface || palette.background);

  // Hero text color override
  // Hero text color override — palette.hero_text takes priority (newest saved location)
  const heroTextColor = palette.hero_text || config.hero_text_color;
  if (heroTextColor) {
    setVar("--hero-text", heroTextColor);
  }

  const font = theme.font_style || "Poppins";
  setVar("--font", `'${font}', 'Segoe UI', sans-serif`);

  const overlay = config.hero_overlay != null ? config.hero_overlay : 0.5;
  setVar("--hero-overlay", overlay);

  const radius = config.card_radius || "16px";
  setVar("--card-radius", radius);

  const bgUrl = theme.background_image_url;
  if (bgUrl) {
    const safe = bgUrl.startsWith("data:") ? bgUrl : `url('${bgUrl.replace(/'/g, "%27")}')`;
    setVar("--hero-bg", safe);
  }

  const nav = document.getElementById("tplNav");
  if (nav) {
    nav.classList.remove("glass", "solid", "minimal");
    nav.classList.add(config.nav_style || "glass");
  }
  const heroEl = document.getElementById("hero");
  if (heroEl) {
    heroEl.classList.remove("image-right", "image-left", "split", "centered", "split-image-right", "split-image-left", "image-overlay-left");
    heroEl.classList.add(theme.hero_layout || "image-right");
  }

  document.title = `${store.name} — ${theme.theme_name || "Store"}`;
  document.getElementById("tplLogo").textContent = store.name;
  // document.getElementById("tplBadge").textContent = `✨ ${theme.theme_name || "AI Theme"} · ${theme.style_category || "modern"} layout`;
  document.getElementById("tplBadge").style.display = "none";
  document.getElementById("tplTagline").textContent = content.store_tagline || store.business_type;
  document.getElementById("tplHeroTitle").textContent = content.hero_title || store.name;
  document.getElementById("tplHeroSubtitle").textContent = content.hero_subtitle || "";
  document.getElementById("tplCta").textContent = content.cta_text || "Shop Now";
  document.getElementById("tplAboutTitle").textContent = `About ${store.name}`;
  document.getElementById("tplAboutText").textContent = content.about_text || "";
  document.getElementById("tplFooter").textContent = `${store.name} · Template + Gemini JSON · ${new Date().getFullYear()}`;

  // if (config.promo_slider) document.getElementById("tplPromo").classList.add("show");

  const promoEl = document.getElementById("tplPromo");
if (config.promo_slider) promoEl.classList.add("show");
if (config.promo_text) promoEl.textContent = config.promo_text;

  const chips = document.getElementById("tplChips");
  chips.innerHTML = [
    `<span class="tpl-chip">📍 ${store.region || "Global"}</span>`,
    `<span class="tpl-chip">🏷️ ${store.business_type || "Store"}</span>`,
    `<span class="tpl-chip">🎨 ${theme.layout_style || "grid"} layout</span>`,
    theme.ai_generated ? `<span class="tpl-chip">🤖 Gemini AI</span>` : "",
  ].join("");

  const productsEl = document.getElementById("tplProducts");
  const layout = theme.layout_style || "grid";
  productsEl.className = `tpl-products ${layout}`;

  const categories = [...new Set(products.map((p) => p.category).filter(Boolean))];
  const catEl = document.getElementById("tplCategories");
  if (config.category_grid && categories.length) {
    catEl.classList.add("show");
    catEl.innerHTML = `<span class="tpl-cat active" data-cat="">All</span>` +
      categories.map((c) => `<span class="tpl-cat" data-cat="${c}">${c}</span>`).join("");

    catEl.querySelectorAll(".tpl-cat").forEach((btn) => {
      btn.addEventListener("click", () => {
        catEl.querySelectorAll(".tpl-cat").forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        renderProducts(btn.dataset.cat);
      });
    });
  }

  function renderProducts(filterCat) {
    const list = filterCat
      ? products.filter((p) => p.category === filterCat)
      : products;

    if (!list.length) {
      productsEl.innerHTML = '<p class="tpl-empty">No products yet. Add products from your ERP dashboard.</p>';
      return;
    }

    productsEl.innerHTML = list.map((p) => {
  const img = p.image_url || (p.images && p.images[0]) || "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&q=80";
  const stock = p.stock || 0;
  return `
    <article class="tpl-card" data-open-id="${p.id}">
      <img src="${img}" alt="${p.name}" loading="lazy">
      <div class="tpl-card-body">
        <h3>${p.name}</h3>
        <div class="tpl-card-footer">
              <span class="tpl-price">${currencySymbol}${Number(p.price || 0).toFixed(2)}</span>
              <span>${stock > 0 ? "In stock" : "Out of stock"}</span>
            </div
            <button class="tpl-btn" style="width:100%;margin-top:10px" data-id="${p.id}" data-name="${p.name}" data-price="${p.price}" ${stock <= 0 ? "disabled" : ""}>
              Add to Cart
            </button>
          </div>
        </article>`;
    }).join("");


    // Clicking the card (but not its buttons) opens the product detail modal
    productsEl.querySelectorAll(".tpl-card").forEach((card) => {
      card.addEventListener("click", (e) => {
        if (e.target.closest("button")) return;
        const id = card.dataset.openId;
        const product = products.find((p) => String(p.id) === String(id));
        if (product) openProductModal(product);
      });
    });

    productsEl.querySelectorAll(".tpl-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        const cart = JSON.parse(localStorage.getItem("cart") || "[]");
        const id = btn.dataset.id;
        const existing = cart.find((i) => i.product_id === id);
        if (existing) existing.quantity += 1;
        else {
          cart.push({
            product_id: id,
            name: btn.dataset.name,
            price: parseFloat(btn.dataset.price),
            quantity: 1,
            store_id: store.id,
          });
        }
        localStorage.setItem("cart", JSON.stringify(cart));
        const toast = document.getElementById("tplToast");
        toast.style.display = "block";
        setTimeout(() => { toast.style.display = "none"; }, 2000);
      });
    });

    // Wishlist buttons
    productsEl.querySelectorAll(".tpl-wish-btn").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const token = localStorage.getItem("auth_token") || localStorage.getItem("token") || "";
        if (!token) {
          btn.textContent = "🔒";
          btn.title = "Login to save to wishlist";
          setTimeout(() => { btn.textContent = "♥"; btn.title = "Add to Wishlist"; }, 2000);
          return;
        }
        btn.textContent = "...";
        btn.disabled = true;
        try {
          const res = await fetch(`${API_BASE_URL}/wishlist`, {
            method: "POST",
            headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
            body: JSON.stringify({ product_id: btn.dataset.id })
          });
          const data = await res.json();
          if (data.success) {
            btn.textContent = "♥";
            btn.style.background = "#ef4444";
            btn.style.border = "1px solid #ef4444";
            btn.style.color = "#fff";
            btn.title = "Saved to Wishlist!";
          } else {
            btn.textContent = "♥";
            btn.disabled = false;
          }
        } catch(e) {
          btn.textContent = "♥";
          btn.disabled = false;
        }
      });
    });
  }

// ── Product detail modal ────────────────────────────────────────────────
  let modalEl = null;
  let modalSlideIdx = 0;
  let modalImages = [];

  function ensureModal() {
    if (modalEl) return modalEl;
    modalEl = document.createElement("div");
    modalEl.id = "tplProductModal";
    modalEl.innerHTML = `
      <div class="tpl-modal-backdrop"></div>
      <div class="tpl-modal-box">
        <button class="tpl-modal-close" type="button" aria-label="Close">✕</button>
        <div class="tpl-modal-slider">
          <button class="tpl-slide-nav tpl-slide-prev" type="button">‹</button>
          <img class="tpl-modal-img" src="" alt="">
          <button class="tpl-slide-nav tpl-slide-next" type="button">›</button>
          <div class="tpl-slide-dots"></div>
        </div>
        <div class="tpl-modal-body">
          <span class="tpl-modal-cat"></span>
          <h2 class="tpl-modal-title"></h2>
          <div class="tpl-modal-price"></div>
          <div class="tpl-modal-stock"></div>
          <p class="tpl-modal-desc"></p>
          <div class="tpl-modal-actions">
            <button class="tpl-btn tpl-modal-add" style="flex:1">Add to Cart</button>
            <button class="tpl-modal-wish" title="Add to Wishlist">♥</button>
          </div>
          <button class="tpl-modal-msg" type="button">💬 Message Seller</button>
        </div>
      </div>`;
    document.body.appendChild(modalEl);

    modalEl.querySelector(".tpl-modal-backdrop").addEventListener("click", closeProductModal);
    modalEl.querySelector(".tpl-modal-close").addEventListener("click", closeProductModal);
    modalEl.querySelector(".tpl-slide-prev").addEventListener("click", () => moveSlide(-1));
    modalEl.querySelector(".tpl-slide-next").addEventListener("click", () => moveSlide(1));
    document.addEventListener("keydown", (e) => {
      if (!modalEl.classList.contains("open")) return;
      if (e.key === "Escape") closeProductModal();
      if (e.key === "ArrowLeft") moveSlide(-1);
      if (e.key === "ArrowRight") moveSlide(1);
    });
    return modalEl;
  }

  function renderSlide() {
    if (!modalImages.length) return;
    modalEl.querySelector(".tpl-modal-img").src = modalImages[modalSlideIdx];
    const dots = modalEl.querySelector(".tpl-slide-dots");
    dots.innerHTML = modalImages.map((_, i) =>
      `<span class="tpl-slide-dot${i === modalSlideIdx ? " active" : ""}" data-idx="${i}"></span>`
    ).join("");
    dots.querySelectorAll(".tpl-slide-dot").forEach((d) => {
      d.addEventListener("click", () => { modalSlideIdx = parseInt(d.dataset.idx); renderSlide(); });
    });
    const showNav = modalImages.length > 1;
    modalEl.querySelector(".tpl-slide-prev").style.display = showNav ? "flex" : "none";
    modalEl.querySelector(".tpl-slide-next").style.display = showNav ? "flex" : "none";
  }

  function moveSlide(dir) {
    if (!modalImages.length) return;
    modalSlideIdx = (modalSlideIdx + dir + modalImages.length) % modalImages.length;
    renderSlide();
  }

  function openProductModal(p) {
    const m = ensureModal();
    modalImages = (p.images && p.images.length) ? p.images : [p.image_url || "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600&q=80"];
    modalSlideIdx = 0;
    renderSlide();

    const stock = p.stock || 0;
    m.querySelector(".tpl-modal-cat").textContent = p.category || "";
    m.querySelector(".tpl-modal-cat").style.display = p.category ? "inline-block" : "none";
    m.querySelector(".tpl-modal-title").textContent = p.name;
    m.querySelector(".tpl-modal-price").textContent = `$${Number(p.price || 0).toFixed(2)}`;
    m.querySelector(".tpl-modal-stock").textContent = stock > 0 ? `${stock} in stock` : "Out of stock";
    m.querySelector(".tpl-modal-stock").style.color = stock > 0 ? "var(--accent)" : "#ef4444";
    m.querySelector(".tpl-modal-desc").textContent = p.description || "No description provided.";

    const addBtn = m.querySelector(".tpl-modal-add");
    addBtn.disabled = stock <= 0;
    addBtn.onclick = () => {
      const cart = JSON.parse(localStorage.getItem("cart") || "[]");
      const existing = cart.find((i) => i.product_id === String(p.id));
      if (existing) existing.quantity += 1;
      else cart.push({ product_id: String(p.id), name: p.name, price: parseFloat(p.price), quantity: 1, store_id: store.id });
      localStorage.setItem("cart", JSON.stringify(cart));
      const toast = document.getElementById("tplToast");
      toast.style.display = "block";
      setTimeout(() => { toast.style.display = "none"; }, 2000);
    };

    const wishBtn = m.querySelector(".tpl-modal-wish");
    let wishItemId = null;

    function setWishVisual(active) {
      wishBtn.textContent = "♥";
      if (active) {
        wishBtn.style.background = "#ef4444"; wishBtn.style.borderColor = "#ef4444"; wishBtn.style.color = "#fff";
      } else {
        wishBtn.style.background = "transparent"; wishBtn.style.borderColor = "var(--accent)"; wishBtn.style.color = "var(--accent)";
      }
    }
    setWishVisual(false);
    wishBtn.disabled = false;

    // Check whether this product is already in the user's wishlist
    (async () => {
      const token = localStorage.getItem("auth_token") || localStorage.getItem("token") || "";
      if (!token) return;
      try {
        const res = await fetch(`${API_BASE_URL}/wishlist`, { headers: { Authorization: `Bearer ${token}` } });
        const resData = await res.json();
        if (resData.success) {
          const match = (resData.data || []).find((item) => String(item.product_id) === String(p.id));
          if (match) { wishItemId = match.id; setWishVisual(true); }
        }
      } catch (e) {}
    })();

    wishBtn.onclick = async () => {
      const token = localStorage.getItem("auth_token") || localStorage.getItem("token") || "";
      if (!token) {
        wishBtn.textContent = "🔒";
        setTimeout(() => { wishBtn.textContent = "♥"; }, 1500);
        return;
      }
      wishBtn.textContent = "...";
      wishBtn.disabled = true;
      try {
        if (wishItemId) {
          // already wishlisted -> remove it
          const res = await fetch(`${API_BASE_URL}/wishlist/${wishItemId}`, {
            method: "DELETE",
            headers: { Authorization: `Bearer ${token}` }
          });
          const resData = await res.json();
          if (resData.success) { wishItemId = null; setWishVisual(false); }
        } else {
          // not wishlisted yet -> add it
          const res = await fetch(`${API_BASE_URL}/wishlist`, {
            method: "POST",
            headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
            body: JSON.stringify({ product_id: p.id })
          });
          const resData = await res.json();
          if (resData.success && resData.data) { wishItemId = resData.data.id; setWishVisual(true); }
        }
      } catch (e) {}
      wishBtn.disabled = false;
      wishBtn.textContent = "♥";
    };

    // Message Seller — chat isn't wired up yet, this is the entry point for it.
    const msgBtn = m.querySelector(".tpl-modal-msg");
    msgBtn.onclick = () => {
      const token = localStorage.getItem("auth_token") || localStorage.getItem("token") || "";
      if (!token) { alert("Please log in to message the seller."); return; }
      window.location.href = `http://127.0.0.1:5000/customer-chat.html?store_id=${store.id}`;
    };

    m.classList.add("open");
    document.body.style.overflow = "hidden";
  }

  function closeProductModal() {
    if (!modalEl) return;
    modalEl.classList.remove("open");
    document.body.style.overflow = "";
  }

  renderProducts("");

  // Red dot notification check
  (async () => {
    const token = localStorage.getItem("auth_token") || localStorage.getItem("token") || "";
    if (!token) return;
    try {
      const res = await fetch(`${API_BASE_URL}/chat/unread-count`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      if (data.count > 0) {
        const dot = document.getElementById("tplChatDot");
        if (dot) dot.style.display = "block";
      }
    } catch(e) {}
  })();


})();