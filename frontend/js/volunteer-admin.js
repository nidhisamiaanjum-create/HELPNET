function renderVolunteerRows(container, volunteers) {
    container.replaceChildren();
    if (!volunteers.length) { const p = document.createElement("p"); p.textContent = "No volunteer records found."; container.appendChild(p); return; }
    volunteers.forEach(v => { const card = document.createElement("article"); card.className = "admin-item"; [["h3", v.full_name], ["p", `Skills: ${v.skills || "—"}`], ["p", `Availability: ${v.availability || "—"}`], ["p", `Location: ${v.location || "—"}`], ["p", `Blood group: ${v.blood_group || "—"}`], ["p", `Certificates: ${v.supporting_certificates || "—"}`], ["p", `${v.email || ""} ${v.phone_number || ""}`]].forEach(([tag, text]) => { const el = document.createElement(tag); el.textContent = text; card.appendChild(el); }); container.appendChild(card); });
}
async function runVolunteerFilters(form, endpoint, output, fields) {
    const params = new URLSearchParams(); fields.forEach(([key, id]) => { const value = document.getElementById(id).value.trim(); if (value) params.set(key, value); });
    try { const response = await apiRequest(`${endpoint}?${params}`); renderVolunteerRows(output, response.data); } catch (e) { output.textContent = e.message; }
}
document.addEventListener("DOMContentLoaded", () => {
    if (!requireLogin()) return;
    const search = document.getElementById("volunteerSearchForm");
    if (search) { const output = document.getElementById("volunteerSearchResults"); const fields = [["skills", "searchSkills"], ["availability", "searchAvailability"], ["location", "searchLocation"]]; search.addEventListener("submit", e => { e.preventDefault(); runVolunteerFilters(search, "/api/volunteer/search/", output, fields); }); runVolunteerFilters(search, "/api/volunteer/search/", output, fields); }
    const admin = document.getElementById("adminVolunteerFilter");
    if (admin) { const output = document.getElementById("adminVolunteerResults"); const fields = [["skills", "adminSkills"], ["availability", "adminAvailability"], ["location", "adminLocation"], ["blood_group", "adminBloodGroup"]]; admin.addEventListener("submit", e => { e.preventDefault(); runVolunteerFilters(admin, "/api/volunteer/admin/", output, fields); }); runVolunteerFilters(admin, "/api/volunteer/admin/", output, fields); }
});
