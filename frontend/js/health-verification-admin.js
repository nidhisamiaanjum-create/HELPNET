function healthAdminLabel(key, fallback) {
    return typeof t === "function" ? t(key) : fallback;
}

function healthAdminAddField(parent, key, fallback, value) {
    const row = document.createElement("p");
    const label = document.createElement("strong");
    label.dataset.i18n = key;
    label.textContent = healthAdminLabel(key, fallback);
    row.append(label, document.createTextNode(`: ${value || "—"}`));
    parent.appendChild(row);
}

async function loadHealthProfessionalApplications() {
    const target = document.getElementById("healthProfessionalApplications");
    if (!target) return;
    target.replaceChildren();
    try {
        const response = await apiRequest("/api/health/professionals/admin/pending/");
        if (!response.data.length) {
            const empty = document.createElement("p");
            empty.dataset.i18n = "healthAdminEmpty";
            empty.textContent = healthAdminLabel("healthAdminEmpty", "No applications are waiting for review.");
            target.appendChild(empty);
            if (typeof applyLanguage === "function") applyLanguage();
            return;
        }

        response.data.forEach(application => {
            const card = document.createElement("article");
            card.className = "admin-item";
            const name = document.createElement("h3");
            name.textContent = application.name;
            card.appendChild(name);
            healthAdminAddField(card, "healthDirectoryProfession", "Profession", application.profession);
            healthAdminAddField(card, "healthDirectorySpecialization", "Specialization", application.specialization);
            healthAdminAddField(card, "healthDirectoryLocation", "Location", application.location);
            healthAdminAddField(card, "healthCredentialType", "Credential type", application.credential_type);
            healthAdminAddField(card, "healthCredentialNumberLabel", "Credential number", application.credential_number);
            healthAdminAddField(card, "phone", "Phone", application.applicant_phone);

            const actions = document.createElement("div");
            actions.className = "admin-actions";
            const documentLink = document.createElement("a");
            documentLink.href = "#";
            documentLink.className = "small-btn";
            documentLink.dataset.i18n = "healthViewCredential";
            documentLink.textContent = healthAdminLabel("healthViewCredential", "View credential");
            documentLink.addEventListener("click", async event => {
                event.preventDefault();
                try {
                    await downloadAdminDocument(application.document_url, application.document_name || `health-credential-${application.id}`);
                } catch (error) {
                    alert(error.message || healthAdminLabel("healthDocumentFailed", "Could not download the credential."));
                }
            });
            actions.appendChild(documentLink);

            const approve = document.createElement("button");
            approve.type = "button";
            approve.className = "small-btn";
            approve.dataset.i18n = "healthApprove";
            approve.textContent = healthAdminLabel("healthApprove", "Approve");
            approve.addEventListener("click", () => reviewHealthApplication(application.id, "approve", ""));
            actions.appendChild(approve);

            const reject = document.createElement("button");
            reject.type = "button";
            reject.className = "small-btn danger-btn";
            reject.dataset.i18n = "healthReject";
            reject.textContent = healthAdminLabel("healthReject", "Reject");
            actions.appendChild(reject);
            card.appendChild(actions);

            const rejection = document.createElement("div");
            rejection.className = "health-rejection-controls";
            rejection.hidden = true;
            const reason = document.createElement("textarea");
            reason.required = true;
            reason.maxLength = 2000;
            reason.dataset.i18nPlaceholder = "healthRejectReason";
            reason.placeholder = healthAdminLabel("healthRejectReason", "Enter a reason for rejection");
            rejection.appendChild(reason);
            const confirm = document.createElement("button");
            confirm.type = "button";
            confirm.className = "small-btn danger-btn";
            confirm.dataset.i18n = "healthConfirmReject";
            confirm.textContent = healthAdminLabel("healthConfirmReject", "Confirm rejection");
            confirm.addEventListener("click", () => {
                const value = reason.value.trim();
                if (!value) {
                    reason.focus();
                    reason.setCustomValidity("A rejection reason is required.");
                    reason.reportValidity();
                    return;
                }
                reviewHealthApplication(application.id, "reject", value);
            });
            reason.addEventListener("input", () => reason.setCustomValidity(""));
            rejection.appendChild(confirm);
            reject.addEventListener("click", () => { rejection.hidden = !rejection.hidden; });
            card.appendChild(rejection);
            target.appendChild(card);
        });
        if (typeof applyLanguage === "function") applyLanguage();
    } catch (error) {
        const message = document.createElement("p");
        message.className = "form-error";
        message.textContent = error.message;
        target.replaceChildren(message);
    }
}

async function reviewHealthApplication(id, action, reason) {
    try {
        await apiRequest(`/api/health/professionals/${encodeURIComponent(id)}/verification/`, "PATCH", {action, reason});
        await loadHealthProfessionalApplications();
    } catch (error) {
        alert(error.message || healthAdminLabel("healthApplicationReviewed", "Could not review this application."));
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const target = document.getElementById("healthProfessionalApplications");
    if (!target) return;
    if (typeof requireLogin === "function" && !requireLogin()) return;
    const user = typeof getStoredUser === "function" ? getStoredUser() : null;
    if (String(user?.role || "").toLowerCase() !== "admin") return;
    loadHealthProfessionalApplications();
});
