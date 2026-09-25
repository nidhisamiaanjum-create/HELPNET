document.addEventListener("DOMContentLoaded", async () => {
    if (!requireLogin()) return;
    const form = document.getElementById("volunteerProfileForm"), notice = document.getElementById("profileMessage");
    const show = (text, type = "") => { notice.textContent = text; notice.className = `form-message ${type}`; };
    try { const {data} = await apiRequest("/api/volunteer/profile/"); document.getElementById("skills").value = data.skills; document.getElementById("availability").value = data.availability; document.getElementById("volunteerLocation").value = data.location; document.getElementById("volunteerBloodGroup").value = data.blood_group; document.getElementById("certificates").value = data.supporting_certificates; }
    catch (e) { show(e.message, "error"); }
    form.addEventListener("submit", async e => { e.preventDefault(); try { await apiRequest("/api/volunteer/profile/", "PUT", {skills: document.getElementById("skills").value.trim(), availability: document.getElementById("availability").value.trim(), location: document.getElementById("volunteerLocation").value.trim(), blood_group: document.getElementById("volunteerBloodGroup").value, supporting_certificates: document.getElementById("certificates").value.trim()}); show("Volunteer profile saved.", "success"); } catch (error) { show(error.message, "error"); } });
});
