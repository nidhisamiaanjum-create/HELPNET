document.addEventListener("DOMContentLoaded", async () => {
    if (!requireLogin()) return;
    const form = document.getElementById("volunteerProfileForm");
    const notice = document.getElementById("profileMessage");
    const show = (text, type = "") => { notice.textContent = text; notice.className = `form-message ${type}`; };
    try {
        const {data} = await apiRequest("/api/volunteer/profile/");
        document.getElementById("skills").value = data.skills;
        document.getElementById("availability").value = data.availability;
        document.getElementById("volunteerLocation").value = data.location;
        document.getElementById("volunteerBloodGroup").value = data.blood_group;
        document.getElementById("certificates").value = data.supporting_certificates;
    } catch (error) { show(error.message, "error"); }

    form.addEventListener("submit", async event => {
        event.preventDefault();
        try {
            await apiRequest("/api/volunteer/profile/", "PUT", {
                skills: document.getElementById("skills").value.trim(),
                availability: document.getElementById("availability").value.trim(),
                location: document.getElementById("volunteerLocation").value.trim(),
                blood_group: document.getElementById("volunteerBloodGroup").value,
                supporting_certificates: document.getElementById("certificates").value.trim()
            });
            show("Volunteer profile saved.", "success");
        } catch (error) { show(error.message, "error"); }
    });

    const list = document.getElementById("uploadedCertificates");
    async function loadDocuments() {
        if (!list) return;
        try {
            const {data} = await apiRequest("/api/volunteer/profile/documents/");
            list.replaceChildren();
            data.forEach(documentItem => {
                const row = document.createElement("p");
                row.textContent = `${documentItem.original_name} · ${new Date(documentItem.uploaded_at).toLocaleDateString()}`;
                list.appendChild(row);
            });
        } catch (error) { show(error.message, "error"); }
    }
    await loadDocuments();
    document.getElementById("certificateUploadForm")?.addEventListener("submit", async event => {
        event.preventDefault();
        const file = document.getElementById("certificateFile").files[0];
        if (!file) return;
        const payload = new FormData();
        payload.append("file", file);
        try {
            const response = await fetch(`${API_BASE}/api/volunteer/profile/documents/`, {
                method: "POST",
                headers: {Authorization: `Bearer ${getToken()}`},
                body: payload
            });
            const data = await response.json();
            if (!response.ok) throw new Error(formatApiError(data));
            event.target.reset();
            show("Certificate uploaded.", "success");
            await loadDocuments();
        } catch (error) { show(error.message, "error"); }
    });
});
