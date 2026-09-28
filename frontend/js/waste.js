/* ============================================================
   HELPNET - Waste Pickup System (ST 41, ST 42)
   Frontend Logic for waste-pickup.html
   ============================================================ */

document.addEventListener("DOMContentLoaded", function () {
    if (typeof requireLogin === "function" && !requireLogin()) {
        return;
    }

    const user = typeof getStoredUser === "function" ? getStoredUser() : null;
    initWastePickupPage(user);
});

function initWastePickupPage(user) {
    const pickupForm = document.getElementById("wastePickupForm");
    const areaInput = document.getElementById("pickupArea");
    const collectorsContainer = document.getElementById("collectorsList");
    const requestsContainer = document.getElementById("requestsList");
    const requestsEmpty = document.getElementById("requestsEmpty");

    // Pre-fill user location if present
    if (user && user.location && areaInput && !areaInput.value) {
        areaInput.value = user.location;
    }

    // Load available collectors when area is typed/changed
    if (areaInput) {
        areaInput.addEventListener("input", debounce(function () {
            loadAvailableCollectors(areaInput.value.trim());
        }, 400));
    }

    // Initial load
    const initialArea = areaInput ? areaInput.value.trim() : "";
    loadAvailableCollectors(initialArea);
    loadMyRequests();

    // Form submission
    if (pickupForm) {
        pickupForm.addEventListener("submit", async function (e) {
            e.preventDefault();
            hideAlert("wasteAlert");
            clearFieldErrors("wastePickupForm");

            const wasteType = document.getElementById("wasteType").value;
            const area = document.getElementById("pickupArea").value.trim();
            const location = document.getElementById("pickupLocation").value.trim();
            const preferredDate = document.getElementById("preferredDate").value;
            const preferredTime = document.getElementById("preferredTime").value.trim();
            const notes = document.getElementById("notes") ? document.getElementById("notes").value.trim() : "";
            const submitBtn = document.getElementById("submitWasteBtn");

            let hasError = false;
            if (!wasteType) {
                showFieldError("wasteType", "Please select a waste type.");
                hasError = true;
            }
            if (!area) {
                showFieldError("pickupArea", "Please enter your area / district.");
                hasError = true;
            }
            if (!location) {
                showFieldError("pickupLocation", "Please enter detailed address.");
                hasError = true;
            }

            if (hasError) return;

            setBusy(submitBtn, true);

            try {
                const payload = {
                    waste_type: wasteType,
                    area: area,
                    location: location,
                    preferred_pickup_date: preferredDate || null,
                    preferred_pickup_time: preferredTime || "",
                    notes: notes,
                };

                const res = await apiRequest("/api/waste/requests/", "POST", payload);
                showAlert("wasteAlert", "Waste pickup request submitted successfully!", "success");
                pickupForm.reset();
                if (areaInput && area) {
                    areaInput.value = area;
                }
                loadAvailableCollectors(area);
                loadMyRequests();
            } catch (err) {
                showAlert("wasteAlert", err.message || "Failed to submit request.", "error");
            } finally {
                setBusy(submitBtn, false);
            }
        });
    }
}

async function loadAvailableCollectors(area) {
    const container = document.getElementById("collectorsList");
    const emptyNotice = document.getElementById("collectorsEmpty");
    if (!container) return;

    try {
        const query = area ? "?area=" + encodeURIComponent(area) : "";
        const res = await apiRequest("/api/waste/collectors/" + query, "GET");
        const collectors = (res && res.data) ? res.data : [];

        container.innerHTML = "";

        if (collectors.length === 0) {
            if (emptyNotice) emptyNotice.hidden = false;
            return;
        }

        if (emptyNotice) emptyNotice.hidden = true;

        collectors.forEach(function (collector) {
            const card = document.createElement("div");
            card.className = "collector-card";
            const ratingStars = "⭐ " + (collector.average_rating || 5.0) + " (" + (collector.rating_count || 0) + ")";

            card.innerHTML = `
                <div class="collector-info">
                    <div class="collector-avatar">♻️</div>
                    <div>
                        <h3 class="collector-name">${escapeHtml(collector.full_name || "Collector")}</h3>
                        <p class="collector-meta">📍 ${escapeHtml(collector.location || "Area Collector")} &bull; <span class="collector-role">${escapeHtml(collector.role || "Collector")}</span></p>
                        <p class="collector-rating">${ratingStars}</p>
                    </div>
                </div>
                <div class="collector-actions">
                    ${collector.phone_number ? `<a href="tel:${escapeHtml(collector.phone_number)}" class="btn-sm btn-call">📞 ${escapeHtml(collector.phone_number)}</a>` : ""}
                    <a href="/collector-details/?id=${collector.user_id}" class="btn-sm btn-outline">View & Rate</a>
                </div>
            `;
            container.appendChild(card);
        });
    } catch (err) {
        console.error("Error loading collectors:", err);
    }
}

async function loadMyRequests() {
    const container = document.getElementById("requestsList");
    const emptyNotice = document.getElementById("requestsEmpty");
    if (!container) return;

    try {
        const res = await apiRequest("/api/waste/requests/", "GET");
        const requests = Array.isArray(res) ? res : (res && res.results ? res.results : (res && res.data ? res.data : []));

        container.innerHTML = "";

        if (!requests || requests.length === 0) {
            if (emptyNotice) emptyNotice.hidden = false;
            return;
        }

        if (emptyNotice) emptyNotice.hidden = true;

        requests.forEach(function (req) {
            const card = document.createElement("div");
            card.className = "request-card";

            const statusClass = "status-" + (req.status || "requested").toLowerCase();
            const dateStr = req.preferred_pickup_date || (req.created_at ? req.created_at.split("T")[0] : "");
            const timeStr = req.preferred_pickup_time ? " (" + req.preferred_pickup_time + ")" : "";

            let actionButtons = "";
            if (req.status === "Requested") {
                actionButtons += `
                    <button class="btn-xs btn-outline" onclick="updateRequestStatus('${req.id}', 'Contacted')">Mark Contacted</button>
                    <button class="btn-xs btn-danger-outline" onclick="updateRequestStatus('${req.id}', 'Cancelled')">Cancel</button>
                `;
            } else if (req.status === "Contacted") {
                actionButtons += `
                    <button class="btn-xs btn-success-outline" onclick="updateRequestStatus('${req.id}', 'Completed')">Mark Completed</button>
                    <button class="btn-xs btn-danger-outline" onclick="updateRequestStatus('${req.id}', 'Cancelled')">Cancel</button>
                `;
            }

            // Collector info or rate link
            let collectorHtml = "";
            if (req.collector_details) {
                collectorHtml = `
                    <div class="request-collector-box">
                        <span>Assigned Collector: <strong>${escapeHtml(req.collector_details.full_name)}</strong> (${escapeHtml(req.collector_details.phone_number || "")})</span>
                        <a href="/collector-details/?id=${req.collector_details.user_id}" class="rate-link">Rate/Report Collector →</a>
                    </div>
                `;
            } else {
                collectorHtml = `
                    <div class="request-collector-box">
                        <span class="text-muted">Available area collectors listed below.</span>
                    </div>
                `;
            }

            card.innerHTML = `
                <div class="request-header">
                    <div>
                        <span class="request-type-badge">${escapeHtml(req.waste_type)}</span>
                        <h4 class="request-title">📍 ${escapeHtml(req.area)} — ${escapeHtml(req.location)}</h4>
                    </div>
                    <span class="status ${statusClass}">${escapeHtml(req.status)}</span>
                </div>
                <div class="request-body">
                    <p class="request-datetime">🗓️ Pickup Preferred: <strong>${escapeHtml(dateStr + timeStr)}</strong></p>
                    ${req.notes ? `<p class="request-notes">📝 ${escapeHtml(req.notes)}</p>` : ""}
                    ${collectorHtml}
                </div>
                <div class="request-actions">
                    ${actionButtons}
                </div>
            `;
            container.appendChild(card);
        });
    } catch (err) {
        console.error("Error loading waste requests:", err);
    }
}

async function updateRequestStatus(requestId, newStatus) {
    try {
        await apiRequest("/api/waste/requests/" + requestId + "/", "PATCH", { status: newStatus });
        loadMyRequests();
    } catch (err) {
        alert(err.message || "Failed to update status.");
    }
}

function debounce(func, wait) {
    let timeout;
    return function (...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

function escapeHtml(text) {
    if (!text) return "";
    return String(text)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
