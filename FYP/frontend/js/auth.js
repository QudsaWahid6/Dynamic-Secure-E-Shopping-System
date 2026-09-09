function saveSession(token, user) {
  localStorage.setItem("token", token);
  localStorage.setItem("user", JSON.stringify(user));
}

function getToken() {
  return localStorage.getItem("token");
}

function getUser() {
  try {
    return JSON.parse(localStorage.getItem("user") || "null");
  } catch {
    return null;
  }
}

function logout() {
  localStorage.removeItem("token");
  localStorage.removeItem("user");
  localStorage.removeItem("cart");
  window.location.href = "login.html";
}

function handleUnauthorized() {
  localStorage.removeItem("token");
  localStorage.removeItem("user");
  alert("Session expired. Please login again.");
  window.location.href = "login.html";
}

function requireAuth(allowedRoles) {
  const token = getToken();
  const user = getUser();
  if (!token || !user) {
    window.location.href = "login.html";
    return null;
  }
  if (allowedRoles && !allowedRoles.includes(user.role)) {
    alert("You do not have access to this page.");
    redirectByRole(user.role);
    return null;
  }
  return user;
}

function redirectByRole(role) {
  const route = DASHBOARD_ROUTES[role] || "login.html";
  window.location.href = route;
}

function getInitials(name, email) {
  if (name) return name.split(" ").map(n => n[0]).join("").slice(0, 2).toUpperCase();
  return (email || "?")[0].toUpperCase();
}
