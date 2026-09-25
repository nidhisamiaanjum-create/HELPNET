function volunteerNotice(message, type = "") {
    const box = document.getElementById("volunteerMessage");
    if (box) { box.textContent = message; box.className = `form-message ${type}`; }
}
function volunteerText(parent, tag, value) { const el = document.createElement(tag); el.textContent = value; parent.appendChild(el); return el; }
function volunteerEventId() { return document.getElementById("messageEventId")?.value || new URLSearchParams(location.search).get("event_id") || ""; }
function volunteerRole() { return (getStoredUser()?.role || "").toLowerCase(); }
function isVolunteerCoordinator() { return volunteerRole() === "ngo"; }

async function loadOpportunities() {
    const target = document.getElementById("opportunityList");
    if (!target) return;
    try {
        const response = await apiRequest(isVolunteerCoordinator() ? "/api/volunteer/my-events/?coordinated=true" : "/api/volunteer/opportunities/"); target.replaceChildren();
        const events = response.data || [];
        if (!events.length) {
            volunteerText(target, "p", isVolunteerCoordinator() ? "You have not created any opportunities yet." : "No open opportunities at the moment.");
            return;
        }
        events.forEach(event => {
            const card = document.createElement("article"); card.className = "admin-item";
            volunteerText(card, "h3", event.title); volunteerText(card, "p", `${event.date} · ${event.location} · ${event.signup_count}/${event.required_volunteers} volunteers`);
            volunteerText(card, "p", event.description); volunteerText(card, "p", `Coordinator: ${event.coordinator_name} · ${event.status}`);
            if (isVolunteerCoordinator()) {
                const actions = document.createElement("div"); actions.className = "admin-actions";
                const statusButton = document.createElement("button"); statusButton.type = "button"; statusButton.className = "small-btn"; statusButton.textContent = event.status === "Open" ? "Close opportunity" : "Reopen opportunity";
                statusButton.addEventListener("click", async () => { try { await apiRequest(`/api/volunteer/opportunities/${event.id}/`, "PATCH", {status: event.status === "Open" ? "Closed" : "Open"}); volunteerNotice("Opportunity status updated.", "success"); await loadOpportunities(); } catch (e) { volunteerNotice(e.message, "error"); } });
                const attendanceLink = document.createElement("a"); attendanceLink.className = "small-btn"; attendanceLink.href = `/volunteer-attendance/?event_id=${encodeURIComponent(event.id)}`; attendanceLink.textContent = "Manage attendance";
                actions.append(statusButton, attendanceLink); card.appendChild(actions);
            } else if (volunteerRole() === "volunteer" && event.status === "Open") {
                const signup = document.createElement("button"); signup.type = "button"; signup.className = "small-btn"; signup.textContent = "Sign up";
                signup.addEventListener("click", async () => { try { await apiRequest(`/api/volunteer/opportunities/${event.id}/signup/`, "POST", {}); volunteerNotice("You signed up successfully.", "success"); await loadOpportunities(); } catch (e) { volunteerNotice(e.message, "error"); } });
                card.appendChild(signup);
            }
            target.appendChild(card);
        });
    } catch (e) { volunteerNotice(e.message, "error"); }
}

async function loadAttendance() {
    const eventId = document.getElementById("attendanceEvent")?.value || new URLSearchParams(location.search).get("event_id") || "";
    const target = document.getElementById("attendanceList");
    if (!eventId || !target) return;
    try {
        const response = await apiRequest(`/api/volunteer/opportunities/${eventId}/attendance/`); target.replaceChildren();
        if (!response.data.length) { volunteerText(target, "p", "No volunteer signups yet."); return; }
        response.data.forEach(item => { const row = document.createElement("article"); row.className = "admin-item"; volunteerText(row, "h3", item.volunteer_name); volunteerText(row, "p", `Check in: ${item.check_in_time || "Not checked in"} · Check out: ${item.check_out_time || "Not checked out"}`);
            [["Check in", "check_in"], ["Check out", "check_out"]].forEach(([label, action]) => { const button = document.createElement("button"); button.type = "button"; button.className = "small-btn"; button.textContent = label; button.addEventListener("click", async () => { try { await apiRequest(`/api/volunteer/opportunities/${eventId}/attendance/`, "POST", {volunteer_id: item.volunteer, action}); await loadAttendance(); } catch (e) { volunteerNotice(e.message, "error"); } }); row.appendChild(button); }); target.appendChild(row); });
    } catch (e) { volunteerNotice(e.message, "error"); }
}

async function loadAttendanceEvents() {
    const select = document.getElementById("attendanceEvent");
    if (!select) return;
    if (!isVolunteerCoordinator()) {
        select.disabled = true;
        const option = document.createElement("option"); option.value = ""; option.textContent = "Coordinator access required";
        select.replaceChildren(option);
        volunteerNotice("Attendance check-in and check-out are available to event coordinators.", "error");
        return;
    }
    try {
        const response = await apiRequest("/api/volunteer/my-events/?coordinated=true");
        select.replaceChildren();
        if (!response.data.length) {
            const option = document.createElement("option"); option.value = ""; option.textContent = "No events created by your account"; select.appendChild(option);
            volunteerText(document.getElementById("attendanceList"), "p", "Create an opportunity before managing attendance.");
            return;
        }
        response.data.forEach(event => { const option = document.createElement("option"); option.value = event.id; option.textContent = `${event.title} · ${event.date}`; select.appendChild(option); });
        const requested = new URLSearchParams(location.search).get("event_id");
        if (requested && response.data.some(event => String(event.id) === requested)) select.value = requested;
        await loadAttendance();
    } catch (e) { volunteerNotice(e.message, "error"); }
}

async function loadMessages() {
    const id = volunteerEventId(), target = document.getElementById("messageList");
    if (!id || !target) { volunteerNotice("Enter an event ID to load messages.", "error"); return; }
    try { const response = await apiRequest(`/api/volunteer/opportunities/${id}/messages/`); target.replaceChildren(); response.data.forEach(item => { const row = document.createElement("p"); row.textContent = `${item.sender_name} · ${new Date(item.timestamp).toLocaleString()}: ${item.message}`; target.appendChild(row); }); }
    catch (e) { volunteerNotice(e.message, "error"); }
}

async function loadCertificateVolunteers() {
    const eventId = document.getElementById("certificateEvent").value;
    const select = document.getElementById("certificateVolunteer");
    if (!eventId) return volunteerNotice("Enter an event ID first.", "error");
    try {
        const response = await apiRequest(`/api/volunteer/opportunities/${eventId}/signup/`);
        select.replaceChildren();
        const prompt = document.createElement("option"); prompt.value = ""; prompt.textContent = response.data.length ? "Select a volunteer" : "No signups for this event"; select.appendChild(prompt);
        response.data.forEach(signup => { const option = document.createElement("option"); option.value = signup.volunteer; option.textContent = signup.volunteer_name; select.appendChild(option); });
        volunteerNotice(response.data.length ? `${response.data.length} signed-up volunteer(s) loaded.` : "No volunteers have signed up for this event.", response.data.length ? "success" : "");
    } catch (error) { select.replaceChildren(); const option = document.createElement("option"); option.value = ""; option.textContent = "Could not load event volunteers"; select.appendChild(option); volunteerNotice(error.message, "error"); }
}

async function loadMessageEvents() {
    const select = document.getElementById("messageEventId");
    try {
        const response = await apiRequest("/api/volunteer/my-events/");
        select.replaceChildren();
        if (!response.data.length) {
            const option = document.createElement("option"); option.value = ""; option.textContent = "No coordinated or joined events"; select.appendChild(option);
            volunteerNotice("You need to coordinate an event or sign up for one before messaging.", "");
            return;
        }
        response.data.forEach(event => {
            const option = document.createElement("option"); option.value = event.id;
            option.textContent = `${event.title} · ${event.date} · ${event.location}`; select.appendChild(option);
        });
        const requested = new URLSearchParams(location.search).get("event_id");
        if (requested && response.data.some(event => String(event.id) === requested)) select.value = requested;
        await loadMessages();
    } catch (error) { volunteerNotice(error.message, "error"); }
}

async function loadCoordinatedEvents() {
    const select = document.getElementById("certificateEvent");
    try {
        const response = await apiRequest("/api/volunteer/my-events/?coordinated=true");
        select.replaceChildren();
        if (!response.data.length) {
            const option = document.createElement("option"); option.value = ""; option.textContent = "No events created by your account"; select.appendChild(option);
            volunteerNotice("There are no events to issue certificates for.", "");
            return;
        }
        response.data.forEach(event => { const option = document.createElement("option"); option.value = event.id; option.textContent = `${event.title} · ${event.date}`; select.appendChild(option); });
        const requested = new URLSearchParams(location.search).get("event_id");
        if (requested && response.data.some(event => String(event.id) === requested)) select.value = requested;
        await loadCertificateVolunteers();
    } catch (error) { volunteerNotice(error.message, "error"); }
}

document.addEventListener("DOMContentLoaded", () => {
    if (!requireLogin()) return;
    if (document.getElementById("opportunityList")) {
        if (isVolunteerCoordinator()) {
            const createLink = document.createElement("a"); createLink.href = "/create-opportunity/"; createLink.className = "btn"; createLink.textContent = "Create opportunity";
            document.getElementById("opportunityList").before(createLink);
        }
        loadOpportunities();
    }
    const createForm = document.getElementById("opportunityForm");
    createForm?.addEventListener("submit", async e => { e.preventDefault(); try { await apiRequest("/api/volunteer/opportunities/", "POST", {title: document.getElementById("eventTitle").value.trim(), description: document.getElementById("eventDescription").value.trim(), date: document.getElementById("eventDate").value, location: document.getElementById("eventLocation").value.trim(), required_volunteers: Number(document.getElementById("eventRequired").value)}); createForm.reset(); volunteerNotice("Opportunity created.", "success"); } catch (error) { volunteerNotice(error.message, "error"); } });
    if (document.getElementById("attendanceList")) {
        document.getElementById("attendanceEvent")?.addEventListener("change", loadAttendance);
        loadAttendanceEvents();
    }
    if (document.getElementById("messageList")) {
        document.getElementById("messageEventId")?.addEventListener("change", loadMessages);
        loadMessageEvents();
    }
    document.getElementById("eventMessageForm")?.addEventListener("submit", async e => { e.preventDefault(); const id = volunteerEventId(); if (!id) return volunteerNotice("Enter an event ID and load its messages first.", "error"); try { await apiRequest(`/api/volunteer/opportunities/${id}/messages/`, "POST", {message: document.getElementById("eventMessage").value.trim()}); e.target.reset(); await loadMessages(); volunteerNotice("Message sent.", "success"); } catch (error) { volunteerNotice(error.message, "error"); } });
    document.getElementById("certificateEvent")?.addEventListener("change", loadCertificateVolunteers);
    document.getElementById("issueCertificateForm")?.addEventListener("submit", async e => { e.preventDefault(); const id = document.getElementById("certificateEvent").value; const volunteerId = document.getElementById("certificateVolunteer").value; if (!id || !volunteerId) return volunteerNotice("Load an event's signed-up volunteers and select one.", "error"); try { await apiRequest(`/api/volunteer/opportunities/${id}/certificates/`, "POST", {volunteer_id: volunteerId}); volunteerNotice("Certificate issued.", "success"); await loadCertificates(); } catch (error) { volunteerNotice(error.message, "error"); } });
    if (document.getElementById("certificateList")) { loadCertificates(); loadCoordinatedEvents(); }
});

async function loadCertificates() {
    const target = document.getElementById("certificateList"); if (!target) return;
    try {
        const response = await apiRequest("/api/volunteer/certificates/"); target.replaceChildren();
        if (!response.data.length) { volunteerText(target, "p", "No certificates issued yet."); return; }
        response.data.forEach(cert => {
            const row = document.createElement("article"); row.className = "admin-item";
            volunteerText(row, "h3", cert.event_name);
            volunteerText(row, "p", `Volunteer: ${cert.volunteer_name} · Completed ${cert.completion_date} · Coordinator: ${cert.coordinator_name}`);
            const button = document.createElement("button"); button.className = "small-btn"; button.type = "button"; button.textContent = "Download PDF";
            button.addEventListener("click", async () => {
                try {
                    const pdfResponse = await fetch(`${API_BASE}/api/volunteer/certificates/${cert.id}/pdf/`, {headers: {Authorization: `Bearer ${getToken()}`}});
                    if (!pdfResponse.ok) throw new Error("Could not download certificate.");
                    const url = URL.createObjectURL(await pdfResponse.blob()); const link = document.createElement("a");
                    link.href = url; link.download = `volunteer-certificate-${cert.id}.pdf`; document.body.appendChild(link); link.click(); link.remove();
                    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
                } catch (e) { volunteerNotice(e.message, "error"); }
            });
            row.appendChild(button); target.appendChild(row);
        });
    } catch (e) { volunteerNotice(e.message, "error"); }
}
