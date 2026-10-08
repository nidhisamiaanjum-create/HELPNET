document.addEventListener("DOMContentLoaded", async () => {
    if (!requireLogin()) return;
    const message = document.getElementById("certificatePrintMessage");
    const certificateId = new URLSearchParams(location.search).get("certificate_id");
    if (!certificateId || !/^\d+$/.test(certificateId)) {
        message.textContent = t("certificateInvalidId");
        return;
    }
    try {
        const {data} = await apiRequest("/api/volunteer/certificates/");
        const certificate = data.find(item => String(item.id) === certificateId);
        if (!certificate) {
            throw new Error(t("certificateUnavailable"));
        }
        document.getElementById("certificateVolunteer").textContent = certificate.volunteer_name;
        document.getElementById("certificateEvent").textContent = certificate.event_name;
        document.getElementById("certificateDate").textContent = certificate.completion_date;
        document.getElementById("certificateCoordinator").textContent = certificate.coordinator_name;
        document.getElementById("printCertificate").addEventListener("click", () => window.print());
        document.title = `Certificate - ${certificate.volunteer_name}`;
    } catch (error) {
        document.getElementById("certificateSheet").hidden = true;
        message.textContent = error.message || t("certificateUnavailable");
        message.className = "form-message error";
    }
});