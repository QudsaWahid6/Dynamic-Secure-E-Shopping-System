function renderProductTable(container, products, { onEdit, onDelete } = {}) {
  if (!products.length) {
    container.innerHTML = `<div class="erp-empty">No products found.</div>`;
    return;
  }
  container.innerHTML = `
    <div class="erp-table-wrap">
      <table class="erp-table">
        <thead><tr>
          <th>Name</th><th>Category</th><th>Price</th><th>Stock</th><th>Actions</th>
        </tr></thead>
        <tbody>
          ${products.map(p => `
            <tr>
              <td><strong>${p.name}</strong><br><small style="color:#94a3b8">${p.description || ""}</small></td>
              <td>${p.category || "—"}</td>
              <td>${formatPrice(p.price)}</td>
              <td>${p.stock ?? 0}</td>
              <td>
                <button class="erp-btn erp-btn-secondary erp-btn-sm" data-edit="${p.id}">Edit</button>
                <button class="erp-btn erp-btn-danger erp-btn-sm" data-del="${p.id}">Delete</button>
              </td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
  `;
  container.querySelectorAll("[data-edit]").forEach(btn => btn.addEventListener("click", () => onEdit(btn.dataset.edit)));
  container.querySelectorAll("[data-del]").forEach(btn => btn.addEventListener("click", () => onDelete(btn.dataset.del)));
}
