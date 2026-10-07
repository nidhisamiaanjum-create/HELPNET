document.addEventListener("DOMContentLoaded", async function () {
    if (typeof requireLogin === "function" && !requireLogin()) {
        return;
    }

    const user = typeof getStoredUser === "function"
        ? getStoredUser()
        : null;

    if (
        !user ||
        !user.role ||
        user.role.toLowerCase() !== "admin"
    ) {
        window.location.href = "/dashboard/";
        return;
    }

    const list = document.getElementById("verificationList");

    if (!list) {
        return;
    }

    const token = localStorage.getItem("helpnet_token");

    async function loadRequests() {
        list.innerHTML = `
            <p>Loading verification requests...</p>
        `;

        try {
            const response = await fetch(
                "/api/verification/admin/",
                {
                    method: "GET",
                    headers: {
                        Authorization: `Bearer ${token}`
                    }
                }
            );

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    data.message ||
                    "Could not load verification requests."
                );
            }

            const requests = data.data || [];

            if (requests.length === 0) {
                list.innerHTML = `
                    <p>
                        No pending verification requests.
                    </p>
                `;
                return;
            }

            list.innerHTML = "";

            requests.forEach(function (item) {
                const card = document.createElement("div");

                card.className = "card";

                card.innerHTML = `
                    <h3>${item.full_name}</h3>

                    <p>
                        <strong>Email:</strong>
                        ${item.email}
                    </p>

                    <p>
                        <strong>Phone:</strong>
                        ${item.phone_number}
                    </p>

                    <p>
                        <strong>Document:</strong>
                        ${item.document_type}
                    </p>

                    <p>
                        <strong>Status:</strong>
                        ${item.status}
                    </p>

                    <p>
                        <strong>Submitted:</strong>
                        ${new Date(
                            item.submitted_at
                        ).toLocaleString()}
                    </p>

                    ${
                        item.document_url
                            ? `
                                <p>
                                    <a
                                        href="${item.document_url}"
                                        target="_blank"
                                        rel="noopener"
                                    >
                                        View Document
                                    </a>
                                </p>
                            `
                            : ""
                    }

                    <div class="verification-actions">
                        <button
                            type="button"
                            class="btn approve-btn"
                            data-id="${item.id}"
                        >
                            Approve
                        </button>

                        <button
                            type="button"
                            class="btn reject-btn"
                            data-id="${item.id}"
                        >
                            Reject
                        </button>
                    </div>

                    <div
                        class="reject-box"
                        id="reject-box-${item.id}"
                        hidden
                    >
                        <textarea
                            id="reject-reason-${item.id}"
                            placeholder="Enter rejection reason"
                            rows="3"
                        ></textarea>

                        <button
                            type="button"
                            class="btn confirm-reject-btn"
                            data-id="${item.id}"
                        >
                            Confirm Reject
                        </button>
                    </div>
                `;

                list.appendChild(card);
            });

            attachActionHandlers();

        } catch (error) {
            console.error(error);

            list.innerHTML = `
                <p class="form-error">
                    ${error.message || "Failed to load requests."}
                </p>
            `;
        }
    }

    function attachActionHandlers() {
        document.querySelectorAll(".approve-btn").forEach(function (button) {
            button.addEventListener("click", async function () {
                const verificationId = button.dataset.id;

                const confirmed = window.confirm(
                    "Are you sure you want to approve this verification?"
                );

                if (!confirmed) {
                    return;
                }

                await performAction(
                    verificationId,
                    "approve",
                    ""
                );
            });
        });

        document.querySelectorAll(".reject-btn").forEach(function (button) {
            button.addEventListener("click", function () {
                const verificationId = button.dataset.id;

                const box = document.getElementById(
                    `reject-box-${verificationId}`
                );

                if (box) {
                    box.hidden = !box.hidden;
                }
            });
        });

        document.querySelectorAll(".confirm-reject-btn").forEach(function (button) {
            button.addEventListener("click", async function () {
                const verificationId = button.dataset.id;

                const reasonInput = document.getElementById(
                    `reject-reason-${verificationId}`
                );

                const reason = reasonInput
                    ? reasonInput.value.trim()
                    : "";

                if (!reason) {
                    alert("Please enter a rejection reason.");
                    return;
                }

                await performAction(
                    verificationId,
                    "reject",
                    reason
                );
            });
        });
    }

    async function performAction(
        verificationId,
        action,
        reason
    ) {
        try {
            const response = await fetch(
                `/api/verification/admin/${verificationId}/action/`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${token}`
                    },
                    body: JSON.stringify({
                        action: action,
                        reason: reason
                    })
                }
            );

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    data.message ||
                    "Verification action failed."
                );
            }

            alert(data.message);

            await loadRequests();

        } catch (error) {
            console.error(error);

            alert(
                error.message ||
                "Verification action failed."
            );
        }
    }

    await loadRequests();
});