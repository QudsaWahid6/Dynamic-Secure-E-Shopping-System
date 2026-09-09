let CHAT_CURRENT_ROLE = null;
let CHAT_ACTIVE_CONVO = null;
let CHAT_CURRENT_USER = null;
let CHAT_POLL_INTERVAL = null;

function initChatPage(role) {
  CHAT_CURRENT_ROLE = role;
  CHAT_CURRENT_USER = JSON.parse(localStorage.getItem("user") || "{}");

  loadConversationList().then(() => {
    if (role === "customer") {
      const params = new URLSearchParams(window.location.search);
      const storeId = params.get("store_id");
      if (storeId) handleIncomingStoreId(storeId);
    }
  });

  document.getElementById("blockedListBtn").addEventListener("click", openBlockedListModal);

  document.getElementById("chatSendBtn").addEventListener("click", handleSendMessage);
  document.getElementById("chatInput").addEventListener("keydown", (e) => {
    if (e.key === "Enter") handleSendMessage();
  });

  // refresh conversation list + active thread every 4s (simple polling)
  CHAT_POLL_INTERVAL = setInterval(() => {
    loadConversationList(true);
    if (CHAT_ACTIVE_CONVO) loadThread(CHAT_ACTIVE_CONVO, true);
  }, 30000);
}

async function handleIncomingStoreId(storeId) {
  const res = await startConversation(storeId);
  if (!res.success) {
    if (res.blocked) alert(res.message);
    return;
  }
  await loadConversationList();
  openConversation(res.data);
}

async function loadConversationList(silent = false) {
  const res = await getConversations();
  const listEl = document.getElementById("chatList");
  if (!res.success) {
    if (!silent) listEl.innerHTML = '<div class="erp-empty">Could not load chats</div>';
    return;
  }
  const conversations = res.data || [];
  if (!conversations.length) {
    listEl.innerHTML = '<div class="erp-empty" style="padding:20px">No conversations yet</div>';
    return;
  }

  listEl.innerHTML = conversations.map(c => {
    const name = CHAT_CURRENT_ROLE === "customer"
      ? (c.stores ? c.stores.name : "Store")
      : (c.users ? c.users.name : "Customer");
    const lastMsg = c.last_message ? c.last_message.content : "No messages yet";
    const unread = c.unread_count > 0
      ? `<span style="background:#ef4444;color:#fff;border-radius:50%;width:18px;height:18px;display:inline-flex;align-items:center;justify-content:center;font-size:0.7rem">${c.unread_count}</span>`
      : "";
    const isActive = CHAT_ACTIVE_CONVO === c.id ? "background:#e0f2fe" : "background:#fff";
    return `
      <div class="chatListItem" data-id="${c.id}" style="padding:13px 16px;border-bottom:1px solid #f1f5f9;cursor:pointer;display:flex;justify-content:space-between;align-items:center;${isActive}">
        <div style="overflow:hidden">
          <div style="font-weight:600;font-size:0.9rem;color:#0f172a;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${name}</div>
          <div style="font-size:0.78rem;color:#64748b;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:220px">${lastMsg}</div>
        </div>
        ${unread}
      </div>
    `;
  }).join("");

  listEl.querySelectorAll(".chatListItem").forEach(item => {
    item.addEventListener("click", () => {
      const id = item.getAttribute("data-id");
      const convo = conversations.find(c => c.id === id);
      openConversation(convo);
    });
  });
}

function openConversation(convo) {
  CHAT_ACTIVE_CONVO = convo.id;
  const otherName = CHAT_CURRENT_ROLE === "customer"
    ? (convo.stores ? convo.stores.name : "Store")
    : (convo.users ? convo.users.name : "Customer");

  const headerEl = document.getElementById("chatHeader");
  headerEl.style.display = "flex";
  headerEl.style.justifyContent = "space-between";
  headerEl.style.alignItems = "center";
  headerEl.innerHTML = `
    <span style="font-weight:600;color:#f1f5f9">${otherName}</span>
    <div style="display:flex;gap:8px">
      <button id="chatBlockBtn" class="erp-btn" style="font-size:0.75rem;padding:5px 12px;background:#334155;color:#e2e8f0;border:none;border-radius:6px">Block</button>
      <button id="chatDeleteBtn" class="erp-btn" style="font-size:0.75rem;padding:5px 12px;background:#7f1d1d;color:#fff;border:none;border-radius:6px">Delete</button>
    </div>
  `;
  document.getElementById("chatInputBar").style.display = "block";

  document.getElementById("chatBlockBtn").addEventListener("click", async () => {
    if (!confirm("Block this user? They won't be able to message you.")) return;
    const otherId = convo.customer_id === CHAT_CURRENT_USER.id ? convo.owner_id : convo.customer_id;
    await blockUser(otherId);
    alert("User blocked.");
    loadConversationList();
  });

  document.getElementById("chatDeleteBtn").addEventListener("click", async () => {
    if (!confirm("Delete this chat?")) return;
    await deleteConversation(convo.id);
    CHAT_ACTIVE_CONVO = null;
    document.getElementById("chatThread").innerHTML = "";
    document.getElementById("chatHeader").style.display = "none";
    document.getElementById("chatInputBar").style.display = "none";
    loadConversationList();
  });

  loadThread(convo.id);
}

async function loadThread(conversationId, silent = false) {
  const res = await getMessages(conversationId);
  const threadEl = document.getElementById("chatThread");

  if (!res.success) {
    if (res.blocked) {
      threadEl.innerHTML = `<div class="erp-empty">${res.message}</div>`;
      document.getElementById("chatInputBar").style.display = "none";
    }
    return;
  }

  const messages = res.data || [];
  threadEl.innerHTML = messages.map(m => {
    const isMine = m.sender_id === CHAT_CURRENT_USER.id;
    return `
      <div style="display:flex;justify-content:${isMine ? "flex-end" : "flex-start"};margin-bottom:12px">
        <div style="max-width:60%;padding:10px 15px;border-radius:16px;${isMine ? "border-bottom-right-radius:4px" : "border-bottom-left-radius:4px"};background:${isMine ? "#0ea5e9" : "#334155"};color:#fff;font-size:0.88rem;box-shadow:0 1px 3px rgba(0,0,0,0.3)">
          ${m.content}
          <div style="font-size:0.65rem;color:${isMine ? "rgba(255,255,255,0.7)" : "#94a3b8"};margin-top:4px;text-align:right">${new Date(m.created_at).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}</div>
        </div>
      </div>
    `;
  }).join("");

  if (!silent) threadEl.scrollTop = threadEl.scrollHeight;
}

async function handleSendMessage() {
  if (!CHAT_ACTIVE_CONVO) return;
  const input = document.getElementById("chatInput");
  const content = input.value.trim();
  if (!content) return;

  const res = await sendMessage(CHAT_ACTIVE_CONVO, content);
  if (!res.success) {
    if (res.blocked) alert(res.message);
    return;
  }
  input.value = "";
  loadThread(CHAT_ACTIVE_CONVO);
  loadConversationList(true);
}

async function openBlockedListModal() {
  const res = await getBlockedUsers();
  const blocked = res.data || [];

  const existing = document.getElementById("blockedModal");
  if (existing) existing.remove();

  const modal = document.createElement("div");
  modal.id = "blockedModal";
  modal.style.cssText = "position:fixed;inset:0;background:rgba(0,0,0,0.6);display:flex;align-items:center;justify-content:center;z-index:999";
  modal.innerHTML = `
    <div class="erp-panel" style="width:380px;max-height:60vh;overflow-y:auto">
      <h3 style="margin-top:0">Blocked Users</h3>
      <div id="blockedListInner">
        ${blocked.length ? blocked.map(b => `
          <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.06)">
            <span>${b.users ? b.users.name : "User"}</span>
            <button class="erp-btn unblockBtn" data-id="${b.blocked_id}" style="font-size:0.75rem;padding:4px 10px">Unblock</button>
          </div>
        `).join("") : '<div class="erp-empty">No blocked users</div>'}
      </div>
      <button id="closeBlockedModal" class="erp-btn" style="margin-top:14px;width:100%">Close</button>
    </div>
  `;
  document.body.appendChild(modal);

  modal.querySelectorAll(".unblockBtn").forEach(btn => {
    btn.addEventListener("click", async () => {
      await unblockUser(btn.getAttribute("data-id"));
      openBlockedListModal();
    });
  });

  document.getElementById("closeBlockedModal").addEventListener("click", () => modal.remove());
}