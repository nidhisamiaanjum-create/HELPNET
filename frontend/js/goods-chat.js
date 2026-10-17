function goodsChatNotice(id, message, type = "") {
    const node = document.getElementById(id); if (!node) return;
    node.textContent = message; node.className = `form-message ${type}`;
}
function goodsChatId() { return new URLSearchParams(location.search).get("conversation_id"); }
function renderGoodsMessages(messages) {
    const history = document.getElementById("chatHistory"); history.replaceChildren();
    if (!messages.length) { const empty = document.createElement("p"); empty.className = "hint"; empty.textContent = "No messages yet. Start the conversation."; history.appendChild(empty); return; }
    const current = getStoredUser();
    messages.forEach(item => {
        const row = document.createElement("article"); row.className = "admin-item";
        const who = document.createElement("strong"); who.textContent = current && String(item.sender_id) === String(current.user_id || current.id) ? "You" : item.sender_name;
        const body = document.createElement("p"); body.textContent = item.message;
        const time = document.createElement("time"); time.dateTime = item.created_at; time.textContent = new Date(item.created_at).toLocaleString();
        row.append(who, body, time); history.appendChild(row);
    });
}
async function loadGoodsConversation() {
    const id = goodsChatId(); if (!id || !/^\d+$/.test(id)) return goodsChatNotice("chatMessage", "Conversation link is missing a valid ID.", "error");
    try {
        const response = await apiRequest(`/api/goods/conversations/${encodeURIComponent(id)}/`);
        document.getElementById("chatTitle").textContent = response.data.listing_title;
        document.getElementById("chatOther").textContent = `Conversation with ${response.data.other_user_name}`;
        document.getElementById("chatListingLink").href = `/goods-details/?listing_id=${encodeURIComponent(response.data.listing_id)}`;
        renderGoodsMessages(response.data.messages); goodsChatNotice("chatMessage", "");
    } catch (error) { goodsChatNotice("chatMessage", error.message, "error"); }
}
async function sendGoodsMessage(event) {
    event.preventDefault(); const button = document.getElementById("chatSend"); const input = document.getElementById("chatInput");
    const message = input.value.trim(); if (!message) return goodsChatNotice("chatMessage", "Enter a message before sending.", "error");
    button.disabled = true;
    try { await apiRequest(`/api/goods/conversations/${encodeURIComponent(goodsChatId())}/`, "POST", {message}); input.value = ""; await loadGoodsConversation(); }
    catch (error) { goodsChatNotice("chatMessage", error.message, "error"); }
    finally { button.disabled = false; }
}
async function loadGoodsConversations() {
    try {
        const response = await apiRequest("/api/goods/conversations/"); const list = document.getElementById("conversationList"); list.replaceChildren();
        if (!response.data.length) { const empty = document.createElement("p"); empty.className = "hint"; empty.textContent = "You have no goods conversations."; list.appendChild(empty); return; }
        response.data.forEach(item => { const row = document.createElement("article"); row.className = "admin-item";
            const title = document.createElement("h2"); title.textContent = item.listing_title;
            const person = document.createElement("p"); person.textContent = `With ${item.other_user_name}`;
            const preview = document.createElement("p"); preview.textContent = item.latest_message || "No messages yet.";
            const time = document.createElement("time"); time.dateTime = item.latest_message_at; time.textContent = new Date(item.latest_message_at).toLocaleString();
            const link = document.createElement("a"); link.className = "small-btn"; link.href = item.url; link.textContent = "Open conversation";
            row.append(title, person, preview, time, link); list.appendChild(row);
        });
    } catch (error) { goodsChatNotice("conversationsMessage", error.message, "error"); }
}
document.addEventListener("DOMContentLoaded", () => {
    if (!requireLogin()) return;
    if (document.getElementById("chatHistory")) { document.getElementById("chatForm").addEventListener("submit", sendGoodsMessage); document.getElementById("chatRefresh").addEventListener("click", loadGoodsConversation); loadGoodsConversation(); window.setInterval(loadGoodsConversation, 10000); }
    if (document.getElementById("conversationList")) loadGoodsConversations();
});
