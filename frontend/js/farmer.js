/* ============================================================
   HELPNET - Farmer Marketplace (ST 43, ST 44, ST 45, ST 47)
   Frontend Logic for farmer marketplace pages
   ============================================================ */

document.addEventListener("DOMContentLoaded", function () {
    if (typeof requireLogin === "function" && !requireLogin()) {
        return;
    }

    const user = typeof getStoredUser === "function" ? getStoredUser() : null;

    // Detect page type
    if (document.getElementById("produceGrid")) {
        initMarketPage(user);
    } else if (document.getElementById("createProduceForm")) {
        initCreateProducePage(user);
    } else if (document.getElementById("produceDetailPage")) {
        initProduceDetailPage(user);
    }
});

/* ============================================================
   1. MARKETPLACE OVERVIEW PAGE (farmer-market.html)
   ============================================================ */
function initMarketPage(user) {
    const isFarmer = user && (user.role === "Farmer" || user.role === "Volunteer" || user.role === "Admin" || user.role === "Citizen");
    const farmerActionSection = document.getElementById("farmerActionSection");
    const myProduceSection = document.getElementById("myProduceSection");

    // Show farmer-specific creation buttons
    if (user && user.role === "Farmer") {
        if (farmerActionSection) farmerActionSection.hidden = false;
        if (myProduceSection) {
            myProduceSection.hidden = false;
            loadMyProduceListings();
        }
    } else if (farmerActionSection) {
        // Even if role is not strictly Farmer, let user easily access post produce if needed
        farmerActionSection.hidden = false;
    }

    const searchInput = document.getElementById("marketSearchInput");
    const categorySelect = document.getElementById("marketCategorySelect");
    const availabilitySelect = document.getElementById("marketAvailabilitySelect");

    function fetchFiltered() {
        const q = searchInput ? searchInput.value.trim() : "";
        const cat = categorySelect ? categorySelect.value : "";
        const avail = availabilitySelect ? availabilitySelect.value : "";
        loadMarketListings({ search: q, category: cat, availability: avail });
    }

    if (searchInput) {
        searchInput.addEventListener("input", debounce(fetchFiltered, 350));
    }
    if (categorySelect) {
        categorySelect.addEventListener("change", fetchFiltered);
    }
    if (availabilitySelect) {
        availabilitySelect.addEventListener("change", fetchFiltered);
    }

    loadMarketListings();
}

async function loadMarketListings(params = {}) {
    const container = document.getElementById("produceGrid");
    const emptyNotice = document.getElementById("produceEmpty");
    if (!container) return;

    let queryString = "";
    const searchParams = new URLSearchParams();
    if (params.search) searchParams.append("search", params.search);
    if (params.category) searchParams.append("category", params.category);
    if (params.availability) searchParams.append("availability", params.availability);

    if (searchParams.toString()) {
        queryString = "?" + searchParams.toString();
    }

    try {
        const res = await apiRequest("/api/farmer/produce/" + queryString, "GET");
        const list = Array.isArray(res) ? res : (res && res.results ? res.results : (res && res.data ? res.data : []));

        container.innerHTML = "";

        if (!list || list.length === 0) {
            if (emptyNotice) emptyNotice.hidden = false;
            return;
        }

        if (emptyNotice) emptyNotice.hidden = true;

        list.forEach(p => {
            const card = document.createElement("div");
            card.className = "produce-card";

            const isAvail = p.availability === "Available";
            const availClass = isAvail ? "status-approved" : "status-rejected";

            card.innerHTML = `
                <div class="produce-card-top">
                    <div class="produce-icon-badge">🌾</div>
                    <span class="status ${availClass}">${escapeHtml(p.availability)}</span>
                </div>
                <h3 class="produce-card-title">${escapeHtml(p.produce_name)}</h3>
                <p class="produce-card-price">৳${escapeHtml(p.price)} <span class="produce-unit">/ ${escapeHtml(p.unit || "kg")}</span></p>
                <div class="produce-meta">
                    <p>📦 Quantity: <strong>${escapeHtml(p.quantity)}</strong></p>
                    <p>📍 Location: <strong>${escapeHtml(p.location)}</strong></p>
                    <p>👨‍🌾 Farmer: <strong>${escapeHtml(p.farmer_name || "Local Farmer")}</strong></p>
                </div>
                ${p.description ? `<p class="produce-card-desc">${escapeHtml(p.description)}</p>` : ""}
                <div class="produce-card-footer">
                    <a href="/produce-details/?id=${p.id}" class="btn btn-sm">View Details & Contact</a>
                </div>
            `;
            container.appendChild(card);
        });
    } catch (err) {
        console.error("Error loading marketplace:", err);
    }
}

async function loadMyProduceListings() {
    const container = document.getElementById("myProduceList");
    const emptyNotice = document.getElementById("myProduceEmpty");
    if (!container) return;

    try {
        const res = await apiRequest("/api/farmer/my-produce/", "GET");
        const list = res && res.data ? res.data : [];

        container.innerHTML = "";

        if (!list || list.length === 0) {
            if (emptyNotice) emptyNotice.hidden = false;
            return;
        }

        if (emptyNotice) emptyNotice.hidden = true;

        list.forEach(p => {
            const card = document.createElement("div");
            card.className = "admin-item";
            const isAvail = p.availability === "Available";

            card.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 10px;">
                    <div>
                        <h3>${escapeHtml(p.produce_name)} (৳${escapeHtml(p.price)} / ${escapeHtml(p.unit)})</h3>
                        <p>📍 ${escapeHtml(p.location)} &bull; Quantity: ${escapeHtml(p.quantity)}</p>
                    </div>
                    <span class="status ${isAvail ? "status-approved" : "status-rejected"}">${escapeHtml(p.availability)}</span>
                </div>
                <div class="admin-actions" style="margin-top: 10px;">
                    <button class="btn-xs btn-outline" onclick="toggleProduceAvailability('${p.id}', '${isAvail ? "Unavailable" : "Available"}')">
                        Set ${isAvail ? "Unavailable" : "Available"}
                    </button>
                    <a href="/produce-details/?id=${p.id}" class="btn-xs btn-outline" style="text-decoration:none; padding:8px 12px; display:inline-block;">Edit / View</a>
                    <button class="btn-xs btn-danger" onclick="deleteProduceListing('${p.id}')">Delete</button>
                </div>
            `;
            container.appendChild(card);
        });
    } catch (err) {
        console.error("Error loading my produce:", err);
    }
}

async function toggleProduceAvailability(id, newStatus) {
    try {
        await apiRequest(`/api/farmer/produce/${id}/`, "PATCH", { availability: newStatus });
        loadMyProduceListings();
        loadMarketListings();
    } catch (err) {
        alert(err.message || "Failed to update status.");
    }
}

async function deleteProduceListing(id) {
    if (!confirm("Are you sure you want to delete this produce listing?")) {
        return;
    }
    try {
        await apiRequest(`/api/farmer/produce/${id}/`, "DELETE");
        loadMyProduceListings();
        loadMarketListings();
    } catch (err) {
        alert(err.message || "Failed to delete produce.");
    }
}

/* ============================================================
   2. CREATE PRODUCE PAGE (create-produce.html)
   ============================================================ */
function initCreateProducePage(user) {
    const form = document.getElementById("createProduceForm");
    const locationInput = document.getElementById("farmLocation");

    // Pre-fill location if user has one
    if (user && user.location && locationInput && !locationInput.value) {
        locationInput.value = user.location;
    }

    if (!form) return;

    form.addEventListener("submit", async function (e) {
        e.preventDefault();
        hideAlert("produceAlert");
        clearFieldErrors("createProduceForm");

        const produceName = document.getElementById("produceName").value.trim();
        const category = document.getElementById("produceCategory").value;
        const price = document.getElementById("producePrice").value.trim();
        const unit = document.getElementById("produceUnit").value.trim();
        const quantity = document.getElementById("produceQuantity").value.trim();
        const location = document.getElementById("farmLocation").value.trim();
        const description = document.getElementById("produceDescription").value.trim();
        const availability = document.getElementById("produceAvailability").value;
        const submitBtn = document.getElementById("submitProduceBtn");

        let hasError = false;
        if (!produceName) {
            showFieldError("produceName", "Please enter the produce name.");
            hasError = true;
        }
        if (!price || isNaN(price) || parseFloat(price) <= 0) {
            showFieldError("producePrice", "Please enter a valid price (e.g. 50).");
            hasError = true;
        }
        if (!quantity) {
            showFieldError("produceQuantity", "Please enter available quantity (e.g. 100 kg).");
            hasError = true;
        }
        if (!location) {
            showFieldError("farmLocation", "Please enter farm / pickup location.");
            hasError = true;
        }

        if (hasError) return;

        setBusy(submitBtn, true);

        try {
            const payload = {
                produce_name: produceName,
                category: category || "Vegetables",
                price: parseFloat(price),
                unit: unit || "kg",
                quantity: quantity,
                location: location,
                description: description,
                availability: availability || "Available",
            };

            await apiRequest("/api/farmer/produce/", "POST", payload);
            showAlert("produceAlert", "Produce listing published successfully!", "success");
            setTimeout(() => {
                window.location.href = "/farmer-market/";
            }, 1000);
        } catch (err) {
            showAlert("produceAlert", err.message || "Failed to create listing.", "error");
        } finally {
            setBusy(submitBtn, false);
        }
    });
}

/* ============================================================
   3. PRODUCE DETAILS & CONTACT (produce-details.html)
   ============================================================ */
async function initProduceDetailPage(user) {
    const params = new URLSearchParams(window.location.search);
    const produceId = params.get("id");

    if (!produceId) {
        showAlert("detailAlert", "No produce ID specified.", "error");
        return;
    }

    try {
        const res = await apiRequest(`/api/farmer/produce/${produceId}/`, "GET");
        if (res) {
            const p = res;
            document.getElementById("detailTitle").textContent = p.produce_name;
            document.getElementById("detailPrice").textContent = `৳${p.price} / ${p.unit || "kg"}`;
            document.getElementById("detailQuantity").textContent = p.quantity;
            document.getElementById("detailLocation").textContent = p.location;
            document.getElementById("detailCategory").textContent = p.category || "General";
            document.getElementById("detailDesc").textContent = p.description || "No specific details provided.";

            const availBadge = document.getElementById("detailAvailability");
            if (availBadge) {
                availBadge.textContent = p.availability;
                availBadge.className = "status " + (p.availability === "Available" ? "status-approved" : "status-rejected");
            }

            // Farmer contact
            const farmerNameEl = document.getElementById("farmerName");
            const farmerPhoneEl = document.getElementById("farmerPhone");
            const farmerLocEl = document.getElementById("farmerLocation");
            const callBtn = document.getElementById("farmerCallBtn");

            if (farmerNameEl) farmerNameEl.textContent = p.farmer_name || "Verified Farmer";
            if (farmerLocEl) farmerLocEl.textContent = "📍 " + (p.farmer_location || p.location);

            const phone = p.farmer_phone || (p.farmer_details && p.farmer_details.phone_number);
            if (phone) {
                if (farmerPhoneEl) farmerPhoneEl.textContent = phone;
                if (callBtn) {
                    callBtn.href = "tel:" + phone;
                    callBtn.hidden = false;
                }
            } else {
                if (farmerPhoneEl) farmerPhoneEl.textContent = "Contact through HELPNET profile";
                if (callBtn) callBtn.hidden = true;
            }

            // Owner management panel
            if (p.is_owner || (user && user.user_id === p.farmer)) {
                const ownerPanel = document.getElementById("ownerPanel");
                if (ownerPanel) {
                    ownerPanel.hidden = false;
                    setupOwnerControls(p);
                }
            }
        }
    } catch (err) {
        showAlert("detailAlert", err.message || "Failed to load produce details.", "error");
    }
}

function setupOwnerControls(produce) {
    const toggleBtn = document.getElementById("toggleAvailBtn");
    const editForm = document.getElementById("editProduceForm");
    const deleteBtn = document.getElementById("deleteProduceBtn");

    if (toggleBtn) {
        const nextStatus = produce.availability === "Available" ? "Unavailable" : "Available";
        toggleBtn.textContent = `Set as ${nextStatus}`;
        toggleBtn.onclick = async function () {
            try {
                await apiRequest(`/api/farmer/produce/${produce.id}/`, "PATCH", { availability: nextStatus });
                window.location.reload();
            } catch (e) {
                alert(e.message);
            }
        };
    }

    if (deleteBtn) {
        deleteBtn.onclick = async function () {
            if (confirm("Are you sure you want to permanently delete this listing?")) {
                try {
                    await apiRequest(`/api/farmer/produce/${produce.id}/`, "DELETE");
                    window.location.href = "/farmer-market/";
                } catch (e) {
                    alert(e.message);
                }
            }
        };
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
