/* Return to the previous HELPNET page when one is available. The link's href
   remains the safe parent-page fallback for direct opens and external referrers. */
document.addEventListener("click", event => {
    const target = event.target instanceof Element ? event.target : null;
    const link = target?.closest("a[data-smart-back]");
    if (!link || event.defaultPrevented || event.button !== 0 ||
        event.metaKey || event.ctrlKey || event.shiftKey || event.altKey ||
        (link.target && link.target !== "_self")) {
        return;
    }

    let referrer;
    try {
        referrer = new URL(document.referrer);
    } catch {
        return;
    }

    if (referrer.origin === window.location.origin && window.history.length > 1) {
        event.preventDefault();
        window.history.back();
    }
});

function updateNotificationBadge(unreadCount) {
    const badge = document.querySelector(".notification-unread-badge");
    if (badge) {
        badge.textContent = unreadCount > 99 ? "99+" : String(unreadCount);
        badge.hidden = unreadCount === 0;
    }
    const dashboardCount = document.getElementById("notificationCount");
    if (dashboardCount) dashboardCount.textContent = String(unreadCount);
}

async function refreshNotificationBadge() {
    if (typeof getToken !== "function" || !getToken() || typeof apiRequest !== "function") return;
    try {
        const response = await apiRequest("/api/notifications/");
        const unreadCount = (response.data || []).filter(item => !item.is_read).length;
        updateNotificationBadge(unreadCount);
    } catch (error) {
        // Keep navigation usable when the notification service is temporarily unavailable.
    }
}

document.addEventListener("DOMContentLoaded", () => {
    if (typeof getToken !== "function" || !getToken()) return;
    const header = document.querySelector(".site-header");
    if (!header) return;
    let link = header.querySelector(".notification-nav-link");
    if (!link) {
        link = document.createElement("a");
        link.href = "/notifications/";
        link.className = "notification-nav-link";
        link.setAttribute("aria-label", "Notifications");
        link.title = "Notifications";
        link.textContent = "\u{1F514}";
        const actions = header.querySelector(".header-actions, nav");
        (actions || header).appendChild(link);
    }
    let badge = link.querySelector(".notification-unread-badge");
    if (!badge) {
        badge = document.createElement("span");
        badge.className = "notification-unread-badge";
        badge.setAttribute("aria-live", "polite");
        badge.setAttribute("aria-label", "Unread notifications");
        badge.hidden = true;
        link.appendChild(badge);
    }
    refreshNotificationBadge();
    window.setInterval(refreshNotificationBadge, 30000);
    window.addEventListener("focus", refreshNotificationBadge);
    window.addEventListener("helpnet:notifications-updated", refreshNotificationBadge);
});
