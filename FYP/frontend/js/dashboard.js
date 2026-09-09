async function loadOwnerDashboardStats() {
  const res = await getDashboard();
  if (!res.success) return null;
  return {
    store: res.store,
    theme: res.theme,
    stats: res.stats,
    products: res.products,
    orders: res.orders,
  };
}

async function loadAdminDashboardStats() {
  const res = await getAdminStats();
  return res.success ? res.stats : null;
}

async function loadCustomerDashboardStats() {
  const [orders, wish, stores] = await Promise.all([getOrders(), getWishlist(), getStores()]);
  return {
    orderCount: orders.success ? orders.data.length : 0,
    wishCount: wish.success ? wish.data.length : 0,
    storeCount: stores.success ? stores.data.length : 0,
    cartCount: typeof getCart === "function" ? getCart().length : 0,
  };
}
