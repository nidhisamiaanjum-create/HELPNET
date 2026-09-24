document.addEventListener("DOMContentLoaded", async function () {
    if (typeof requireLogin === "function" && !requireLogin()) {
        return;
    }

    const user = typeof getStoredUser === "function"
        ? getStoredUser()
        : null;

    if (!user || !user.role || user.role.toLowerCase() !== "admin") {
        window.location.href = "/dashboard/";
        return;
    }

    await loadAdminLogs();

    document
        .getElementById("logoutButton")
        ?.addEventListener("click", function () {
            if (typeof logout === "function") {
                logout();
            }
        });
});


async function loadAdminLogs() {
    const container = document.getElementById("logsContainer");

    if (!container) {
        return;
    }

    const token = localStorage.getItem("helpnet_token");

    if (!token) {
        window.location.href = "/login/";
        return;
    }

    try {
        const response = await fetch(
            "/api/verification/admin/logs/",
            {
                method: "GET",
                headers: {
                    Authorization: `Bearer ${token}`
                }
            }
        );

        const payload = await response.json();

        if (!response.ok) {
            throw new Error(
                payload.message || "Could not load admin logs."
            );
        }

        renderAdminLogs(payload.data || []);

    } catch (error) {
        console.error("Failed to load admin logs:", error);

        container.innerHTML = `
            <p class="form-error">
                Admin logs could not be loaded.
            </p>
        `;
    }
}


function renderAdminLogs(logs) {
    const container = document.getElementById("logsContainer");

    if (!container) {
        return;
    }

    container.replaceChildren();

    if (!logs.length) {
        const emptyMessage = document.createElement("p");
        emptyMessage.textContent = "No admin activity found.";
        container.appendChild(emptyMessage);
        return;
    }

    logs.forEach(function (log) {
        const card = document.createElement("div");
        card.className = "card";

        const action = document.createElement("h3");
        action.textContent = log.action_label || log.action;

        const admin = document.createElement("p");
        admin.textContent =
            `Admin: ${log.admin_name || "—"}`;

        const target = document.createElement("p");
        target.textContent =
            `Target User: ${log.target_user || "—"}`;

        const reason = document.createElement("p");
        reason.textContent =
            `Reason: ${log.reason || "—"}`;

        const reference = document.createElement("p");
        reference.textContent =
            `Reference: ${log.target_reference || "—"}`;

        const timestamp = document.createElement("p");
        timestamp.textContent =
            `Time: ${formatLogTime(log.timestamp)}`;

        card.appendChild(action);
        card.appendChild(admin);
        card.appendChild(target);
        card.appendChild(reason);
        card.appendChild(reference);
        card.appendChild(timestamp);

        container.appendChild(card);
    });
}


function formatLogTime(value) {
    if (!value) {
        return "—";
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return value;
    }

    return date.toLocaleString();
}