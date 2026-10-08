document.addEventListener("DOMContentLoaded", async () => {
    if (!requireLogin()) return;
    const message = document.getElementById("certificatePrintMessage");
    const certificateId = new URLSearchParams(location.search).get("certificate_id");
    if (!certificateId || !/^\d+$/.test(certificateId)) {
        message.textContent = "A valid certificate ID is required.";
        return;
    }
    try {
        const {data} = await apiRequest("/api/volunteer/certificates/");
        const certificate = data.find(item => String(item.id) === certificateId);
        if (!certificate) throw new Error("This certificate is not available to your account.");
        document.getElementById("certificateVolunteer").textContent = certificate.volunteer_name;
        document.getElementById("certificateEvent").textContent = certificate.event_name;
        document.getElementById("certificateDate").textContent = certificate.completion_date;
        document.getElementById("certificateCoordinator").textContent = certificate.coordinator_name;
        document.getElementById("printCertificate").addEventListener("click", () => window.print());
        document.title = `Certificate - ${certificate.volunteer_name}`;
    } catch (error) {
        document.getElementById("certificateSheet").hidden = true;
        message.textContent = error.message;
        message.className = "form-message error";
    }
});