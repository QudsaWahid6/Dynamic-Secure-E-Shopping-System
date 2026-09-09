function initERPLayout({ title, activePage, allowedRoles }) {
  const user = requireAuth(allowedRoles);
  if (!user) return null;

  document.body.classList.add("erp-body");

  const navItems = NAV_CONFIG[user.role] || [];
  const navHtml = navItems.map(item => `
    <a href="${item.href}" class="${activePage === item.href ? "active" : ""}">
      <span>${item.icon}</span> ${item.label}
    </a>
  `).join("");

  const initials = getInitials(user.name, user.email);
  const avatarUrl = user.profile_image_url;

  const shell = document.createElement("div");
  shell.className = "erp-app";
  shell.innerHTML = `
    <aside class="erp-sidebar">
      <div class="erp-brand">ERP Commerce</div>
      <div class="erp-role-badge">${(user.role || "").replace("_", " ")}</div>
      <nav class="erp-nav">${navHtml}</nav>
    </aside>
    <div class="erp-main">
      <header class="erp-topbar">
        <h1>${title || "Dashboard"}</h1>
        <div class="erp-profile">
          <button class="erp-profile-btn" id="profileBtn" type="button">
            <div class="erp-avatar">${avatarUrl ? `<img src="${avatarUrl}" alt="" style="width:100%;height:100%;border-radius:50%;object-fit:cover">` : initials}</div>
            <div>
              <div style="font-weight:600;text-align:left">${user.name || "User"}</div>
              <div style="font-size:0.75rem;color:#94a3b8;text-align:left">${user.email || ""}</div>
            </div>
          </button>
          <div class="erp-profile-menu" id="profileMenu">
            <a href="${user.role === "customer" ? "customer-chat.html" : (user.role === "store_owner" ? "owner-chat.html" : "#")}">💬 Chat</a>
            <a href="${user.role === "customer" ? "customer-profile.html" : (user.role === "store_owner" ? "owner-settings.html" : "admin-settings.html")}">Settings</a>
            <button type="button" id="logoutBtn">Logout</button>
          </div>
        </div>
      </header>
      <main class="erp-content" id="erpPageContent"></main>
    </div>
  `;

  const existing = document.getElementById("page-root");
  if (existing) {
    const content = existing.innerHTML;
    document.body.innerHTML = "";
    document.body.appendChild(shell);
    document.getElementById("erpPageContent").innerHTML = content;
  } else {
    document.body.insertBefore(shell, document.body.firstChild);
  }

  document.getElementById("profileBtn").addEventListener("click", () => {
    document.getElementById("profileMenu").classList.toggle("open");
  });

  document.getElementById("logoutBtn").addEventListener("click", logout);

  document.addEventListener("click", (e) => {
    const menu = document.getElementById("profileMenu");
    const btn = document.getElementById("profileBtn");
    if (menu && btn && !menu.contains(e.target) && !btn.contains(e.target)) {
      menu.classList.remove("open");
    }
  });

  return user;
}

function showAlert(container, message, type = "error") {
  const el = document.createElement("div");
  el.className = `erp-alert erp-alert-${type}`;
  el.textContent = message;
  container.prepend(el);
  setTimeout(() => el.remove(), 5000);
}

function statusBadge(status) {
  const map = { pending: "badge-pending", shipped: "badge-shipped", delivered: "badge-delivered", cancelled: "badge-cancelled" };
  return `<span class="erp-badge ${map[status] || "badge-pending"}">${status || "pending"}</span>`;
}

function formatDate(d) {
  if (!d) return "—";
  return new Date(d).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
}

function formatPrice(p) {
  return `$${Number(p || 0).toFixed(2)}`;
}
