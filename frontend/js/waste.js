/* ============================================================
   HELPNET - Waste Pickup System (ST 41, ST 42)
   Waste pickup requests + shared waste collector contacts
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
    const collectorForm = document.getElementById("collectorShareForm");

    const areaInput = document.getElementById("pickupArea");
    const collectorsContainer = document.getElementById("collectorsList");
    const requestsContainer = document.getElementById("requestsList");

    // Pre-fill user's location
    if (user && user.location && areaInput && !areaInput.value) {
        areaInput.value = user.location;
    }

    // Search collectors when area changes
    if (areaInput) {
        areaInput.addEventListener(
            "input",
            debounce(function () {
                loadAvailableCollectors(areaInput.value.trim());
            }, 400)
        );
    }

    // Initial load
    const initialArea = areaInput
        ? areaInput.value.trim()
        : "";

    loadAvailableCollectors(initialArea);
    loadMyRequests();

    // ---------------------------------------------------------
    // Waste pickup request
    // ---------------------------------------------------------

    if (pickupForm) {
        pickupForm.addEventListener("submit", async function (e) {
            e.preventDefault();

            hideAlert("wasteAlert");
            clearFieldErrors("wastePickupForm");

            const wasteType =
                document.getElementById("wasteType").value;

            const area =
                document.getElementById("pickupArea").value.trim();

            const location =
                document.getElementById("pickupLocation").value.trim();

            const preferredDate =
                document.getElementById("preferredDate").value;

            const preferredTime =
                document.getElementById("preferredTime").value.trim();

            const notesElement =
                document.getElementById("notes");

            const notes = notesElement
                ? notesElement.value.trim()
                : "";

            const submitBtn =
                document.getElementById("submitWasteBtn");

            let hasError = false;

            if (!wasteType) {
                showFieldError(
                    "wasteType",
                    "Please select a waste type."
                );
                hasError = true;
            }

            if (!area) {
                showFieldError(
                    "pickupArea",
                    "Please enter your area / district."
                );
                hasError = true;
            }

            if (!location) {
                showFieldError(
                    "pickupLocation",
                    "Please enter detailed address."
                );
                hasError = true;
            }

            if (hasError) {
                return;
            }

            setBusy(submitBtn, true);

            try {
                const payload = {
                    waste_type: wasteType,
                    area: area,
                    location: location,
                    preferred_pickup_date:
                        preferredDate || null,
                    preferred_pickup_time:
                        preferredTime || "",
                    notes: notes,
                };

                await apiRequest(
                    "/api/waste/requests/",
                    "POST",
                    payload
                );

                showAlert(
                    "wasteAlert",
                    "Waste pickup request submitted successfully!",
                    "success"
                );

                pickupForm.reset();

                // Keep the user's area after reset
                if (areaInput) {
                    areaInput.value = area;
                }

                loadAvailableCollectors(area);
                loadMyRequests();

            } catch (err) {
                showAlert(
                    "wasteAlert",
                    err.message ||
                    "Failed to submit request.",
                    "error"
                );
            } finally {
                setBusy(submitBtn, false);
            }
        });
    }

    // ---------------------------------------------------------
    // Share waste collector information
    // ---------------------------------------------------------

    if (collectorForm) {
        collectorForm.addEventListener(
            "submit",
            async function (e) {
                e.preventDefault();

                const name =
                    document.getElementById(
                        "collectorName"
                    ).value.trim();

                const phone =
                    document.getElementById(
                        "collectorPhone"
                    ).value.trim();

                const area =
                    document.getElementById(
                        "collectorArea"
                    ).value.trim();

                const wasteTypes =
                    document.getElementById(
                        "collectorWasteTypes"
                    ).value.trim();

                const notes =
                    document.getElementById(
                        "collectorNotes"
                    ).value.trim();

                const submitBtn =
                    document.getElementById(
                        "shareCollectorBtn"
                    );

                if (!name || !phone || !area) {
                    showAlert(
                        "wasteAlert",
                        "Please enter collector name, phone number and area.",
                        "error"
                    );
                    return;
                }

                setBusy(submitBtn, true);

                try {
                    const payload = {
                        name: name,
                        phone: phone,
                        area: area,
                        waste_types: wasteTypes,
                        notes: notes,
                    };

                    await apiRequest(
                        "/api/waste/collectors/",
                        "POST",
                        payload
                    );

                    showAlert(
                        "wasteAlert",
                        "Waste collector information shared successfully!",
                        "success"
                    );

                    collectorForm.reset();

                    if (areaInput && area) {
                        areaInput.value = area;
                    }

                    loadAvailableCollectors(area);

                } catch (err) {
                    showAlert(
                        "wasteAlert",
                        err.message ||
                        "Failed to share collector information.",
                        "error"
                    );
                } finally {
                    setBusy(submitBtn, false);
                }
            }
        );
    }
}


// ============================================================
// Load shared waste collectors
// ============================================================

async function loadAvailableCollectors(area) {
    const container =
        document.getElementById("collectorsList");

    const emptyNotice =
        document.getElementById("collectorsEmpty");

    if (!container) {
        return;
    }

    try {
        const query = area
            ? "?area=" + encodeURIComponent(area)
            : "";

        const res = await apiRequest(
            "/api/waste/collectors/" + query,
            "GET"
        );

        console.log("WASTE COLLECTORS RESPONSE:", res);

        let collectors = [];

        if (Array.isArray(res)) {
            collectors = res;
        } else if (
            res &&
            Array.isArray(res.results)
        ) {
            collectors = res.results;
        } else if (
            res &&
            Array.isArray(res.data)
        ) {
            collectors = res.data;
        }

        container.innerHTML = "";

        if (collectors.length === 0) {
            if (emptyNotice) {
                emptyNotice.hidden = false;
            }
            return;
        }

        if (emptyNotice) {
            emptyNotice.hidden = true;
        }

        collectors.forEach(function (collector) {
            const card =
                document.createElement("div");

            card.className = "collector-card";

            const average =
                Number(
                    collector.average_rating
                ) || 0;

            const ratingCount =
                Number(
                    collector.rating_count
                ) || 0;

            card.innerHTML = `
                <div class="collector-info">

                    <div class="collector-avatar">
                        ♻️
                    </div>

                    <div>

                        <h3 class="collector-name">
                            ${escapeHtml(
                collector.name ||
                "Waste Collector"
            )}
                        </h3>

                        <p class="collector-meta">
                            📍 ${escapeHtml(
                collector.area ||
                "Area not specified"
            )}
                        </p>

                        <p class="collector-meta">
                            🗑️ ${escapeHtml(
                collector.waste_types ||
                "Waste collection service"
            )}
                        </p>

                        <p class="collector-meta">
                            👤 Shared by
                            ${escapeHtml(
                collector.shared_by_name ||
                "HELPNET user"
            )}
                        </p>

                        ${collector.notes
                    ? `
                                    <p class="collector-meta">
                                        📝 ${escapeHtml(
                        collector.notes
                    )}
                                    </p>
                                `
                    : ""
                }

                        <p class="collector-meta">
                            ⭐ ${average.toFixed(1)}
                            (${ratingCount} ${ratingCount === 1
                    ? "rating"
                    : "ratings"
                })
                        </p>

                    </div>

                </div>

                <div class="collector-actions">

    ${collector.phone
                    ? `
                <a
                    href="tel:${escapeHtml(
                        collector.phone
                    )}"
                    class="btn-sm btn-call"
                >
                    📞 Call
                </a>
            `
                    : ""
                }

    <button
        type="button"
        class="btn-sm btn-rate"
        data-collector-id="${escapeHtml(
                    collector.id
                )}"
    >
        ⭐ ${collector.user_rating
                    ? "Update Rating"
                    : "Rate"
                }
    </button>

</div>
            `;
            const rateButton =
                card.querySelector(
                    ".btn-rate"
                );

            if (rateButton) {
                rateButton.addEventListener(
                    "click",
                    function () {
                        openRatingModal(
                            collector
                        );
                    }
                );
            }
            container.appendChild(card);
        });

    } catch (err) {
        console.error(
            "Error loading waste collectors:",
            err
        );

        container.innerHTML = `
            <p class="activity-empty">
                Failed to load waste collectors.
            </p>
        `;

        if (emptyNotice) {
            emptyNotice.hidden = true;
        }
    }
}


// ============================================================
// Load my waste pickup requests
// ============================================================

async function loadMyRequests() {
    const container =
        document.getElementById("requestsList");

    const emptyNotice =
        document.getElementById("requestsEmpty");

    if (!container) {
        return;
    }

    try {
        const res = await apiRequest(
            "/api/waste/requests/",
            "GET"
        );

        const requests =
            Array.isArray(res)
                ? res
                : (
                    res && Array.isArray(res.results)
                        ? res.results
                        : (
                            res &&
                                Array.isArray(res.data)
                                ? res.data
                                : []
                        )
                );

        container.innerHTML = "";

        if (requests.length === 0) {
            if (emptyNotice) {
                emptyNotice.hidden = false;
            }
            return;
        }

        if (emptyNotice) {
            emptyNotice.hidden = true;
        }

        requests.forEach(function (req) {
            const card =
                document.createElement("div");

            card.className = "request-card";

            const statusClass =
                "status-" +
                (req.status || "requested")
                    .toLowerCase();

            const dateStr =
                req.preferred_pickup_date ||
                (
                    req.created_at
                        ? req.created_at.split("T")[0]
                        : ""
                );

            const timeStr =
                req.preferred_pickup_time
                    ? " (" +
                    req.preferred_pickup_time +
                    ")"
                    : "";

            let actionButtons = "";

            if (req.status === "Requested") {
                actionButtons += `
                    <button
                        class="btn-xs btn-outline"
                        onclick="updateRequestStatus(
                            '${req.id}',
                            'Contacted'
                        )"
                    >
                        Mark Contacted
                    </button>

                    <button
                        class="btn-xs btn-danger-outline"
                        onclick="updateRequestStatus(
                            '${req.id}',
                            'Cancelled'
                        )"
                    >
                        Cancel
                    </button>
                `;
            }

            else if (req.status === "Contacted") {
                actionButtons += `
                    <button
                        class="btn-xs btn-success-outline"
                        onclick="updateRequestStatus(
                            '${req.id}',
                            'Completed'
                        )"
                    >
                        Mark Completed
                    </button>

                    <button
                        class="btn-xs btn-danger-outline"
                        onclick="updateRequestStatus(
                            '${req.id}',
                            'Cancelled'
                        )"
                    >
                        Cancel
                    </button>
                `;
            }

            // Shared collector information
            let collectorHtml = "";

            if (req.collector_details) {
                const collector =
                    req.collector_details;

                collectorHtml = `
                    <div class="request-collector-box">
                        <span>
                            Collector:
                            <strong>
                                ${escapeHtml(
                    collector.name ||
                    "Waste Collector"
                )}
                            </strong>

                            ${collector.phone
                        ? `
                                        (${escapeHtml(
                            collector.phone
                        )})
                                    `
                        : ""
                    }
                        </span>

                        ${collector.phone
                        ? `
                                    <a
                                        href="tel:${escapeHtml(
                            collector.phone
                        )}"
                                        class="rate-link"
                                    >
                                        📞 Call Collector
                                    </a>
                                `
                        : ""
                    }
                    </div>
                `;
            } else {
                collectorHtml = `
                    <div class="request-collector-box">
                        <span class="text-muted">
                            Shared collectors for this area
                            are listed above.
                        </span>
                    </div>
                `;
            }

            card.innerHTML = `
                <div class="request-header">
                    <div>
                        <span class="request-type-badge">
                            ${escapeHtml(
                req.waste_type
            )}
                        </span>

                        <h4 class="request-title">
                            📍 ${escapeHtml(
                req.area
            )}
                            —
                            ${escapeHtml(
                req.location
            )}
                        </h4>
                    </div>

                    <span class="status ${statusClass}">
                        ${escapeHtml(
                req.status
            )}
                    </span>
                </div>

                <div class="request-body">
                    <p class="request-datetime">
                        🗓️ Pickup Preferred:
                        <strong>
                            ${escapeHtml(
                dateStr + timeStr
            )}
                        </strong>
                    </p>

                    ${req.notes
                    ? `
                                <p class="request-notes">
                                    📝 ${escapeHtml(
                        req.notes
                    )}
                                </p>
                            `
                    : ""
                }

                    ${collectorHtml}
                </div>

                <div class="request-actions">
                    ${actionButtons}
                </div>
            `;

            container.appendChild(card);
        });

    } catch (err) {
        console.error(
            "Error loading waste requests:",
            err
        );
    }
}


// ============================================================
// Update request status
// ============================================================

async function updateRequestStatus(
    requestId,
    newStatus
) {
    try {
        await apiRequest(
            "/api/waste/requests/" +
            requestId +
            "/",
            "PATCH",
            {
                status: newStatus,
            }
        );

        loadMyRequests();

    } catch (err) {
        alert(
            err.message ||
            "Failed to update status."
        );
    }
}


// ============================================================
// Helpers
// ============================================================

function debounce(func, wait) {
    let timeout;

    return function (...args) {
        clearTimeout(timeout);

        timeout = setTimeout(
            () => func.apply(this, args),
            wait
        );
    };
}


function escapeHtml(text) {
    if (!text) {
        return "";
    }

    return String(text)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// ============================================================
// Waste Collector Rating Modal
// ============================================================

let selectedCollectorId = null;


function openRatingModal(collector) {
    console.log("OPEN RATING MODAL:", collector);

    const modal = document.getElementById("ratingModal");
    const nameElement = document.getElementById("ratingCollectorName");
    const ratingInput = document.getElementById("collectorRating");
    const reviewInput = document.getElementById("collectorReview");
    const ratingValue = document.getElementById("ratingValue");

    console.log("RATING MODAL ELEMENT:", modal);

    if (!modal) {
        console.error("ERROR: #ratingModal was not found.");
        return;
    }

    selectedCollectorId = collector.id;

    if (nameElement) {
        nameElement.textContent =
            collector.name || "Waste Collector";
    }

    const existingRating = collector.user_rating;

    const rating =
        existingRating && existingRating.rating
            ? Number(existingRating.rating)
            : 0;

    if (ratingInput) {
        ratingInput.value = rating;
    }

    if (reviewInput) {
        reviewInput.value =
            existingRating && existingRating.review
                ? existingRating.review
                : "";
    }

    updateRatingStars(rating);

    if (ratingValue) {
        ratingValue.textContent =
            rating ? `${rating}/5` : "Select a rating";
    }

    // IMPORTANT: explicitly show the modal
    modal.hidden = false;
    modal.style.display = "flex";

    console.log("RATING MODAL OPENED");
}


function closeRatingModal() {
    const modal =
        document.getElementById("ratingModal");

    if (modal) {
        modal.hidden = true;
    }

    selectedCollectorId = null;

    updateRatingStars(0);
}


function updateRatingStars(value) {
    const stars =
        document.querySelectorAll(
            ".rating-star"
        );

    stars.forEach(function (star) {
        const starValue =
            Number(
                star.dataset.value
            );

        star.classList.toggle(
            "selected",
            starValue <= value
        );
    });
}

// ============================================================
// Rating Modal Events
// ============================================================

document.addEventListener("DOMContentLoaded", function () {

    const stars =
        document.querySelectorAll(".rating-star");

    const ratingInput =
        document.getElementById("collectorRating");

    const ratingValue =
        document.getElementById("ratingValue");

    const closeButton =
        document.getElementById("closeRatingModal");

    const cancelButton =
        document.getElementById("cancelRating");

    const ratingForm =
        document.getElementById("collectorRatingForm");


    // Select star rating
    stars.forEach(function (star) {

        star.addEventListener(
            "click",
            function () {

                const value =
                    Number(
                        star.dataset.value
                    );

                if (ratingInput) {
                    ratingInput.value = value;
                }

                updateRatingStars(value);

                if (ratingValue) {
                    ratingValue.textContent =
                        `${value}/5`;
                }
            }
        );

    });


    // Close button
    if (closeButton) {
        closeButton.addEventListener(
            "click",
            closeRatingModal
        );
    }


    // Cancel button
    if (cancelButton) {
        cancelButton.addEventListener(
            "click",
            closeRatingModal
        );
    }


    // Submit rating
    if (ratingForm) {

        ratingForm.addEventListener(
            "submit",
            async function (e) {

                e.preventDefault();

                const rating =
                    Number(
                        document.getElementById(
                            "collectorRating"
                        ).value
                    );

                const review =
                    document.getElementById(
                        "collectorReview"
                    ).value.trim();

                const errorBox =
                    document.getElementById(
                        "ratingError"
                    );

                const submitButton =
                    document.getElementById(
                        "submitCollectorRating"
                    );


                if (!selectedCollectorId) {
                    return;
                }


                if (rating < 1 || rating > 5) {

                    if (errorBox) {
                        errorBox.textContent =
                            "Please select a rating from 1 to 5.";
                        errorBox.hidden = false;
                    }

                    return;
                }


                if (errorBox) {
                    errorBox.hidden = true;
                }


                setBusy(
                    submitButton,
                    true
                );


                try {

                    await apiRequest(
                        "/api/waste/collectors/" +
                            selectedCollectorId +
                            "/ratings/",
                        "POST",
                        {
                            rating: rating,
                            review: review
                        }
                    );


                    closeRatingModal();

                    showAlert(
                        "wasteAlert",
                        "Rating submitted successfully!",
                        "success"
                    );


                    const areaInput =
                        document.getElementById(
                            "pickupArea"
                        );

                    const area =
                        areaInput
                            ? areaInput.value.trim()
                            : "";

                    loadAvailableCollectors(area);


                } catch (err) {

                    console.error(
                        "Rating submission error:",
                        err
                    );

                    if (errorBox) {

                        errorBox.textContent =
                            err.message ||
                            "Failed to submit rating.";

                        errorBox.hidden = false;

                    }

                } finally {

                    setBusy(
                        submitButton,
                        false
                    );

                }

            }
        );

    }

});