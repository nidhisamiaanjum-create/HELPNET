
document.addEventListener("DOMContentLoaded", async function () {
    const user = typeof getStoredUser === "function"
        ? getStoredUser()
        : null;

    if (!user) {
        window.location.href = "/login/";
        return;
    }

    if (
    !user ||
    (
        user.is_superuser !== true &&
        String(user.role || "").toLowerCase() !== "admin"
    )
) {
    window.location.href = "/dashboard/";
    return;
}

    const list = document.getElementById("ngoApplicationList");
    const message = document.getElementById("ngoMessage");
    const refreshButton = document.getElementById("refreshNGOs");

    function showMessage(text) {
        message.textContent = text;
    }

    async function loadPendingNGOs() {
        list.replaceChildren();
        showMessage("Loading NGO applications...");
        refreshButton.disabled = true;

        try {
            const result = await apiRequest(
                "/api/auth/ngo-profiles/pending/"
            );

            if (!result || result.success !== true ||
                !Array.isArray(result.data)) {
                throw new Error("Unexpected response from the server.");
            }

            if (result.data.length === 0) {
                showMessage("No pending NGO applications.");
                return;
            }

            showMessage(
                result.data.length + " pending NGO application(s)."
            );

            result.data.forEach(function (ngo) {
                const card = document.createElement("article");
                card.className = "ngo-application";

                const heading = document.createElement("h3");
                heading.textContent = ngo.full_name || "Unnamed applicant";
                card.appendChild(heading);

                const details = document.createElement("div");
                details.className = "ngo-details";

                const email = document.createElement("p");
                email.textContent = "Email: " + (ngo.email || "Not provided");

                const phone = document.createElement("p");
                phone.textContent = "Phone: " + (ngo.phone_number || "Not provided");

                const location = document.createElement("p");
                location.textContent = "Location: " + (ngo.location || "Not provided");

                const submitted = document.createElement("p");
                submitted.textContent = "Submitted: " +
                    (ngo.created_at
                        ? new Date(ngo.created_at).toLocaleString()
                        : "Not available");

                const status = document.createElement("p");
                status.textContent = "Approval status: Pending";

                details.append(email, phone, location, submitted, status);
                card.appendChild(details);

                const actions = document.createElement("div");
                actions.className = "ngo-actions";

                const approve = document.createElement("button");
                approve.type = "button";
                approve.className = "approve-button";
                approve.textContent = "Approve";

                const reject = document.createElement("button");
                reject.type = "button";
                reject.className = "reject-button";
                reject.textContent = "Reject";

                async function updateApproval(approvalStatus) {
                    const actionLabel = approvalStatus === "approved"
                        ? "approve"
                        : "reject";

                    if (!window.confirm(
                        "Are you sure you want to " + actionLabel +
                        " this NGO application?"
                    )) {
                        return;
                    }

                    approve.disabled = true;
                    reject.disabled = true;
                    showMessage("Updating NGO application...");

                    try {
                        const response = await apiRequest(
                            "/api/auth/ngo-profiles/" +
                                encodeURIComponent(ngo.profile_id) +
                                "/approval/",
                            "PATCH",
                            { approval_status: approvalStatus }
                        );

                        if (!response || response.success !== true) {
                            throw new Error(
                                "The server did not confirm the update."
                            );
                        }

                        showMessage(
                            "NGO application " + approvalStatus + "."
                        );

                        await loadPendingNGOs();
                    } catch (error) {
                        showMessage(
                            "Could not update the application: " +
                            (error.message || "Please try again.")
                        );
                        approve.disabled = false;
                        reject.disabled = false;
                    }
                }

                approve.addEventListener("click", function () {
                    updateApproval("approved");
                });

                reject.addEventListener("click", function () {
                    updateApproval("rejected");
                });

                actions.append(approve, reject);
                card.appendChild(actions);
                list.appendChild(card);
            });
        } catch (error) {
            showMessage(
                "Could not load NGO applications: " +
                (error.message || "Please try again.")
            );
        } finally {
            refreshButton.disabled = false;
        }
    }

    refreshButton.addEventListener("click", loadPendingNGOs);
    await loadPendingNGOs();
});
