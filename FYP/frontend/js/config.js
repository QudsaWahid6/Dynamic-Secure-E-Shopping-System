// If someone opens this page by double-clicking the file (file:// protocol),
// auto-redirect to the same page served through Flask — so localStorage/cart/
// session all live under one consistent origin instead of breaking silently.
if (window.location.protocol === "file:") {
  const samePage = window.location.pathname.split("/").pop();
  window.location.href = "http://127.0.0.1:5000/" + samePage + window.location.search;
}
const API_BASE = "http://127.0.0.1:5000";

const DASHBOARD_ROUTES = {
  super_admin: "admin-dashboard.html",
  store_owner: "store-owner-dashboard.html",
  customer: "customer-dashboard.html",
};

const NAV_CONFIG = {
  super_admin: [
    { href: "admin-dashboard.html", label: "Dashboard", icon: "📊" },
    { href: "admin-users.html", label: "User Management", icon: "👥" },
    { href: "admin-stores.html", label: "Store Management", icon: "🏪" },
    { href: "admin-themes.html", label: "Theme Analytics", icon: "🎨" },
    { href: "admin-analytics.html", label: "System Analytics", icon: "📈" },
    { href: "admin-activity.html", label: "Activity Logs", icon: "📋" },
    { href: "admin-settings.html", label: "Settings", icon: "⚙️" },
  ],
  store_owner: [
    { href: "store-owner-dashboard.html", label: "Dashboard", icon: "📊" },
    { href: "owner-products.html", label: "Products", icon: "📦" },
    { href: "owner-orders.html", label: "Orders", icon: "🛒" },
    { href: "owner-inventory.html", label: "Inventory", icon: "📋" },
    { href: "owner-themes.html", label: "Theme Management", icon: "🎨" },
    { href: "owner-theme-generator.html", label: "AI Generator", icon: "✨" },
    { href: "owner-theme-library.html", label: "Theme Library", icon: "📚" },
    { href: "owner-analytics.html", label: "Analytics", icon: "📈" },
    { href: "owner-chat.html", label: "Chat", icon: "💬" },
    { href: "owner-settings.html", label: "Store Settings", icon: "⚙️" },
  ],
  customer: [
    { href: "customer-dashboard.html", label: "Dashboard", icon: "📊" },
    { href: "customer-profile.html", label: "Profile", icon: "👤" },
    { href: "customer-orders.html", label: "Orders", icon: "🛒" },
    { href: "customer-cart.html", label: "Cart", icon: "🛍️" },
    { href: "customer-wishlist.html", label: "Wishlist", icon: "❤️" },
    { href: "customer-stores.html", label: "Store Discovery", icon: "🔍" },
    { href: "customer-theme-preview.html", label: "Theme Preview", icon: "🎨" },
    { href: "customer-chat.html", label: "Chat", icon: "💬" },
    { href: "customer-settings.html", label: "Settings", icon: "⚙️" },
  ],
};
