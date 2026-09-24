function showNotificationMessage(message, type = "") {
    const element = document.getElementById("notificationMessage");
    if (!element) return;
    element.textContent = message;
    element.className = `form-message ${type}`;
}

function renderNotifications(notifications) {
    const list = document.getElementById("notificationList");
    list.replaceChildren();
    if (!notifications.length) {
        const empty = document.createElement("p");
        empty.className = "hint notification-empty";
        empty.textContent = "You have no notifications.";
        list.appendChild(empty);
        return;
    }

    notifications.forEach((notification) => {
        const item = document.createElement("article");
        item.className = `notification-item${notification.is_read ? "" : " unread"}`;
        const content = document.createElement("div");
        const message = document.createElement("p");
        message.textContent = notification.message;
        const date = document.createElement("time");
        date.dateTime = notification.created_at;
        date.textContent = new Date(notification.created_at).toLocaleString();
        content.append(message, date);
        item.appendChild(content);

        if (!notification.is_read) {
            const button = document.createElement("button");
            button.type = "button";
            button.className = "small-btn notification-read-button";
            button.textContent = "Mark as read";
            button.addEventListener("click", () => markNotificationRead(notification.id));
            item.appendChild(button);
        } else {
            const status = document.createElement("span");
            status.className = "notification-status";
            status.textContent = "Read";
            item.appendChild(status);
        }
        list.appendChild(item);
    });
}

async function loadNotifications() {
    try {
        const response = await apiRequest("/api/notifications/");
        renderNotifications(response.data || []);
        showNotificationMessage("");
    } catch (error) {
        showNotificationMessage(error.message, "error");
    }
}

async function markNotificationRead(notificationId) {
    try {
        await apiRequest(`/api/notifications/${notificationId}/read/`, "POST");
        showNotificationMessage("Notification marked as read.", "success");
        await loadNotifications();
    } catch (error) {
        showNotificationMessage(error.message, "error");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    if (!getToken()) {
        window.location.href = "/login/";
        return;
    }
    document.getElementById("refreshNotifications").addEventListener("click", loadNotifications);
    loadNotifications();
});
