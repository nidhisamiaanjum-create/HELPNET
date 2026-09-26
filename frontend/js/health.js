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
                const link = healthText(card, "a", "Open question", "small-btn");
                link.href = `/health-question-details/?question_id=${encodeURIComponent(question.id)}`;
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
    const questionId = event.currentTarget.dataset.questionId || healthQuestionId();
    try {
        const response = await apiRequest(`/api/health/questions/${encodeURIComponent(questionId)}/replies/`, "POST", {
            reply: document.getElementById("healthReply").value.trim(),
        });
        document.getElementById("healthReply").value = "";
        healthMessage(response.message || "Reply added.", "success");
        await loadHealthReplies(questionId);
    } catch (error) {
        healthMessage(error.message, "error");
    }
}

async function loadHealthProfessionals() {
    const target = document.getElementById("healthProfessionals");
    try {
        const response = await apiRequest("/api/health/professionals/");
        target.replaceChildren();
        if (!response.data.length) return healthText(target, "p", "No professionals listed yet.", "hint");
        response.data.forEach(professional => {
            const card = document.createElement("article");
            card.className = "admin-item";
            healthText(card, "h2", professional.name);
            healthText(card, "p", `Profession: ${professional.profession}`);
            if (professional.specialization) healthText(card, "p", `Specialization: ${professional.specialization}`);
            if (professional.location) healthText(card, "p", `Location: ${professional.location}`);
            if (professional.contact) healthText(card, "p", `Contact: ${professional.contact}`);
            healthText(card, "p", professional.is_verified ? "Admin verified" : "Not admin verified", professional.is_verified ? "badge" : "hint");
            if (professional.average_rating !== null) healthText(card, "p", `Community rating: ${Number(professional.average_rating).toFixed(1)} / 5 (${professional.rating_count} ratings)`);
            target.appendChild(card);
        });
    } catch (error) {
        healthMessage(error.message, "error");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    if (!requireLogin()) return;
    if (document.getElementById("healthQuestions")) loadHealthQuestions();
    document.getElementById("healthQuestionForm")?.addEventListener("submit", createHealthQuestion);
    if (document.getElementById("healthQuestionDetails")) loadHealthQuestionDetails();
    document.getElementById("healthReplyForm")?.addEventListener("submit", submitHealthReply);
    if (document.getElementById("healthProfessionals")) loadHealthProfessionals();
});
