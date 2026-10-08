function renderVolunteerRows(container, volunteers) {
    container.replaceChildren();
    if (!volunteers.length) {
        const empty = document.createElement("p");
        empty.textContent = "No volunteer records found.";
        container.appendChild(empty);
        return;
    }
    volunteers.forEach(volunteer => {
        const card = document.createElement("article");
        card.className = "admin-item";
        const details = [
            ["h3", volunteer.full_name],
            ["p", `Skills: ${volunteer.skills || "—"}`],
            ["p", `Availability: ${volunteer.availability || "—"}`],
            ["p", `Location: ${volunteer.location || "—"}`],
            ["p", `Blood group: ${volunteer.blood_group || "—"}`],
            ["p", `Certificates: ${volunteer.supporting_certificates || "—"} ${volunteer.email || ""} ${volunteer.phone_number || ""}`]
        ];
        details.forEach(([tag, value]) => {
            const element = document.createElement(tag);
            element.textContent = value;
            card.appendChild(element);
        });
        container.appendChild(card);
    });
}

async function runVolunteerFilters(form, endpoint, output, fields) {
    const params = new URLSearchParams();
    fields.forEach(([key, id]) => {
        const field = document.getElementById(id);
        const value = field?.value.trim();
        if (value) params.set(key, value);
    });
    try {
        const response = await apiRequest(`${endpoint}?${params}`);
        renderVolunteerRows(output, response.data);
    } catch (error) {
        output.textContent = error.message;
    }
}

async function downloadVolunteerCsv(form) {
    const message = document.getElementById("adminVolunteerMessage");
    const params = new URLSearchParams();
    [["skills", "adminSkills"], ["availability", "adminAvailability"], ["location", "adminLocation"]].forEach(([key, id]) => {
        const value = document.getElementById(id).value.trim();
        if (value) params.set(key, value);
    });
    try {
        const response = await fetch(`${API_BASE}/api/volunteer/admin/export/?${params}`, {
            headers: {Authorization: `Bearer ${getToken()}`}
        });
        if (!response.ok) throw new Error("Could not export volunteers. Administrator access is required.");
        const url = URL.createObjectURL(await response.blob());
        const link = document.createElement("a");
        link.href = url;
        link.download = "helpnet-volunteers.csv";
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.setTimeout(() => URL.revokeObjectURL(url), 1000);
        if (message) message.textContent = "Volunteer CSV downloaded.";
    } catch (error) {
        if (message) message.textContent = error.message;
    }
}

document.addEventListener("DOMContentLoaded", () => {
    if (!requireLogin()) return;
    const search = document.getElementById("volunteerSearchForm");
    if (search) {
        const output = document.getElementById("volunteerSearchResults");
        const fields = [["skills", "searchSkills"], ["availability", "searchAvailability"], ["location", "searchLocation"], ["participation_history", "searchParticipation"]];
        search.addEventListener("submit", event => { event.preventDefault(); runVolunteerFilters(search, "/api/volunteer/search/", output, fields); });
        runVolunteerFilters(search, "/api/volunteer/search/", output, fields);
    }
    const admin = document.getElementById("adminVolunteerFilter");
    if (admin) {
        const output = document.getElementById("adminVolunteerResults");
        const fields = [["skills", "adminSkills"], ["availability", "adminAvailability"], ["location", "adminLocation"], ["blood_group", "adminBloodGroup"]];
        admin.addEventListener("submit", event => { event.preventDefault(); runVolunteerFilters(admin, "/api/volunteer/admin/", output, fields); });
        runVolunteerFilters(admin, "/api/volunteer/admin/", output, fields);
        document.getElementById("exportVolunteers")?.addEventListener("click", () => downloadVolunteerCsv(admin));
    }
});
