const bloodState = {
    requests: [],
    donors: [],
    currentUserId: null,
};

function bloodMessage(message, type = "") {
    const element = document.getElementById("bloodMessage");
    if (!element) return;
    element.textContent = message;
    element.className = `form-message ${type}`;
}

function populateBloodGroups() {
    const select = document.getElementById("requestGroup");
    if (!select) return;
    select.replaceChildren();
    addText(select, "option", t("selectBloodGroup")).value = "";
    ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"].forEach((group) => {
        const option = document.createElement("option");
        option.value = group;
        option.textContent = group;
        select.appendChild(option);
    });
}

function populateSearchOptions() {
    const select = document.getElementById("searchGroup");
    if (!select) return;
    ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"].forEach((group) => {
        const option = document.createElement("option");
        option.value = group;
        option.textContent = group;
        select.appendChild(option);
    });
}

function addText(parent, tag, text, className = "") {
    const element = document.createElement(tag);
    element.textContent = text;
    if (className) element.className = className;
    parent.appendChild(element);
    return element;
}

async function loadDonorProfile() {
    try {
        const response = await apiRequest("/api/blood/donor-profile/");
        const profile = response.data;
        document.getElementById("bloodGroup").value = profile.blood_group;
        document.getElementById("donorArea").value = profile.area;
        document.getElementById("donorAvailable").checked = profile.is_available;
    } catch (error) {
        if (!error.message.includes("Not found")) bloodMessage(error.message, "error");
    }
}

async function saveDonorProfile(event) {
    event.preventDefault();
    try {
        await apiRequest("/api/blood/donor-profile/", "PUT", {
            blood_group: document.getElementById("bloodGroup").value,
            area: document.getElementById("donorArea").value,
            is_available: document.getElementById("donorAvailable").checked,
        });
        bloodMessage(t("donorProfileSaved"), "success");
        await loadRequests();
    } catch (error) {
        bloodMessage(error.message, "error");
    }
}

async function createBloodRequest(event) {
    event.preventDefault();
    try {
        await apiRequest("/api/blood/requests/", "POST", {
            blood_group: document.getElementById("requestGroup").value,
            area: document.getElementById("requestArea").value,
            hospital: document.getElementById("hospital").value.trim(),
            details: document.getElementById("requestDetails").value.trim(),
        });
        event.target.reset();
        bloodMessage(t("bloodRequestCreated"), "success");
        await loadRequests();
    } catch (error) {
        bloodMessage(error.message, "error");
    }
}

async function showMatches(requestId, container) {
    try {
        const response = await apiRequest(`/api/blood/requests/${requestId}/matches/`);
        container.replaceChildren();
        addText(container, "strong", t("matchingDonors"));
        if (!response.data.length) {
            addText(container, "p", t("noMatchingDonors"), "hint");
            return;
        }
        const select = document.createElement("select");
        select.className = "donor-match-select";
        addText(select, "option", t("chooseDonor")).value = "";
        response.data.forEach((donor) => {
            const option = document.createElement("option");
            option.value = donor.user_id;
            option.textContent = `${donor.full_name} · ${donor.blood_group} · ${donor.area}`;
            select.appendChild(option);
        });
        container.appendChild(select);
        const complete = document.createElement("button");
        complete.type = "button";
        complete.className = "small-btn";
        complete.textContent = t("fulfillRequest");
        complete.addEventListener("click", () => completeRequest(requestId, select.value));
        container.appendChild(complete);
    } catch (error) {
        bloodMessage(error.message, "error");
    }
}

async function completeRequest(requestId, donorId) {
    if (!donorId) {
        bloodMessage(t("chooseDonor"), "error");
        return;
    }
    try {
        await apiRequest(`/api/blood/requests/${requestId}/complete/`, "POST", { donor_id: donorId });
        bloodMessage(t("bloodRequestFulfilled"), "success");
        await loadRequests();
        await loadHistory();
    } catch (error) {
        bloodMessage(error.message, "error");
    }
}

async function closeRequest(requestId) {
    try {
        await apiRequest(`/api/blood/requests/${requestId}/close/`, "POST");
        bloodMessage(t("bloodRequestClosed"), "success");
        await loadRequests();
    } catch (error) {
        bloodMessage(error.message, "error");
    }
}

function renderRequests(requests) {
    const list = document.getElementById("requestList");
    list.replaceChildren();
    if (!requests.length) {
        addText(list, "p", t("noOpenRequests"), "hint");
        return;
    }
    requests.forEach((item) => {
        const card = document.createElement("article");
        card.className = "blood-request-item";
        addText(card, "h3", `${item.blood_group} · ${item.area}`);
        addText(card, "p", `${item.hospital} · ${t("requestedBy")} ${item.requester_name}`);
        if (item.details) addText(card, "p", item.details, "hint");
        const actions = document.createElement("div");
        actions.className = "blood-request-actions";
        if (item.requester_id === bloodState.currentUserId) {
            const matches = document.createElement("div");
            matches.className = "match-panel";
            const matchButton = document.createElement("button");
            matchButton.type = "button";
            matchButton.className = "small-btn";
            matchButton.textContent = t("findMatchingDonors");
            matchButton.addEventListener("click", () => showMatches(item.id, matches));
            actions.append(matchButton, matches);
            const close = document.createElement("button");
            close.type = "button";
            close.className = "small-btn danger-btn";
            close.textContent = t("closeRequest");
            close.addEventListener("click", () => closeRequest(item.id));
            actions.appendChild(close);
        } else {
            const reportForm = document.createElement("form");
            reportForm.className = "blood-report-form";
            reportForm.innerHTML = `<label>${t("bloodReport")}<textarea maxlength="2000" required aria-label="${t("bloodReportReason")}" placeholder="${t("bloodReportReason")}"></textarea></label><button class="small-btn danger-btn" type="submit">${t("bloodReportSubmit")}</button><p class="form-message" aria-live="polite"></p>`;
            reportForm.addEventListener("submit", async (event) => {
                event.preventDefault();
                const textarea = reportForm.querySelector("textarea");
                const feedback = reportForm.querySelector(".form-message");
                try {
                    await apiRequest(`/api/blood/requests/${encodeURIComponent(item.id)}/reports/`, "POST", { description: textarea.value.trim() });
                    feedback.textContent = t("bloodReportSuccess");
                    feedback.className = "form-message success";
                    textarea.disabled = true;
                    reportForm.querySelector("button").disabled = true;
                } catch (error) {
                    feedback.textContent = t("bloodReportFailed");
                    feedback.className = "form-message error";
                }
            });
            actions.appendChild(reportForm);
        }
        card.appendChild(actions);
        list.appendChild(card);
    });
}

async function loadRequests() {
    try {
        const response = await apiRequest("/api/blood/requests/");
        bloodState.requests = response.data;
        renderRequests(response.data);
    } catch (error) {
        bloodMessage(error.message, "error");
    }
}

async function loadHistory() {
    try {
        const response = await apiRequest("/api/blood/donations/");
        const list = document.getElementById("historyList");
        list.replaceChildren();
        if (!response.data.length) {
            addText(list, "p", t("noDonationsRecorded"), "hint");
            return;
        }
        response.data.forEach((item) => {
            const row = document.createElement("article");
            row.className = "history-item";
            addText(row, "strong", `${item.blood_group} · ${item.area}`);
            addText(row, "p", `${item.hospital} · ${new Date(item.donated_at).toLocaleDateString(getLanguage() === "bn" ? "bn-BD" : "en-BD")}`);
            list.appendChild(row);
        });
    } catch (error) {
        bloodMessage(error.message, "error");
    }
}

function renderDonorSearchResults(donors) {
    bloodState.donors = donors;
    const list = document.getElementById("donorSearchResults");
    list.replaceChildren();
    if (!donors.length) {
        addText(list, "p", "No available donors found.", "hint");
        return;
    }
    donors.forEach((donor) => {
        const card = document.createElement("article");
        card.className = "blood-request-item donor-result";
        const name = document.createElement("h3");
        name.textContent = donor.full_name;
        if (donor.is_verified) addText(name, "span", ` ✓ ${t("verified")}`, "donor-verified");
        card.appendChild(name);
        addText(card, "p", `${donor.blood_group} · ${donor.area}`);
        addText(card, "p", `★ ${donor.average_rating === null ? "0.0" : Number(donor.average_rating).toFixed(1)} · ${t("ratingsCount").replace("{count}", donor.rating_count)}`);
        if (donor.user_id === bloodState.currentUserId) {
            addText(card, "span", t("yourDonorProfile"), "hint");
        } else {
            const link = document.createElement("a");
            link.className = "small-btn donor-rate-link";
            link.href = `/ratings/?user_id=${encodeURIComponent(donor.user_id)}`;
            link.textContent = t("rateDonor");
            card.appendChild(link);
        }
        list.appendChild(card);
    });
}

async function searchDonors(event) {
    event.preventDefault();
    const params = new URLSearchParams();
    const group = document.getElementById("searchGroup").value;
    const area = document.getElementById("searchArea").value;
    const search = document.getElementById("donorSearch").value.trim();
    if (group) params.set("blood_group", group);
    if (area) params.set("area", area);
    if (search) params.set("search", search);
    try {
        const response = await apiRequest(`/api/blood/donors/?${params.toString()}`);
        renderDonorSearchResults(response.data);
    } catch (error) {
        bloodMessage(error.message, "error");
    }
}

document.addEventListener("DOMContentLoaded", async () => {
    if (!getToken()) {
        window.location.href = "/login/";
        return;
    }
    bloodState.currentUserId = getStoredUser()?.user_id || null;
    populateDistricts("donorArea");
    populateDistricts("requestArea");
    populateDistricts("searchArea");
    populateBloodGroups();
    populateSearchOptions();
    document.getElementById("donorProfileForm").addEventListener("submit", saveDonorProfile);
    document.getElementById("requestForm").addEventListener("submit", createBloodRequest);
    document.getElementById("refreshRequests").addEventListener("click", loadRequests);
    document.getElementById("refreshHistory").addEventListener("click", loadHistory);
    document.getElementById("donorSearchForm").addEventListener("submit", searchDonors);
    if (new URLSearchParams(window.location.search).get("section") === "search") {
        const searchSection = document.getElementById("donorSearchSection");
        searchSection?.scrollIntoView({ behavior: "smooth", block: "start" });
        document.getElementById("donorSearch")?.focus();
    }
    await loadDonorProfile();
    await loadRequests();
    await loadHistory();
});

document.addEventListener("helpnet:languagechange", () => {
    renderRequests(bloodState.requests);
    if (bloodState.donors.length) renderDonorSearchResults(bloodState.donors);
    if (document.getElementById("historyList")) loadHistory();
});
