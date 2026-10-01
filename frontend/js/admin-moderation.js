function moderationMessage(message, type = "") {
    const target = document.getElementById("moderationMessage");
    target.textContent = message;
    target.className = `form-message ${type}`;
}

function moderationButton(label, action, callback) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = action === "remove" ? "btn-xs btn-danger" : "small-btn";
    button.textContent = label;
    button.addEventListener("click", callback);
    return button;
}

async function submitModeration(payload) {
    try {
        await apiRequest("/api/reports/moderation/", "POST", payload);
        moderationMessage(t(payload.action === "remove" ? "moderationRemoved" : payload.action === "review" ? "moderationReviewed" : "moderationSaved"), "success");
        await loadModerationReports();
    } catch (error) {
        moderationMessage(t("moderationFailed"), "error");
    }
}

async function loadModerationReports() {
    const container = document.getElementById("moderationReports");
    try {
        const response = await apiRequest("/api/reports/");
        container.replaceChildren();
        if (!response.data.length) {
            const empty = document.createElement("p");
            empty.className = "hint";
            empty.textContent = t("moderationEmpty");
            container.appendChild(empty);
            return;
        }
        response.data.forEach((report) => {
            const card = document.createElement("article");
            card.className = "admin-item";
            const title = document.createElement("h2");
            const statusKey = `reportStatus${report.status.charAt(0).toUpperCase()}${report.status.slice(1)}`;
            title.textContent = `${report.category === "fraud" ? t("reportFraud") : report.category === "other" ? t("reportOther") : report.category} · ${t(statusKey)}`;
            card.appendChild(title);
            const description = document.createElement("p");
            description.textContent = report.description;
            card.appendChild(description);
            if (report.content_type && report.object_id) {
                const target = document.createElement("p");
                const typeKeys = {
                    "blood.bloodrequest": "bloodPageTitle",
                    "goods.goodslisting": "moderationGoods",
                    "farmer.producelisting": "moderationFarmer",
                    "volunteer.volunteeropportunity": "moderationVolunteer",
                };
                target.textContent = `${t(typeKeys[report.content_type] || "moderationContentType")} #${report.object_id}: ${report.content_summary || ""}`;
                card.appendChild(target);
            }
            const reason = document.createElement("input");
            reason.type = "text";
            reason.maxLength = 1000;
            reason.placeholder = t("moderationReason");
            card.appendChild(reason);
            if (report.status === "pending") {
                card.appendChild(moderationButton(t("moderationReview"), "review", () => submitModeration({ report_id: report.id, action: "review", reason: reason.value })));
            }
            if (report.content_type && report.object_id) {
                const changes = document.createElement("textarea");
                changes.placeholder = t("moderationChanges");
                card.appendChild(changes);
                const actions = document.createElement("div");
                actions.className = "admin-actions";
                actions.appendChild(moderationButton(t("moderationEdit"), "edit", () => {
                    let parsed;
                    try { parsed = JSON.parse(changes.value); }
                    catch (_) { moderationMessage(t("moderationInvalidChanges"), "error"); return; }
                    submitModeration({ report_id: report.id, action: "edit", changes: parsed, reason: reason.value });
                }));
                actions.appendChild(moderationButton(t("moderationRemove"), "remove", () => submitModeration({ report_id: report.id, action: "remove", reason: reason.value })));
                card.appendChild(actions);
            }
            container.appendChild(card);
        });
    } catch (error) {
        moderationMessage(t("moderationLoadFailed"), "error");
    }
}

async function loadModerationContent() {
    const container = document.getElementById("moderationContentItems");
    const contentType = document.getElementById("moderationContentType").value;
    try {
        const response = await apiRequest(`/api/reports/moderation/?content_type=${encodeURIComponent(contentType)}`);
        container.replaceChildren();
        response.data.forEach((item) => {
            const card = document.createElement("article");
            card.className = "admin-item";
            const title = document.createElement("h3");
            title.textContent = `${item.summary} · #${item.id}`;
            card.appendChild(title);
            const changes = document.createElement("textarea");
            changes.value = JSON.stringify(item.editable, null, 2);
            changes.setAttribute("aria-label", t("moderationChanges"));
            card.appendChild(changes);
            const reason = document.createElement("input");
            reason.placeholder = t("moderationReason");
            card.appendChild(reason);
            const actions = document.createElement("div");
            actions.className = "admin-actions";
            actions.appendChild(moderationButton(t("moderationEdit"), "edit", () => {
                let parsed;
                try { parsed = JSON.parse(changes.value); }
                catch (_) { moderationMessage(t("moderationInvalidChanges"), "error"); return; }
                submitModeration({ content_type: contentType, object_id: item.id, action: "edit", changes: parsed, reason: reason.value });
            }));
            actions.appendChild(moderationButton(t("moderationRemove"), "remove", () => submitModeration({
                content_type: contentType, object_id: item.id, action: "remove", reason: reason.value,
            })));
            card.appendChild(actions);
            container.appendChild(card);
        });
    } catch (error) {
        moderationMessage(t("moderationLoadFailed"), "error");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const user = typeof getStoredUser === "function" ? getStoredUser() : null;
    if (!user || !(user.role === "Admin" || user.is_staff === true || user.is_superuser === true)) {
        moderationMessage(t("adminAccessRequired"), "error");
        return;
    }
    document.getElementById("logoutButton")?.addEventListener("click", () => logout());
    document.getElementById("moderationContentType")?.addEventListener("change", loadModerationContent);
    document.addEventListener("helpnet:languagechange", () => {
        loadModerationReports();
        loadModerationContent();
    });
    loadModerationReports();
    loadModerationContent();
});
