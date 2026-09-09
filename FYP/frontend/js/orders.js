const ORDER_FLOW = {
  pending: ["shipped", "cancelled"],
  shipped: ["delivered", "cancelled"],
  delivered: [],
  cancelled: [],
};

const COLUMN_COLORS = {
  pending: "#ef4444",
  shipped: "#38bdf8",
  delivered: "#22c55e",
  cancelled: "#94a3b8",
};

function renderOrderItems(items) {
  if (!items || !items.length) return `<div style="color:#64748b;font-size:0.78rem;margin-top:6px">No item details</div>`;
  return `<div style="margin-top:8px;border-top:1px solid rgba(255,255,255,0.07);padding-top:8px">
    ${items.map(i => {
      const name = (i.products && i.products.name) || i.product_id || "Item";
      const img = i.products && i.products.image_url;
      return `<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;font-size:0.8rem">
        ${img ? `<img src="${img}" style="width:32px;height:32px;object-fit:cover;border-radius:6px">` : ""}
        <span style="flex:1">${name}</span>
        <span style="color:#94a3b8">×${i.quantity}</span>
        <span style="color:#38bdf8">$${Number(i.price || 0).toFixed(2)}</span>
      </div>`;
    }).join("")}
  </div>`;
}
// === YE NAYA FUNCTION ADD KAREIN (renderOrderItems ke baad, renderOrderBoard se pehle) ===
function renderPaymentBadge(o) {
  const isOnline = o.payment_method === "online";
  const label = isOnline ? "💳 Online" : "💵 Cash on Delivery";
  const color = isOnline ? "#38bdf8" : "#94a3b8";
  let extra = "";
  if (isOnline) {
    extra = o.receipt_image_url
      ? ` <span style="color:#4ade80">· receipt attached</span>`
      : ` <span style="color:#f87171">· no receipt on file</span>`;
  }
  return `<div style="margin-top:4px;font-size:0.78rem;color:${color}">${label}${extra}</div>`;
}

function renderOrderBoard(container, orders, { onStatusChange } = {}) {
  const columns = ["pending", "shipped", "delivered", "cancelled"];

  // Order ID search bar
  const searchBar = `
    <div style="margin-bottom:16px;display:flex;gap:10px;align-items:center">
      <input id="orderSearch" class="erp-input" placeholder="Search Order ID..." style="max-width:280px;padding:8px 12px">
      <button class="erp-btn erp-btn-secondary" id="orderSearchBtn">Lookup</button>
      <span id="orderSearchResult" style="color:#94a3b8;font-size:0.85rem"></span>
    </div>`;

  container.innerHTML = searchBar + `
    <div style="display:flex;gap:16px;overflow-x:auto;align-items:flex-start">
      ${columns.map(col => {
        const colOrders = orders.filter(o => (o.status || "pending") === col);
        return `
          <div style="flex:1;min-width:240px;background:#0f172a;border-radius:10px;padding:12px">
            <h3 style="color:${COLUMN_COLORS[col]};text-transform:capitalize;margin-bottom:10px;font-size:0.95rem">
              ${col} (${colOrders.length})
            </h3>
            <div style="display:flex;flex-direction:column;gap:8px">
              ${colOrders.length ? colOrders.map(o => `
                <div style="background:#1e293b;border-radius:8px;padding:10px;font-size:0.85rem" data-order-card="${o.id}">
                  <div style="display:flex;justify-content:space-between;align-items:center">
                    <span style="font-weight:600">#${String(o.id).slice(0, 8)}</span>
                    <button class="erp-btn erp-btn-sm details-toggle" data-order="${o.id}" style="padding:2px 8px;font-size:0.75rem">▼ Details</button>
                  </div>
                  <div style="color:#94a3b8;margin-top:4px">${formatPrice(o.total_amount)} · ${formatDate(o.created_at)}</div>
                  <div style="color:#cbd5e1;margin-top:4px;font-size:0.78rem">📍 ${o.shipping_address || "No address on file"} · 📞 ${o.shipping_phone || "No phone on file"}</div>
                  ${renderPaymentBadge(o)}
                  <div class="order-details" id="details-${o.id}" style="display:none">
                    ${renderOrderItems(o.items)}
                  </div>
                  <div style="margin-top:8px;display:flex;gap:6px;flex-wrap:wrap">
                    ${ORDER_FLOW[col].map(next => `
                      <button class="erp-btn erp-btn-sm" data-order="${o.id}" data-next="${next}">
                        ${next === "cancelled" ? "Cancel" : "Move to " + next.charAt(0).toUpperCase() + next.slice(1)}
                      </button>
                    `).join("")}
                    <button class="erp-btn erp-btn-sm erp-btn-secondary" onclick="window.open('customer-receipt.html?order_id=${o.id}','_blank')">🧾 Receipt</button>
                  </div>
                </div>
              `).join("") : `<div style="color:#64748b;font-size:0.8rem">No orders</div>`}
            </div>
          </div>
        `;
      }).join("")}
    </div>
  `;

  // Toggle details panels
  container.querySelectorAll(".details-toggle").forEach(btn => {
    btn.addEventListener("click", () => {
      const panel = document.getElementById(`details-${btn.dataset.order}`);
      if (panel) {
        const open = panel.style.display !== "none";
        panel.style.display = open ? "none" : "block";
        btn.textContent = open ? "▼ Details" : "▲ Hide";
      }
    });
  });

  // Status change buttons
  container.querySelectorAll("[data-next]").forEach(btn => {
    btn.addEventListener("click", () => onStatusChange(btn.dataset.order, btn.dataset.next));
  });

  // Order ID lookup
  const searchBtn = document.getElementById("orderSearchBtn");
  const searchInput = document.getElementById("orderSearch");
  const resultEl = document.getElementById("orderSearchResult");
  if (searchBtn) {
    searchBtn.addEventListener("click", () => {
      const term = searchInput.value.trim().toLowerCase();
      if (!term) { resultEl.textContent = ""; return; }
      // Remove previous highlights
      container.querySelectorAll("[data-order-card]").forEach(el => el.style.outline = "");
      const match = orders.find(o => o.id.toLowerCase().includes(term));
      if (match) {
        const el = container.querySelector(`[data-order-card="${match.id}"]`);
        if (el) {
          el.style.outline = "2px solid #38bdf8";
          el.scrollIntoView({ behavior: "smooth", block: "center" });
          resultEl.textContent = `Found: #${match.id.slice(0, 8)}`;
          // auto-open details
          const panel = document.getElementById(`details-${match.id}`);
          if (panel) panel.style.display = "block";
        }
      } else {
        resultEl.textContent = "No match found.";
      }
    });
    searchInput.addEventListener("keydown", e => { if (e.key === "Enter") searchBtn.click(); });
  }
}
function getCart() {
  try { return JSON.parse(localStorage.getItem("cart") || "[]"); } catch { return []; }
}

function saveCart(cart) {
  localStorage.setItem("cart", JSON.stringify(cart));
}

function addToCart(product, storeId) {
  const cart = getCart();
  const existing = cart.find(i => i.product_id === product.id);
  if (existing) existing.quantity += 1;
  else cart.push({ product_id: product.id, name: product.name, price: product.price, quantity: 1, store_id: storeId });
  saveCart(cart);
}
