document.addEventListener("DOMContentLoaded", async function () {
    if (typeof requireLogin === "function" && !requireLogin()) {
        return;
    }

    const user = typeof getStoredUser === "function"
        ? getStoredUser()
        : null;

    const role = String(user?.role || "").trim().toLowerCase();
    const isAdmin =
        user?.is_superuser === true ||
        user?.is_staff === true ||
        role === "admin";

    if (!isAdmin) {
        window.location.href = "/dashboard/";
        return;
    }

    const list = document.getElementById("verificationList");

    if (!list) {
        return;
    }

    const token = localStorage.getItem("helpnet_token");

    function showListMessage(message, className = "") {
        const paragraph = document.createElement("p");
        paragraph.className = className;
        paragraph.textContent = message;
        list.replaceChildren(paragraph);
    }

    function appendDetail(card, label, value) {
        const paragraph = document.createElement("p");
        const strong = document.createElement("strong");
        strong.textContent = `${label}: `;
        paragraph.append(strong, document.createTextNode(value || ""));
        card.appendChild(paragraph);
    }

    async function loadRequests() {
        showListMessage("Loading verification requests...");

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
                showListMessage("No pending verification requests.");
                return;
            }

            list.replaceChildren();

            requests.forEach(function (item) {
                const card = document.createElement("div");

                card.className = "card";

                const heading = document.createElement("h3");
                heading.textContent = item.full_name || "";
                card.appendChild(heading);
                appendDetail(card, "Email", item.email);
                appendDetail(card, "Phone", item.phone_number);
                appendDetail(card, "Document", item.document_type);
                appendDetail(card, "Status", item.status);

                const submittedAt = item.submitted_at
                    ? new Date(item.submitted_at).toLocaleString()
                    : "";
                appendDetail(card, "Submitted", submittedAt);

                if (item.document_url) {
                    const documentLink = document.createElement("a");
                    documentLink.href =
                        `/api/verification/admin/${encodeURIComponent(item.id)}/document/`;
                    documentLink.target = "_blank";
                    documentLink.rel = "noopener";
                    documentLink.textContent = "View Document";
                    card.appendChild(documentLink);
                }

                const actions = document.createElement("div");
                actions.className = "verification-actions";
                for (const [label, className] of [
                    ["Approve", "approve-btn"],
                    ["Reject", "reject-btn"],
                ]) {
                    const button = document.createElement("button");
                    button.type = "button";
                    button.className = `btn ${className}`;
                    button.dataset.id = item.id;
                    button.textContent = label;
                    actions.appendChild(button);
                }
                card.appendChild(actions);

                const rejectBox = document.createElement("div");
                rejectBox.className = "reject-box";
                rejectBox.id = `reject-box-${item.id}`;
                rejectBox.hidden = true;

                const reason = document.createElement("textarea");
                reason.id = `reject-reason-${item.id}`;
                reason.placeholder = "Enter rejection reason";
                reason.rows = 3;
                rejectBox.appendChild(reason);

                const confirmReject = document.createElement("button");
                confirmReject.type = "button";
                confirmReject.className = "btn confirm-reject-btn";
                confirmReject.dataset.id = item.id;
                confirmReject.textContent = "Confirm Reject";
                rejectBox.appendChild(confirmReject);
                card.appendChild(rejectBox);

                list.appendChild(card);
            });

            attachActionHandlers();

        } catch (error) {
            console.error(error);
            showListMessage(
                error.message || "Failed to load requests.",
                "form-error"
            );
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
                `/api/verification/admin/${encodeURIComponent(verificationId)}/action/`,
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