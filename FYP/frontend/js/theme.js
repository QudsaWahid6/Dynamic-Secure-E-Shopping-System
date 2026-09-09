function renderThemeCards(container, themes) {
  if (!themes.length) {
    container.innerHTML = `<div class="erp-empty">No themes saved yet. Generate one with AI.</div>`;
    return;
  }
  container.innerHTML = themes.map(t => {
    const palette = t.color_palette || {};
    const primary = palette.primary || "#2563eb";
    const secondary = palette.secondary || "#06b6d4";
    const accent = palette.accent || "#38bdf8";
    const bgUrl = t.background_image_url || "";
    const layout = t.layout_style || "grid";
    return `
      <div class="erp-card" style="margin-bottom:16px">
        <h3 style="color:#38bdf8;margin-bottom:8px">${t.theme_name || "Untitled Theme"}</h3>
        <p style="color:#94a3b8;font-size:0.85rem;margin-bottom:12px">
          ${layout} layout · ${t.font_style || "Inter"} · ${formatDate(t.generated_at)}
          ${t.ai_generated ? " · 🤖 Gemini" : ""}
        </p>
        ${bgUrl ? `<div style="height:100px;border-radius:10px;margin-bottom:12px;background:url('${bgUrl}') center/cover"></div>` : ""}
        <div style="display:flex;gap:8px;margin-bottom:12px">
          <div style="width:40px;height:40px;border-radius:8px;background:${primary}"></div>
          <div style="width:40px;height:40px;border-radius:8px;background:${secondary}"></div>
          <div style="width:40px;height:40px;border-radius:8px;background:${accent}"></div>
        </div>
        <p style="font-size:0.8rem;color:#64748b">Template: dynamic-store.html — JSON drives colors, hero bg, layout</p>
      </div>
    `;
  }).join("");
}
