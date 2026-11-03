document.addEventListener("DOMContentLoaded", async function () {
    const user = typeof getStoredUser === "function"
        ? getStoredUser()
        : null;

    if (!user || user.is_superuser !== true) {
        window.location.href = user ? "/dashboard/" : "/login/";
        return;
    }

    const list = document.getElementById("ngoApplicationList");
    const message = document.getElementById("ngoMessage");
    const refreshButton = document.getElementById("refreshNGOs");

    function translate(key, fallback = key) {
        return typeof t === "function" ? t(key) : fallback;
    }

    function showMessage(text) {
        message.textContent = text;
    }

    function addDetail(container, label, value) {
        const row = document.createElement("p");
        const strong = document.createElement("strong");
        strong.textContent = `${label}: `;
        row.append(strong, document.createTextNode(
            value || translate("notProvided", "Not provided")
        ));
        container.appendChild(row);
    }

    async function downloadDocument(documentInfo, link) {
        const token = typeof getToken === "function" ? getToken() : null;
        if (!token) throw new Error("Please sign in again to download documents.");

        link.setAttribute("aria-busy", "true");
        try {
            const response = await fetch(documentInfo.download_url, {
                headers: { Authorization: `Bearer ${token}` }
            });
            if (!response.ok) {
                throw new Error(`Document download failed (${response.status}).`);
            }
            const objectUrl = URL.createObjectURL(await response.blob());
            const download = document.createElement("a");
            download.href = objectUrl;
            download.download = documentInfo.name;
            document.body.appendChild(download);
            download.click();
            download.remove();
            window.setTimeout(() => URL.revokeObjectURL(objectUrl), 1000);
        } finally {
            link.removeAttribute("aria-busy");
        }
    }

    function renderApplication(ngo) {
        const card = document.createElement("article");
        card.className = "ngo-application";

        const heading = document.createElement("h3");
        heading.textContent = ngo.display_name || ngo.full_name ||
            translate("unnamedApplicant", "Unnamed NGO applicant");
        card.appendChild(heading);

        const details = document.createElement("div");
        details.className = "ngo-details";
        const statusKey = `ngoVerification_${ngo.ngo_verification_status}`;
        addDetail(
            details,
            translate("verificationStatusLabel", "Verification status"),
            translate(statusKey, ngo.ngo_verification_status)
        );
        addDetail(details, translate("ngoRegistrationNumber", "Registration number"), ngo.ngo_registration_number);
        addDetail(details, translate("ngoOrganizationAddress", "Organization address"), ngo.ngo_address);
        addDetail(details, translate("ngoContactEmail", "Official contact email"), ngo.ngo_contact_email);
        addDetail(details, translate("ngoContactPhone", "Contact phone number"), ngo.ngo_contact_phone);
        addDetail(details, translate("ngoRepresentativeName", "Authorized representative"), ngo.ngo_representative_name);
        addDetail(details, translate("emailLabel", "Account email"), ngo.email);
        addDetail(details, translate("phoneLabel", "Account phone"), ngo.phone_number);
        addDetail(details, translate("submittedLabel", "Submitted"), ngo.ngo_submitted_at
            ? new Date(ngo.ngo_submitted_at).toLocaleString()
            : translate("notAvailable", "Not available"));
        addDetail(details, translate("reviewedLabel", "Last reviewed"), ngo.ngo_reviewed_at
            ? new Date(ngo.ngo_reviewed_at).toLocaleString()
            : translate("notAvailable", "Not available"));
        if (ngo.ngo_verification_reason) {
            addDetail(
                details,
                translate("reviewReason", "Review reason"),
                ngo.ngo_verification_reason
            );
        }
        card.appendChild(details);

        const documentsHeading = document.createElement("h4");
        documentsHeading.textContent = translate("ngoSubmittedDocuments", "Submitted documents");
        card.appendChild(documentsHeading);
        const documentList = document.createElement("ul");
        documentList.className = "ngo-document-list";
        (Array.isArray(ngo.documents) ? ngo.documents : []).forEach(
            function (documentInfo) {
                const item = document.createElement("li");
                const link = document.createElement("a");
                link.href = documentInfo.download_url;
                link.textContent = `${translate(
                    `ngoDocument_${documentInfo.document_type}`,
                    documentInfo.document_type
                )}: ${documentInfo.name}`;
                link.addEventListener("click", async function (event) {
                    event.preventDefault();
                    try {
                        await downloadDocument(documentInfo, link);
                    } catch (error) {
                        console.error("NGO document download failed:", error);
                        showMessage(error.message || "Could not download the document.");
                    }
                });
                item.appendChild(link);
                documentList.appendChild(item);
            }
        );
        if (documentList.childElementCount === 0) {
            const empty = document.createElement("li");
            empty.textContent = translate("noNGODocuments", "No documents uploaded.");
            documentList.appendChild(empty);
        }
        card.appendChild(documentList);

        const reasonLabel = document.createElement("label");
        reasonLabel.textContent = translate("reviewReason", "Review reason");
        const reason = document.createElement("textarea");
        reason.className = "ngo-review-reason";
        reason.rows = 3;
        reason.maxLength = 2000;
        reasonLabel.appendChild(reason);
        card.appendChild(reasonLabel);

        const actions = document.createElement("div");
        actions.className = "ngo-actions";
        const actionItems = [
            {
                status: "under_review",
                className: "review-button",
                label: translate("markUnderReview", "Mark Under Review")
            },
            {
                status: "approved",
                className: "approve-button",
                label: translate("approve", "Approve")
            },
            {
                status: "rejected",
                className: "reject-button",
                label: translate("reject", "Reject")
            },
            {
                status: "additional_documents_required",
                className: "request-documents-button",
                label: translate("requestAdditionalDocuments", "Request Additional Documents")
            }
        ];

        actionItems.forEach(function (action) {
            const button = document.createElement("button");
            button.type = "button";
            button.className = action.className;
            button.textContent = action.label;
            button.addEventListener("click", async function () {
                const reviewReason = reason.value.trim();
                if (
                    ["rejected", "additional_documents_required"].includes(
                        action.status
                    ) &&
                    !reviewReason
                ) {
                    reason.setCustomValidity(
                        translate("reviewReasonRequired", "A reason is required.")
                    );
                    reason.reportValidity();
                    return;
                }
                reason.setCustomValidity("");
                if (
                    ["approved", "rejected"].includes(action.status) &&
                    !window.confirm(
                        translate(
                            action.status === "approved"
                                ? "confirmApproveNGO"
                                : "confirmRejectNGO",
                            "Confirm this NGO review decision?"
                        )
                    )
                ) {
                    return;
                }

                actions.querySelectorAll("button").forEach((item) => {
                    item.disabled = true;
                });
                showMessage(translate("updatingNGOApplication", "Updating NGO application..."));
                try {
                    const response = await apiRequest(
                        `/api/auth/ngo-profiles/${encodeURIComponent(
                            ngo.profile_id
                        )}/approval/`,
                        "PATCH",
                        {
                            verification_status: action.status,
                            review_reason: reviewReason
                        }
                    );
                    if (!response || response.success !== true) {
                        throw new Error("The server did not confirm the update.");
                    }
                    showMessage(translate(
                        "ngoApplicationUpdated",
                        "NGO application updated."
                    ));
                    await loadPendingNGOs();
                } catch (error) {
                    console.error("NGO review update failed:", error);
                    showMessage(error.message || translate(
                        "ngoApplicationUpdateFailed",
                        "Could not update the NGO application."
                    ));
                    actions.querySelectorAll("button").forEach((item) => {
                        item.disabled = false;
                    });
                }
            });
            actions.appendChild(button);
        });
        card.appendChild(actions);
        list.appendChild(card);
    }

    async function loadPendingNGOs() {
        list.replaceChildren();
        showMessage(translate("loadingNGOApplications", "Loading NGO applications..."));
        refreshButton.disabled = true;

        try {
            const result = await apiRequest("/api/auth/ngo-profiles/pending/");
            if (!result || result.success !== true ||
                !Array.isArray(result.data)) {
                throw new Error("Unexpected response from the server.");
            }

            if (result.data.length === 0) {
                showMessage(translate("noPendingNGOApplications", "No applications require review."));
                return;
            }

            showMessage(
                `${result.data.length} · ${translate(
                    "pendingNGOApplications",
                    "NGO Applications Requiring Review"
                )}`
            );
            result.data.forEach(renderApplication);
        } catch (error) {
            console.error("NGO applications could not be loaded:", error);
            showMessage(error.message || translate(
                "ngoApplicationsLoadFailed",
                "Could not load NGO applications."
            ));
        } finally {
            refreshButton.disabled = false;
        }
    }

    refreshButton.addEventListener("click", loadPendingNGOs);
    await loadPendingNGOs();
});
