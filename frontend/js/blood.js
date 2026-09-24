const bloodState = {
    requests: [],
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
    select.innerHTML = '<option value="">Select blood group</option>';
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
        bloodMessage("Donor profile saved.", "success");
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
        bloodMessage("Blood request created.", "success");
        await loadRequests();
    } catch (error) {
        bloodMessage(error.message, "error");
    }
}

async function showMatches(requestId, container) {
    try {
        const response = await apiRequest(`/api/blood/requests/${requestId}/matches/`);
        container.replaceChildren();
        addText(container, "strong", "Matching available donors");
        if (!response.data.length) {
            addText(container, "p", "No donor matches this group and area right now.", "hint");
            return;
        }
        const select = document.createElement("select");
        select.className = "donor-match-select";
        addText(select, "option", "Select a donor").value = "";
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
        complete.textContent = "Fulfill request";
        complete.addEventListener("click", () => completeRequest(requestId, select.value));
        container.appendChild(complete);
    } catch (error) {
        bloodMessage(error.message, "error");
    }
}

async function completeRequest(requestId, donorId) {
    if (!donorId) {
        bloodMessage("Select a matching donor first.", "error");
        return;
    }
    try {
        await apiRequest(`/api/blood/requests/${requestId}/complete/`, "POST", { donor_id: donorId });
        bloodMessage("Request fulfilled and donation history recorded.", "success");
        await loadRequests();
        await loadHistory();
    } catch (error) {
        bloodMessage(error.message, "error");
    }
}

async function closeRequest(requestId) {
    try {
        await apiRequest(`/api/blood/requests/${requestId}/close/`, "POST");
        bloodMessage("Request closed.", "success");
        await loadRequests();
    } catch (error) {
        bloodMessage(error.message, "error");
    }
}

function renderRequests(requests) {
    const list = document.getElementById("requestList");
    list.replaceChildren();
    if (!requests.length) {
        addText(list, "p", "No open blood requests.", "hint");
        return;
    }
    requests.forEach((item) => {
        const card = document.createElement("article");
        card.className = "blood-request-item";
        addText(card, "h3", `${item.blood_group} · ${item.area}`);
        addText(card, "p", `${item.hospital} · Requested by ${item.requester_name}`);
        if (item.details) addText(card, "p", item.details, "hint");
        const actions = document.createElement("div");
        actions.className = "blood-request-actions";
        if (item.requester_id === bloodState.currentUserId) {
            const matches = document.createElement("div");
            matches.className = "match-panel";
            const matchButton = document.createElement("button");
            matchButton.type = "button";
            matchButton.className = "small-btn";
            matchButton.textContent = "Find matching donors";
            matchButton.addEventListener("click", () => showMatches(item.id, matches));
            actions.append(matchButton, matches);
            const close = document.createElement("button");
            close.type = "button";
            close.className = "small-btn danger-btn";
            close.textContent = "Close request";
            close.addEventListener("click", () => closeRequest(item.id));
            actions.appendChild(close);
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
            addText(list, "p", "No donations recorded yet.", "hint");
            return;
        }
        response.data.forEach((item) => {
            const row = document.createElement("article");
            row.className = "history-item";
            addText(row, "strong", `${item.blood_group} · ${item.area}`);
            addText(row, "p", `${item.hospital} · ${new Date(item.donated_at).toLocaleDateString()}`);
            list.appendChild(row);
        });
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
    populateBloodGroups();
    document.getElementById("donorProfileForm").addEventListener("submit", saveDonorProfile);
    document.getElementById("requestForm").addEventListener("submit", createBloodRequest);
    document.getElementById("refreshRequests").addEventListener("click", loadRequests);
    document.getElementById("refreshHistory").addEventListener("click", loadHistory);
    await Promise.all([loadDonorProfile(), loadRequests(), loadHistory()]);
});
