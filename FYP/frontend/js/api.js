async function apiRequest(endpoint, method = "GET", data = null, token = null) {
  const options = {
    method,
    headers: { "Content-Type": "application/json" },
  };

  const authToken = token || (typeof getToken === "function" ? getToken() : null);
  if (authToken) options.headers["Authorization"] = `Bearer ${authToken}`;

  if (data && method !== "GET") options.body = JSON.stringify(data);

  let response;
  try {
    response = await fetch(`${API_BASE}${endpoint}`, options);
  } catch (err) {
    return { success: false, error: "Network failure. Is the backend running?", network: true };
  }

  let json;
  try {
    json = await response.json();
  } catch {
    return { success: false, error: "Invalid server response", status: response.status };
  }

  if (response.status === 401) {
    if (typeof handleUnauthorized === "function") handleUnauthorized();
    return { ...json, unauthorized: true };
  }

  json.status = response.status;
  return json;
}

async function loginUser(email, password) {
  return apiRequest("/login", "POST", { email, password });
}

async function registerUser(name, email, password, role) {
  return apiRequest("/signup", "POST", { name, email, password, role });
}

async function getProfile() {
  return apiRequest("/profile");
}

async function updateProfile(data) {
  return apiRequest("/profile", "PUT", data);
}

async function getDashboard() {
  return apiRequest("/dashboard");
}

async function getAdminStats() {
  return apiRequest("/admin/stats");
}

async function getAdminUsers() {
  return apiRequest("/admin/users");
}

async function getAdminStores() {
  return apiRequest("/admin/stores");
}

async function getAdminActivity() {
  return apiRequest("/admin/activity");
}

async function getStores() {
  return apiRequest("/stores");
}

async function createStore(data) {
  return apiRequest("/stores", "POST", data);
}

async function updateStore(storeId, data) {
  return apiRequest(`/stores/${storeId}`, "PATCH", data);
}

async function getProducts(params = {}) {
  const qs = new URLSearchParams(params).toString();
  return apiRequest(`/products${qs ? "?" + qs : ""}`);
}

async function createProduct(data) {
  return apiRequest("/products", "POST", data);
}

async function updateProduct(id, data) {
  return apiRequest(`/products/${id}`, "PUT", data);
}

async function deleteProduct(id) {
  return apiRequest(`/products/${id}`, "DELETE");
}

async function getInventory() {
  return apiRequest("/inventory");
}

async function getOrders() {
  return apiRequest("/orders");
}

async function createOrder(data) {
  return apiRequest("/orders", "POST", data);
}

async function updateOrderStatus(id, status) {
  return apiRequest(`/orders/${id}/status`, "PATCH", { status });
}

async function getThemes(storeId) {
  const qs = storeId ? `?store_id=${storeId}` : "";
  return apiRequest(`/themes${qs}`);
}

async function generateTheme(data) {
  return apiRequest("/themes/generate", "POST", data);
}

function getStoreLiveUrl(storeId) {
  return `${API_BASE}/store-live/${storeId}`;
}

async function getWishlist() {
  return apiRequest("/wishlist");
}

async function addToWishlist(productId) {
  return apiRequest("/wishlist", "POST", { product_id: productId });
}

async function removeFromWishlist(id) {
  return apiRequest(`/wishlist/${id}`, "DELETE");
}

async function getCategories() {
  return apiRequest("/categories");
}

async function getProductCategories(storeId) {
  return apiRequest(`/product-categories?store_id=${storeId}`);
}

async function createProductCategory(name, storeId) {
  return apiRequest("/product-categories", "POST", { name, store_id: storeId });
}

async function deleteProductCategory(id) {
  return apiRequest(`/product-categories/${id}`, "DELETE");
}

async function suggestProductCategory(data) {
  return apiRequest("/products/suggest-category", "POST", data);
}


async function uploadImageToImgBB(file) {
  const IMGBB_KEY = "636ccaece741485ef51c8eaca5b734c1"; // get free key from imgbb.com/api
  const formData = new FormData();
  formData.append("image", file);
  try {
    const res = await fetch(`https://api.imgbb.com/1/upload?key=${IMGBB_KEY}`, {
      method: "POST", body: formData
    });
    const data = await res.json();
    return data.success ? data.data.url : null;
  } catch(e) {
    return null;
  }
}

async function updateTheme(themeId, data) {
  return apiRequest(`/themes/${themeId}`, "PATCH", data);
}

async function getConversations() {
  return apiRequest("/chat/conversations");
}

async function startConversation(storeId) {
  return apiRequest("/chat/conversations", "POST", { store_id: storeId });
}

async function deleteConversation(conversationId) {
  return apiRequest(`/chat/conversations/${conversationId}`, "DELETE");
}

async function getMessages(conversationId) {
  return apiRequest(`/chat/conversations/${conversationId}/messages`);
}

async function sendMessage(conversationId, content) {
  return apiRequest(`/chat/conversations/${conversationId}/messages`, "POST", { content });
}

async function getUnreadCount() {
  return apiRequest("/chat/unread-count");
}

async function blockUser(userId) {
  return apiRequest("/chat/block", "POST", { user_id: userId });
}

async function unblockUser(userId) {
  return apiRequest(`/chat/block/${userId}`, "DELETE");
}

async function getBlockedUsers() {
  return apiRequest("/chat/blocked");
}

async function getAdminUsers() {
  return apiRequest("/admin/users");
}

async function clearSecurityLogs() {
  return apiRequest("/admin/clear-logs", "POST");
}

async function getStorePaymentInfo(storeId) {
  return apiRequest(`/stores/${storeId}/payment-info`);
}