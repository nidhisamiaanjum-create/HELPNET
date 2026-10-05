function moderationMessage(message, type = "") {
    const target = document.getElementById("moderationMessage");

    if (!target) return;

    target.textContent = message;
    target.className = `form-message ${type}`;
}


function moderationButton(label, action, callback) {
    const button = document.createElement("button");

    button.type = "button";
    button.className =
        action === "remove"
            ? "btn-xs btn-danger"
            : "small-btn";

    button.textContent = label;

    button.addEventListener("click", async () => {
        // Prevent double clicking
        if (button.disabled) return;

        button.disabled = true;

        try {
            await callback();
        } finally {
            button.disabled = false;
        }
    });

    return button;
}


/*
 * Submit moderation action
 */
async function submitModeration(payload) {
    try {
        console.log("MODERATION PAYLOAD:", payload);

        const response = await apiRequest(
            "/api/reports/moderation/",
            "POST",
            payload
        );

        console.log("MODERATION SUCCESS:", response);

        moderationMessage(
            t(
                payload.action === "remove"
                    ? "moderationRemoved"
                    : payload.action === "review"
                        ? "moderationReviewed"
                        : "moderationSaved"
            ),
            "success"
        );

        /*
         * Reload both sections.
         *
         * This is important because:
         * - report status may change
         * - content may be edited
         * - content may be removed
         */
        await Promise.all([
            loadModerationReports(),
            loadModerationContent()
        ]);

    } catch (error) {
        console.error("MODERATION ERROR:", error);

        moderationMessage(
            error.message || t("moderationFailed"),
            "error"
        );
    }
}


/*
 * Load reports
 */
async function loadModerationReports() {
    const container = document.getElementById("moderationReports");

    if (!container) return;

    try {
        const response = await apiRequest("/api/reports/");

        console.log("REPORTS API RESPONSE:", response);

        /*
         * Clear old reports before rendering.
         */
        container.replaceChildren();

        /*
         * Support both:
         *
         * [
         *   {...},
         *   {...}
         * ]
         *
         * and:
         *
         * {
         *   data: [...]
         * }
         */
        const reports = Array.isArray(response)
            ? response
            : Array.isArray(response?.data)
                ? response.data
                : [];

        if (!reports.length) {
            const empty = document.createElement("p");

            empty.className = "hint";
            empty.textContent = t("moderationEmpty");

            container.appendChild(empty);
            return;
        }


        /*
         * Prevent duplicate report IDs from being rendered.
         */
        const uniqueReports = [];
        const seenReports = new Set();

        reports.forEach((report) => {
            const reportId = String(report.id);

            if (seenReports.has(reportId)) {
                console.warn(
                    "Duplicate report ignored:",
                    reportId
                );
                return;
            }

            seenReports.add(reportId);
            uniqueReports.push(report);
        });


        uniqueReports.forEach((report) => {
            const card = document.createElement("article");

            card.className = "admin-item";
            card.dataset.reportId = report.id;


            /*
             * Report title
             */
            const title = document.createElement("h2");

            const statusKey =
                `reportStatus${report.status
                    .charAt(0)
                    .toUpperCase()}${report.status.slice(1)}`;

            let categoryText;

            if (report.category === "fraud") {
                categoryText = t("reportFraud");
            } else if (report.category === "other") {
                categoryText = t("reportOther");
            } else {
                categoryText = report.category;
            }

            let statusText;

            try {
                statusText = t(statusKey);
            } catch (_) {
                statusText = report.status;
            }

            title.textContent =
                `${categoryText} · ${statusText}`;

            card.appendChild(title);


            /*
             * Description
             */
            const description = document.createElement("p");

            description.textContent =
                report.description || "";

            card.appendChild(description);


            /*
             * Reported content
             */
            if (
                report.status === "pending" &&
                report.content_type &&
                report.object_id
            ) {
                const target = document.createElement("p");

                const typeKeys = {
                    "blood.bloodrequest": "bloodPageTitle",
                    "goods.goodslisting": "moderationGoods",
                    "farmer.producelisting": "moderationFarmer",
                    "volunteer.volunteeropportunity":
                        "moderationVolunteer"
                };

                const contentName = t(
                    typeKeys[report.content_type]
                    || "moderationContentType"
                );

                target.textContent =
                    `${contentName} #${report.object_id}: ${report.content_summary || ""}`;

                card.appendChild(target);
            }


            /*
             * Reason input
             */
            const reason = document.createElement("input");

            reason.type = "text";
            reason.maxLength = 1000;
            reason.placeholder = t("moderationReason");

            card.appendChild(reason);


            /*
             * Review button
             *
             * Only pending reports can be reviewed.
             */
            if (report.status === "pending") {
                card.appendChild(
                    moderationButton(
                        t("moderationReview"),
                        "review",
                        () => submitModeration({
                            report_id: report.id,
                            action: "review",
                            reason: reason.value.trim()
                        })
                    )
                );
            }


            /*
             * Edit + Remove only if the report
             * has a related content object.
             */
            if (
                report.content_type &&
                report.object_id
            ) {
                /*
                 * Changes textarea
                 */
                const changes =
                    document.createElement("textarea");

                changes.placeholder =
                    t("moderationChanges");

                card.appendChild(changes);


                /*
                 * Action container
                 */
                const actions =
                    document.createElement("div");

                actions.className = "admin-actions";


                /*
                 * EDIT
                 */
                actions.appendChild(
                    moderationButton(
                        t("moderationEdit"),
                        "edit",
                        async () => {
                            let parsed;

                            try {
                                parsed =
                                    JSON.parse(changes.value);
                            } catch (_) {
                                moderationMessage(
                                    t("moderationInvalidChanges"),
                                    "error"
                                );

                                return;
                            }

                            await submitModeration({
                                report_id: report.id,
                                action: "edit",
                                changes: parsed,
                                reason: reason.value.trim()
                            });
                        }
                    )
                );


                /*
                 * REMOVE
                 */
                actions.appendChild(
                    moderationButton(
                        t("moderationRemove"),
                        "remove",
                        async () => {
                            const confirmed = window.confirm(
                                t("moderationConfirmRemove")
                                || "Are you sure you want to remove this content?"
                            );

                            if (!confirmed) {
                                return;
                            }

                            await submitModeration({
                                report_id: report.id,
                                action: "remove",
                                reason: reason.value.trim()
                            });
                        }
                    )
                );

                card.appendChild(actions);
            }


            container.appendChild(card);
        });

    } catch (error) {
        console.error(
            "LOAD MODERATION REPORTS ERROR:",
            error
        );

        moderationMessage(
            t("moderationLoadFailed"),
            "error"
        );
    }
}


/*
 * Load content for direct admin editing/removal
 */
async function loadModerationContent() {
    const container =
        document.getElementById(
            "moderationContentItems"
        );

    const selector =
        document.getElementById(
            "moderationContentType"
        );

    if (!container || !selector) return;

    const contentType = selector.value;

    try {
        const response = await apiRequest(
            `/api/reports/moderation/?content_type=${encodeURIComponent(contentType)}`
        );

        console.log(
            "MODERATION CONTENT RESPONSE:",
            response
        );

        /*
         * Clear previous content.
         */
        container.replaceChildren();


        /*
         * Support:
         *
         * {
         *   data: [...]
         * }
         *
         * and:
         *
         * [...]
         */
        const items = Array.isArray(response)
            ? response
            : Array.isArray(response?.data)
                ? response.data
                : [];


        /*
         * No content
         */
        if (!items.length) {
            const empty = document.createElement("p");

            empty.className = "hint";
            empty.textContent =
                t("moderationEmpty");

            container.appendChild(empty);

            return;
        }


        /*
         * Prevent duplicate content IDs.
         */
        const uniqueItems = [];
        const seenItems = new Set();

        items.forEach((item) => {
            const itemId = String(item.id);

            if (seenItems.has(itemId)) {
                console.warn(
                    "Duplicate content ignored:",
                    itemId
                );

                return;
            }

            seenItems.add(itemId);
            uniqueItems.push(item);
        });


        uniqueItems.forEach((item) => {
            const card =
                document.createElement("article");

            card.className = "admin-item";


            /*
             * Title
             */
            const title =
                document.createElement("h3");

            title.textContent =
                `${item.summary || ""} · #${item.id}`;

            card.appendChild(title);


            /*
             * Editable fields
             */
            const changes =
                document.createElement("textarea");

            changes.value =
                JSON.stringify(
                    item.editable || {},
                    null,
                    2
                );

            changes.setAttribute(
                "aria-label",
                t("moderationChanges")
            );

            card.appendChild(changes);


            /*
             * Reason
             */
            const reason =
                document.createElement("input");

            reason.type = "text";
            reason.maxLength = 1000;
            reason.placeholder =
                t("moderationReason");

            card.appendChild(reason);


            /*
             * Actions
             */
            const actions =
                document.createElement("div");

            actions.className =
                "admin-actions";


            /*
             * EDIT
             */
            actions.appendChild(
                moderationButton(
                    t("moderationEdit"),
                    "edit",
                    async () => {
                        let parsed;

                        try {
                            parsed =
                                JSON.parse(changes.value);
                        } catch (_) {
                            moderationMessage(
                                t("moderationInvalidChanges"),
                                "error"
                            );

                            return;
                        }

                        await submitModeration({
                            content_type: contentType,
                            object_id: item.id,
                            action: "edit",
                            changes: parsed,
                            reason: reason.value.trim()
                        });
                    }
                )
            );


            /*
             * REMOVE
             */
            actions.appendChild(
                moderationButton(
                    t("moderationRemove"),
                    "remove",
                    async () => {
                        const confirmed =
                            window.confirm(
                                t("moderationConfirmRemove")
                                || "Are you sure you want to remove this content?"
                            );

                        if (!confirmed) {
                            return;
                        }

                        await submitModeration({
                            content_type: contentType,
                            object_id: item.id,
                            action: "remove",
                            reason: reason.value.trim()
                        });
                    }
                )
            );


            card.appendChild(actions);

            container.appendChild(card);
        });

    } catch (error) {
        console.error(
            "LOAD MODERATION CONTENT ERROR:",
            error
        );

        moderationMessage(
            t("moderationLoadFailed"),
            "error"
        );
    }
}


/*
 * Page initialization
 */
document.addEventListener(
    "DOMContentLoaded",
    () => {
        const user =
            typeof getStoredUser === "function"
                ? getStoredUser()
                : null;


        /*
         * Admin-only access
         */
        if (
            !user ||
            !(
                user.role === "Admin" ||
                user.is_staff === true ||
                user.is_superuser === true
            )
        ) {
            moderationMessage(
                t("adminAccessRequired"),
                "error"
            );

            return;
        }


        /*
         * Logout
         */
        document
            .getElementById("logoutButton")
            ?.addEventListener(
                "click",
                () => logout()
            );


        /*
         * Content type change
         */
        document
            .getElementById(
                "moderationContentType"
            )
            ?.addEventListener(
                "change",
                loadModerationContent
            );


        /*
         * Language change
         */
        document.addEventListener(
            "helpnet:languagechange",
            async () => {
                await loadModerationReports();
                await loadModerationContent();
            }
        );


        /*
         * Initial load
         */
        loadModerationReports();
        loadModerationContent();
    }
);
