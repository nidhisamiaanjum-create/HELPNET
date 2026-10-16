let healthQuestionsLoadPromise = null;

function healthMessage(message, type = "") {
    const element = document.getElementById("healthMessage");
    if (!element) return;
    element.textContent = message;
    element.className = `form-message ${type}`;
}

function healthText(parent, tag, text, className = "") {
    const element = document.createElement(tag);
    element.textContent = text ?? "";
    if (className) element.className = className;
    parent.appendChild(element);
    return element;
}

function healthDate(value) {
    return value ? new Date(value).toLocaleString() : "";
}

function healthQuestionId() {
    return new URLSearchParams(window.location.search).get("question_id");
}

async function loadHealthQuestions() {
    if (healthQuestionsLoadPromise) return healthQuestionsLoadPromise;
    const target = document.getElementById("healthQuestions");
    healthQuestionsLoadPromise = (async () => {
        try {
            const response = await apiRequest("/api/health/questions/");
            target.replaceChildren();
            if (!response.data.length) return healthText(target, "p", "No health questions yet.", "hint");
            const fragment = document.createDocumentFragment();
            const seen = new Set();
            response.data.forEach(question => {
                if (seen.has(String(question.id))) return;
                seen.add(String(question.id));
                const card = document.createElement("article");
                card.className = "admin-item";
                healthText(card, "h2", question.title);
                healthText(card, "p", `Category: ${question.category}`);
                healthText(card, "p", `By ${question.author_name} · ${healthDate(question.created_at)}`);
                const link = healthText(card, "a", "", "small-btn");
                link.href = `/health-question-details/?question_id=${encodeURIComponent(question.id)}`;
                link.dataset.i18n = "openQuestion";
                link.textContent =
                    typeof t === "function" ? t("openQuestion") : "Open question";

                // Add a line break before the link
                card.appendChild(document.createElement("br"));
                fragment.appendChild(card);
            });
            target.appendChild(fragment);
        } catch (error) {
            healthMessage(error.message, "error");
        }
    })();
    return healthQuestionsLoadPromise;
}

async function createHealthQuestion(event) {
    event.preventDefault();
    const form = event.currentTarget;
    if (form.dataset.submitting === "true") return;
    form.dataset.submitting = "true";
    const submitButton = form.querySelector("[type=submit]");
    if (submitButton) submitButton.disabled = true;
    try {
        const response = await apiRequest("/api/health/questions/", "POST", {
            title: document.getElementById("healthTitle").value.trim(),
            description: document.getElementById("healthDescription").value.trim(),
            category: document.getElementById("healthCategory").value.trim(),
        });
        healthMessage(response.message || "Question created.", "success");
        window.location.href = `/health-question-details/?question_id=${encodeURIComponent(response.data.id)}`;
    } catch (error) {
        healthMessage(error.message, "error");
        form.dataset.submitting = "false";
        if (submitButton) submitButton.disabled = false;
    }
}

async function loadHealthQuestionDetails() {
    const id = healthQuestionId();
    const target = document.getElementById("healthQuestionDetails");
    if (!id || !/^\d+$/.test(id)) return healthMessage("A valid question ID is required.", "error");
    try {
        const response = await apiRequest(`/api/health/questions/${encodeURIComponent(id)}/`);
        const question = response.data;
        target.replaceChildren();
        healthText(target, "h1", question.title);
        healthText(target, "p", `Category: ${question.category}`);
        healthText(target, "p", `Asked by ${question.author_name} · ${healthDate(question.created_at)}`);
        if (question.author_is_verified) healthText(target, "span", "Verified", "badge");
        healthText(target, "p", question.description);
        document.getElementById("healthReplyForm").dataset.questionId = question.id;
        await loadHealthReplies(id);
    } catch (error) {
        healthMessage(error.message, "error");
    }
}

async function loadHealthReplies(id = healthQuestionId()) {
    const target = document.getElementById("healthReplies");
    try {
        const response = await apiRequest(`/api/health/questions/${encodeURIComponent(id)}/replies/`);
        target.replaceChildren();
        if (!response.data.length) return healthText(target, "p", "No replies yet.", "hint");
        response.data.forEach(reply => {
            const card = document.createElement("article");
            card.className = "admin-item";
            const heading = healthText(card, "h3", `${reply.author_name} · ${healthDate(reply.created_at)}`);
            if (reply.author_is_verified) healthText(heading, "span", " Verified", "badge");
            const average = reply.author_average_rating === null ? "No ratings yet" : `${Number(reply.author_average_rating).toFixed(1)} / 5 (${reply.author_rating_count} ratings)`;
            healthText(card, "p", `Community rating: ${average}`, "hint");
            healthText(card, "p", reply.reply);
            target.appendChild(card);
        });
    } catch (error) {
        healthMessage(error.message, "error");
    }
}

async function submitHealthReply(event) {
    event.preventDefault();
    const form = event.currentTarget;
    if (form.dataset.submitting === "true") return;
    form.dataset.submitting = "true";
    const submitButton = form.querySelector("[type=submit]");
    if (submitButton) submitButton.disabled = true;
    const questionId = form.dataset.questionId || healthQuestionId();
    try {
        const response = await apiRequest(`/api/health/questions/${encodeURIComponent(questionId)}/replies/`, "POST", {
            reply: document.getElementById("healthReply").value.trim(),
        });
        document.getElementById("healthReply").value = "";
        healthMessage(response.message || "Reply added.", "success");
        await loadHealthReplies(questionId);
    } catch (error) {
        healthMessage(error.message, "error");
    } finally {
        form.dataset.submitting = "false";
        if (submitButton) submitButton.disabled = false;
    }
}

async function loadHealthProfessionals() {
    const target = document.getElementById("healthProfessionals");
    try {
        const response = await apiRequest("/api/health/professionals/");
        target.replaceChildren();
        target.removeAttribute("data-i18n");
        if (!response.data.length) {
            const empty = healthText(target, "p", typeof t === "function" ? t("healthDirectoryEmpty") : "No approved professionals listed yet.", "hint");
            empty.dataset.i18n = "healthDirectoryEmpty";
            return;
        }
        response.data.forEach(professional => {
            const card = document.createElement("article");
            card.className = "admin-item";
            const nameRow = document.createElement("div");
            nameRow.className = "health-professional-name-row";
            healthText(nameRow, "h2", professional.name);
            const badge = healthText(nameRow, "span", "", "badge");
            badge.dataset.i18n = "healthVerifiedBadge";
            card.appendChild(nameRow);
            healthAddLabeledValue(card, "healthDirectoryProfession", professional.profession);
            if (professional.specialization) healthAddLabeledValue(card, "healthDirectorySpecialization", professional.specialization);
            if (professional.location) healthAddLabeledValue(card, "healthDirectoryLocation", professional.location);
            if (professional.contact) {
                const contact = document.createElement("p");
                const label = document.createElement("strong");
                label.dataset.i18n = "healthDirectoryContact";
                label.textContent = typeof t === "function" ? t("healthDirectoryContact") : "Contact directly";
                contact.append(label, document.createTextNode(": "));
                const value = String(professional.contact).trim();
                let href = "";
                if (/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) href = `mailto:${value}`;
                else if (/^[+()\d.\s-]+$/.test(value)) href = `tel:${value.replace(/[^+\d]/g, "")}`;
                if (href) {
                    const link = document.createElement("a");
                    link.href = href;
                    link.textContent = value;
                    contact.appendChild(link);
                } else {
                    contact.appendChild(document.createTextNode(value));
                }
                card.appendChild(contact);
            }
            target.appendChild(card);
        });
        if (typeof applyLanguage === "function") applyLanguage();
    } catch (error) {
        healthMessage(error.message, "error");
    }
}

function healthAddLabeledValue(parent, key, value) {
    const row = document.createElement("p");
    const label = document.createElement("strong");
    label.dataset.i18n = key;
    label.textContent = typeof t === "function" ? t(key) : key;
    row.append(label, document.createTextNode(`: ${value}`));
    parent.appendChild(row);
}

function healthApplicationStatusKey(status) {
    return ({
        not_submitted: "healthStatusNotSubmitted",
        pending: "healthStatusPending",
        verified: "healthStatusApproved",
        rejected: "healthStatusRejected",
    })[status] || "healthStatusNotSubmitted";
}

async function loadHealthProfessionalApplication() {
    const section = document.getElementById("healthProfessionalApplication");
    const form = document.getElementById("healthApplicationForm");
    if (!section || !form) return;
    const user = typeof getStoredUser === "function" ? getStoredUser() : null;
    if (String(user?.role || "").toLowerCase() !== "citizen") return;
    section.hidden = false;
    try {
        const response = await apiRequest("/api/health/professionals/application/");
        const application = response.data;
        const statusKey = healthApplicationStatusKey(application.status);
        const statusElement = document.getElementById("healthApplicationStatus");
        statusElement.replaceChildren();
        const statusLabel = document.createElement("span");
        statusLabel.dataset.i18n = statusKey;
        statusLabel.textContent = typeof t === "function" ? t(statusKey) : application.status;
        statusElement.appendChild(statusLabel);
        if (application.status === "rejected" && application.rejection_reason) {
            statusElement.appendChild(document.createTextNode(` ${application.rejection_reason}`));
        }
        ["name", "profession", "specialization", "location", "contact", "credential_type", "credential_number"].forEach(field => {
            const input = document.getElementById(({name:"healthProfessionalName",profession:"healthProfession",specialization:"healthSpecialization",location:"healthLocation",contact:"healthContact",credential_type:"healthCredentialType",credential_number:"healthCredentialNumber"})[field]);
            if (input && application[field]) input.value = application[field];
        });
        form.hidden = application.status === "pending" || application.status === "verified";
        if (typeof applyLanguage === "function") applyLanguage();
    } catch (error) {
        healthMessage(error.message, "error");
    }
}

async function submitHealthProfessionalApplication(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const button = document.getElementById("submitHealthApplication");
    const payload = new FormData();
    payload.append("name", document.getElementById("healthProfessionalName").value.trim());
    payload.append("profession", document.getElementById("healthProfession").value.trim());
    payload.append("specialization", document.getElementById("healthSpecialization").value.trim());
    payload.append("location", document.getElementById("healthLocation").value.trim());
    payload.append("contact", document.getElementById("healthContact").value.trim());
    payload.append("credential_type", document.getElementById("healthCredentialType").value.trim());
    payload.append("credential_number", document.getElementById("healthCredentialNumber").value.trim());
    const file = document.getElementById("healthCredentialDocument").files[0];
    if (file) payload.append("credential_document", file);
    if (button) button.disabled = true;
    try {
        await apiRequest("/api/health/professionals/application/", "POST", payload);
        form.reset();
        await loadHealthProfessionalApplication();
    } catch (error) {
        healthMessage(error.message, "error");
    } finally {
        if (button) button.disabled = false;
    }
}

document.addEventListener("DOMContentLoaded", () => {
    if (!requireLogin()) return;
    if (document.getElementById("healthQuestions")) loadHealthQuestions();
    document.getElementById("healthQuestionForm")?.addEventListener("submit", createHealthQuestion);
    if (document.getElementById("healthQuestionDetails")) loadHealthQuestionDetails();
    document.getElementById("healthReplyForm")?.addEventListener("submit", submitHealthReply);
    if (document.getElementById("healthProfessionals")) loadHealthProfessionals();
    if (document.getElementById("healthProfessionalApplication")) loadHealthProfessionalApplication();
    document.getElementById("healthApplicationForm")?.addEventListener("submit", submitHealthProfessionalApplication);
});
