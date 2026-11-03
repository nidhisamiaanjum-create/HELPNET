
document.addEventListener("DOMContentLoaded", function () {
    "use strict";

    /* =====================================================
       1. PROFILE MANAGEMENT
    ===================================================== */

    const profileTypes = {
        citizen: "Citizen",
        volunteer: "Volunteer",
        farmer: "Farmer",
        ngo: "NGO",
        blood_donor: "Blood Donor"
    };

    const profileList = document.getElementById("myProfilesList");
    const profileForm = document.getElementById("newProfileForm");
    const typeSelect = document.getElementById("newProfileType");
    const donorFields = document.getElementById("donorFields");
    const ngoFields = document.getElementById("ngoFields");
    const createProfileButton = document.getElementById("createProfileButton");
    const profileEditForm = document.getElementById("profileEditForm");
    const profileRoleFields = document.getElementById("profileRoleFields");
    const ngoVerificationSection = document.getElementById(
        "ngoVerificationSection"
    );
    const ngoVerificationForm = document.getElementById(
        "ngoVerificationForm"
    );

    function translate(key, fallback) {
        return typeof t === "function" ? t(key) : fallback;
    }

    const volunteerEditFields = [
        { name: "skills", key: "profileSkills", type: "textarea" },
        { name: "availability", key: "profileAvailability", type: "text" },
        { name: "location", key: "location", type: "text" },
        { name: "blood_group", key: "bloodGroup", type: "text" },
        { name: "supporting_certificates", key: "profileCertificates", type: "textarea" }
    ];

    function createProfileField(config, value) {
        const wrapper = document.createElement("div");
        wrapper.className = "field";
        const label = document.createElement("label");
        label.htmlFor = `profile-detail-${config.name}`;
        label.textContent = translate(config.key, config.key);
        label.dataset.i18n = config.key;
        const input = document.createElement(
            config.type === "textarea" ? "textarea" : "input"
        );
        input.id = label.htmlFor;
        input.name = config.name;
        input.dataset.profileDetail = config.name;
        input.value = value || "";
        if (config.type !== "textarea") {
            input.type = config.type;
            if (config.maxLength) input.maxLength = config.maxLength;
        } else {
            input.rows = 3;
        }
        wrapper.append(label, input);
        return wrapper;
    }

    function renderRoleEditFields(profile, details) {
        if (!profileRoleFields) return;
        profileRoleFields.replaceChildren();
        const config = profile.profile_type === "volunteer"
            ? volunteerEditFields
            : profile.profile_type === "blood_donor"
                ? [
                    { name: "blood_group", key: "bloodGroup", type: "select", values: ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"] },
                    { name: "area", key: "area", type: "text" },
                    {
                        name: "availability",
                        key: "donorAvailability",
                        type: "select",
                        values: [
                            { value: "available", key: "donorAvailable" },
                            { value: "busy", key: "donorBusy" },
                            { value: "not_available", key: "donorNotAvailable" }
                        ]
                    }
                ]
                : [];
        const fieldset = document.getElementById("profileRoleDetails");
        if (fieldset) fieldset.hidden = config.length === 0;

        config.forEach(function (field) {
            if (field.type !== "select") {
                profileRoleFields.appendChild(
                    createProfileField(field, details[field.name])
                );
                return;
            }

            const wrapper = document.createElement("div");
            wrapper.className = "field";
            const label = document.createElement("label");
            label.htmlFor = `profile-detail-${field.name}`;
            label.textContent = translate(field.key, field.key);
            label.dataset.i18n = field.key;
            const select = document.createElement("select");
            select.id = label.htmlFor;
            select.name = field.name;
            select.dataset.profileDetail = field.name;
            field.values.forEach(function (choice) {
                const option = document.createElement("option");
                const value = typeof choice === "string"
                    ? choice
                    : choice.value;
                option.value = value;
                option.textContent = typeof choice === "string"
                    ? value
                    : translate(choice.key, value);
                if (typeof choice !== "string") {
                    option.dataset.i18n = choice.key;
                }
                option.selected = value === details[field.name];
                select.appendChild(option);
            });
            wrapper.append(label, select);
            profileRoleFields.appendChild(wrapper);
        });
    }

    function getUser() {
        if (typeof getStoredUser === "function") {
            const stored = getStoredUser();
            if (stored) return stored;
        }

        try {
            return JSON.parse(localStorage.getItem("helpnet_user") || "null");
        } catch (error) {
            console.error("Could not read stored user:", error);
            return null;
        }
    }

    function saveUser(user) {
        localStorage.setItem("helpnet_user", JSON.stringify(user));
    }

    // Do not overwrite Admin's role when switching normal profiles.
    function isAdminUser(user) {
        return Boolean(
            user &&
            (
                user.is_superuser === true ||
                user.is_staff === true ||
                String(user.role || "").trim().toLowerCase() === "admin"
            )
        );
    }

    if (createProfileButton && profileForm) {
        createProfileButton.setAttribute("aria-expanded", "false");

        createProfileButton.addEventListener("click", function (event) {
            event.preventDefault();

            const opening = profileForm.hasAttribute("hidden");

            if (opening) {
                profileForm.removeAttribute("hidden");
            } else {
                profileForm.setAttribute("hidden", "");
            }

            createProfileButton.setAttribute(
                "aria-expanded",
                String(opening)
            );

            if (opening) {
                profileForm.scrollIntoView({
                    behavior: "smooth",
                    block: "center"
                });
                typeSelect?.focus();
            }
        });
    }

    typeSelect?.addEventListener("change", function () {
        if (donorFields) {
            donorFields.hidden = typeSelect.value !== "blood_donor";
        }
        if (ngoFields) {
            ngoFields.hidden = typeSelect.value !== "ngo";
        }
    });

    document.getElementById("cancelProfileEdit")?.addEventListener(
        "click",
        function () {
            profileEditForm.hidden = true;
            profileEditForm.reset();
            profileRoleFields?.replaceChildren();
        }
    );

    function renderNGOVerification(data) {
        const statusElement = document.getElementById("ngoVerificationStatus");
        const reasonElement = document.getElementById("ngoVerificationReason");
        const documentsElement = document.getElementById(
            "ngoVerificationDocuments"
        );
        if (!statusElement || !documentsElement || !ngoVerificationForm) return;

        const verificationStatus = data.ngo_verification_status ||
            "not_submitted";
        const statusKey = `ngoVerification_${verificationStatus}`;
        statusElement.textContent = translate(statusKey, verificationStatus);
        statusElement.dataset.i18n = statusKey;

        reasonElement.hidden = !data.ngo_verification_reason;
        reasonElement.textContent = data.ngo_verification_reason || "";
        documentsElement.replaceChildren();
        const documents = Array.isArray(data.documents) ? data.documents : [];
        documents.forEach(function (documentInfo) {
            const item = document.createElement("li");
            const link = document.createElement("a");
            link.href = documentInfo.download_url;
            link.textContent = documentInfo.name;
            link.addEventListener("click", async function (event) {
                event.preventDefault();
                try {
                    const response = await fetch(documentInfo.download_url, {
                        headers: {
                            Authorization: `Bearer ${getToken()}`
                        }
                    });
                    if (!response.ok) {
                        throw new Error(
                            `Document download failed (${response.status}).`
                        );
                    }
                    const objectUrl = URL.createObjectURL(
                        await response.blob()
                    );
                    const download = document.createElement("a");
                    download.href = objectUrl;
                    download.download = documentInfo.name;
                    document.body.appendChild(download);
                    download.click();
                    download.remove();
                    window.setTimeout(
                        () => URL.revokeObjectURL(objectUrl),
                        1000
                    );
                } catch (error) {
                    console.error("NGO document download failed:", error);
                    const message = document.getElementById(
                        "ngoVerificationFormMessage"
                    );
                    if (message) {
                        message.textContent =
                            error.message || "Could not download the document.";
                        message.classList.add("show");
                    }
                }
            });
            item.appendChild(link);
            documentsElement.appendChild(item);
        });

        const values = {
            ngoOrganizationName: data.display_name,
            ngoRegistrationNumber: data.ngo_registration_number,
            ngoOrganizationAddress: data.ngo_address,
            ngoContactEmail: data.ngo_contact_email,
            ngoContactPhone: data.ngo_contact_phone,
            ngoRepresentativeName: data.ngo_representative_name
        };
        Object.entries(values).forEach(function ([id, value]) {
            const input = document.getElementById(id);
            if (input && !input.value) input.value = value || "";
        });

        const canSubmit = [
            "not_submitted",
            "rejected",
            "additional_documents_required"
        ].includes(verificationStatus);
        ngoVerificationForm.dataset.verificationStatus = verificationStatus;
        ngoVerificationForm.hidden = !canSubmit;
        const formMessage = document.getElementById(
            "ngoVerificationFormMessage"
        );
        if (formMessage) {
            formMessage.textContent =
                verificationStatus === "additional_documents_required"
                    ? translate(
                        "ngoAdditionalDocumentUploadRequired",
                        "Upload at least one requested or replacement document."
                    )
                    : "";
            formMessage.classList.toggle(
                "show",
                Boolean(formMessage.textContent)
            );
        }
        const certificateInput = document.getElementById(
            "ngoRegistrationCertificate"
        );
        if (certificateInput) {
            certificateInput.required = !documents.some(function (document) {
                return document.document_type === "registration_certificate";
            });
        }
    }

    async function loadNGOVerification(activeProfile) {
        if (!ngoVerificationSection) return;
        ngoVerificationSection.hidden =
            !activeProfile || activeProfile.profile_type !== "ngo";
        if (ngoVerificationSection.hidden) return;

        const message = document.getElementById("ngoVerificationFormMessage");
        try {
            const result = await apiRequest(
                `/api/auth/profiles/${activeProfile.id}/ngo-verification/`
            );
            if (!result || result.success !== true || !result.data) {
                throw new Error("Could not load NGO verification details.");
            }
            renderNGOVerification(result.data);
        } catch (error) {
            console.error("NGO verification details could not be loaded:", error);
            if (message) {
                message.textContent =
                    error.message || "Could not load NGO verification details.";
                message.classList.add("show");
            }
        }
    }

    ngoVerificationForm?.addEventListener("submit", async function (event) {
        event.preventDefault();
        const message = document.getElementById("ngoVerificationFormMessage");
        const submitButton = ngoVerificationForm.querySelector(
            'button[type="submit"]'
        );
        if (submitButton) submitButton.disabled = true;
        if (message) {
            message.textContent = "";
            message.classList.remove("show");
        }

        try {
            const activeResult = await apiRequest("/api/auth/active-profile/");
            const activeProfile = activeResult?.data;
            if (!activeProfile || activeProfile.profile_type !== "ngo") {
                throw new Error(translate(
                    "ngoVerificationSelectProfile",
                    "Select your NGO profile before requesting verification."
                ));
            }

            const formData = new FormData(ngoVerificationForm);
            Array.from(formData.entries()).forEach(function ([name, value]) {
                if (value instanceof File && value.size === 0) {
                    formData.delete(name);
                }
            });
            if (
                ngoVerificationForm.dataset.verificationStatus ===
                    "additional_documents_required" &&
                !Array.from(formData.values()).some(function (value) {
                    return value instanceof File && value.size > 0;
                })
            ) {
                throw new Error(translate(
                    "ngoAdditionalDocumentUploadRequired",
                    "Upload at least one requested or replacement document."
                ));
            }
            const result = await apiRequest(
                `/api/auth/profiles/${activeProfile.id}/ngo-verification/`,
                "POST",
                formData
            );
            if (!result || result.success !== true || !result.data) {
                throw new Error("The server did not confirm the application.");
            }
            renderNGOVerification(result.data);
            if (message) {
                message.textContent = translate(
                    "ngoVerificationSubmitted",
                    "Verification application submitted."
                );
                message.classList.add("show");
            }
            await loadProfiles();
        } catch (error) {
            console.error("NGO verification submission failed:", error);
            if (message) {
                message.textContent =
                    error.message || translate(
                        "ngoVerificationSubmitFailed",
                        "Could not submit the verification application."
                    );
                message.classList.add("show");
            }
        } finally {
            if (submitButton) submitButton.disabled = false;
        }
    });

    async function loadProfiles() {
        if (
            !profileList ||
            typeof apiRequest !== "function" ||
            typeof getToken !== "function" ||
            !getToken()
        ) {
            return;
        }

        try {
            const [result, activeResult] = await Promise.all([
                apiRequest("/api/auth/profiles/"),
                apiRequest("/api/auth/active-profile/")
            ]);

            const profiles = Array.isArray(result?.data)
                ? result.data
                : Array.isArray(result)
                    ? result
                    : [];
            const active = activeResult?.data ?? null;

            profileList.replaceChildren();
            loadNGOVerification(active);
            const ngoNotice = document.getElementById("ngoApprovalNotice");
            const unapprovedNGOProfiles = profiles.filter(function (profile) {
                const verificationStatus = profile.ngo_verification_status ||
                    profile.ngo_approval_status;
                return (
                    profile.profile_type === "ngo" &&
                    verificationStatus !== "approved"
                );
            });
            const activeNGO = active?.profile_type === "ngo";
            const activeNGOStatus = activeNGO
                ? (active.ngo_verification_status || active.ngo_approval_status)
                : "";
            const pendingNGO =
                activeNGO && activeNGOStatus !== "approved";
            const rejectedNGO =
                activeNGO &&
                activeNGOStatus === "rejected";
            const additionalDocumentsNGO =
                activeNGO &&
                activeNGOStatus === "additional_documents_required";
            const notSubmittedNGO =
                activeNGO &&
                ["not_submitted", "not_required"].includes(activeNGOStatus);
            document.body.classList.toggle(
                "ngo-approval-pending",
                pendingNGO
            );
            if (ngoNotice) {
                ngoNotice.hidden = unapprovedNGOProfiles.length === 0;
                if (!ngoNotice.hidden) {
                    ngoNotice.textContent = unapprovedNGOProfiles.map(
                        function (profile) {
                            const statusKey =
                                `ngoVerification_${profile.ngo_verification_status || profile.ngo_approval_status}`;
                            const statusText = translate(
                                statusKey,
                                profile.ngo_verification_status || profile.ngo_approval_status
                            );
                            const profileName =
                                profile.display_name ||
                                translate("profileNGO", "NGO profile");
                            return `${profileName}: ${statusText}`;
                        }
                    ).join(" · ");
                    if (notSubmittedNGO) {
                        ngoNotice.textContent += ` — ${translate(
                            "ngoVerificationNotSubmittedNotice",
                            "Submit organization information and documents to request verification."
                        )}`;
                    } else if (rejectedNGO) {
                        ngoNotice.textContent += ` — ${translate(
                            "ngoApprovalRejectedNotice",
                            "Contact an administrator for more information."
                        )}`;
                    } else if (additionalDocumentsNGO) {
                        ngoNotice.textContent += ` — ${translate(
                            "ngoAdditionalDocumentsNotice",
                            "Submit the additional documents requested by the administrator."
                        )}`;
                    } else if (pendingNGO) {
                        ngoNotice.textContent += ` — ${translate(
                            "ngoApprovalPendingNotice",
                            "NGO coordinator features are not available until approval."
                        )}`;
                    }
                }
            }
            if (pendingNGO) {
                const titleKey = rejectedNGO
                    ? "ngoApprovalRejectedTitle"
                    : additionalDocumentsNGO
                        ? "ngoAdditionalDocumentsTitle"
                        : notSubmittedNGO
                            ? "ngoVerificationNotSubmittedTitle"
                            : "ngoApprovalPendingTitle";
                const descriptionKey = rejectedNGO
                    ? "ngoApprovalRejectedDescription"
                    : additionalDocumentsNGO
                        ? "ngoAdditionalDocumentsDescription"
                        : notSubmittedNGO
                            ? "ngoVerificationNotSubmittedDescription"
                            : "ngoApprovalPendingDescription";
                const pendingTitle = translate(
                    titleKey,
                    rejectedNGO ? "NGO application not approved" : "NGO approval pending"
                );
                const pendingDescription = translate(
                    descriptionKey,
                    rejectedNGO
                        ? "Contact an administrator for information about your application."
                        : "An administrator is reviewing your application."
                );
                const roleTitle = document.getElementById("roleSectionTitle");
                const roleDescription = document.getElementById(
                    "roleSectionDescription"
                );
                if (roleTitle) roleTitle.textContent = pendingTitle;
                if (roleDescription) {
                    roleDescription.textContent = pendingDescription;
                }
                const dashboardTitle = document.getElementById(
                    "dashboardRoleTitle"
                );
                if (dashboardTitle) {
                    dashboardTitle.textContent = pendingTitle;
                    dashboardTitle.dataset.i18n = titleKey;
                }
                if (roleTitle) {
                    roleTitle.dataset.i18n = titleKey;
                }
                if (roleDescription) {
                    roleDescription.dataset.i18n = descriptionKey;
                }
            }

            if (typeSelect) {
                const ownedTypes = new Set(
                    profiles.map(function (profile) {
                        return profile.profile_type;
                    })
                );

                Array.from(typeSelect.options).forEach(function (option) {
                    if (!option.value) {
                        option.hidden = false;
                        option.disabled = false;
                        return;
                    }

                    const unavailable = ownedTypes.has(option.value);

                    option.hidden = unavailable;
                    option.disabled = unavailable;
                });

                if (
                    typeSelect.value &&
                    typeSelect.options[typeSelect.selectedIndex]?.disabled
                ) {
                    typeSelect.value = "";
                }

                if (donorFields) {
                    donorFields.hidden = typeSelect.value !== "blood_donor";
                }
                if (ngoFields) {
                    ngoFields.hidden = typeSelect.value !== "ngo";
                }
            }

            profiles.forEach(function (profile) {
                const card = document.createElement("div");
                card.className = "card";

                const title = document.createElement("strong");
                title.textContent =
                    profile.display_name ||
                    profileTypes[profile.profile_type] ||
                    profile.profile_type;

                const status = document.createElement("span");
                status.textContent =
                    profile.id === active?.id
                        ? ` · ${translate("currentProfile", "Current profile")}`
                        : ` · ${translate(profile.status === "active" ? "profileActive" : "profileInactive", profile.status)}`;
                if (
                    profile.profile_type === "ngo" &&
                    (profile.ngo_verification_status ||
                        profile.ngo_approval_status) !== "approved"
                ) {
                    status.textContent += ` · ${translate(
                        `ngoVerification_${profile.ngo_verification_status || profile.ngo_approval_status}`,
                        profile.ngo_verification_status ||
                            profile.ngo_approval_status
                    )}`;
                }

                card.append(title, status);

                const edit = document.createElement("button");
                edit.type = "button";
                edit.className = "btn";
                edit.textContent = translate("editProfile", "Edit profile");

                edit.addEventListener("click", async function () {
                    try {
                        const result = await apiRequest(
                            `/api/auth/profiles/${profile.id}/`
                        );
                        const current = result?.data || profile;
                        document.getElementById("editProfileId").value = current.id;
                        document.getElementById("editProfileDisplayName").value =
                            current.display_name || "";
                        renderRoleEditFields(current, current.details || {});
                        profileEditForm.hidden = false;
                        profileEditForm.scrollIntoView({
                            behavior: "smooth",
                            block: "center"
                        });
                    } catch (error) {
                        alert(error.message || translate(
                            "profileLoadFailed",
                            "Could not load profile."
                        ));
                    }
                });

                card.append(edit);

                if (profile.status === "active") {
                    const deactivate = document.createElement("button");
                    deactivate.type = "button";
                    deactivate.className = "btn btn-danger";
                    deactivate.textContent = translate(
                        "deactivateProfile",
                        "Deactivate / delete profile"
                    );

                    deactivate.addEventListener(
                        "click",
                        async function () {
                            if (!confirm(
                                translate(
                                    "deactivateProfileConfirm",
                                    "Deactivate this profile? Its related records will be retained, and you can reactivate it later."
                                )
                            )) {
                                return;
                            }

                            try {
                                await apiRequest(
                                    `/api/auth/profiles/${profile.id}/`,
                                    "DELETE"
                                );
                                if (profile.id === active?.id) {
                                    window.location.reload();
                                    return;
                                }
                                await loadProfiles();
                            } catch (error) {
                                alert(
                                    error.message ||
                                    translate("profileDeactivateFailed", "Could not deactivate profile.")
                                );
                            }
                        }
                    );

                    card.append(deactivate);
                } else {
                    const reactivate = document.createElement("button");
                    reactivate.type = "button";
                    reactivate.className = "btn";
                    reactivate.textContent = translate(
                        "reactivateProfile",
                        "Reactivate profile"
                    );
                    reactivate.addEventListener("click", async function () {
                        try {
                            await apiRequest(
                                `/api/auth/profiles/${profile.id}/reactivate/`,
                                "POST"
                            );
                            await loadProfiles();
                        } catch (error) {
                            alert(error.message || translate(
                                "profileReactivateFailed",
                                "Could not reactivate profile."
                            ));
                        }
                    });
                    card.append(reactivate);
                }

                if (
                    profile.status === "active" &&
                    profile.id !== active?.id
                ) {
                    const switchButton =
                        document.createElement("button");

                    switchButton.type = "button";
                    switchButton.className = "btn";
                    switchButton.textContent = translate(
                        "switchProfile",
                        "Switch profile"
                    );

                    switchButton.addEventListener(
                        "click",
                        async function () {
                            try {
                                await apiRequest(
                                    "/api/auth/active-profile/",
                                    "PUT",
                                    { profile_id: profile.id }
                                );

                                let user = getUser();

                                try {
                                    const token = localStorage.getItem("helpnet_token");

                                    if (token) {
                                        const response = await fetch("/api/auth/me/", {
                                            headers: {
                                                Authorization: `Bearer ${token}`
                                            }
                                        });

                                        if (response.ok) {
                                            const result = await response.json();

                                            if (result.success && result.data) {
                                                user = {
                                                    ...(user || {}),
                                                    ...result.data
                                                };

                                                localStorage.setItem(
                                                    "helpnet_user",
                                                    JSON.stringify(user)
                                                );
                                            }
                                        } else {
                                            console.error(
                                                "Failed to refresh user:",
                                                response.status
                                            );
                                        }
                                    }
                                } catch (error) {
                                    console.error("Could not refresh user data:", error);
                                }

                                // Keep Django admin permissions intact.
                                if (user && !isAdminUser(user)) {
                                    user.role =
                                        profileTypes[profile.profile_type] ||
                                        profile.profile_type;

                                    saveUser(user);
                                }

                                location.reload();
                            } catch (error) {
                                alert(
                                    error.message ||
                                    "Could not switch profile."
                                );
                            }
                        }
                    );

                    card.append(switchButton);
                }

                profileList.append(card);
            });

            // Update ordinary users' active profile only.
            const user = getUser();

            if (active && user && !isAdminUser(user)) {
                const activeRole = profileTypes[active.profile_type];

                if (activeRole && user.role !== activeRole) {
                    user.role = activeRole;
                    saveUser(user);
                }
            }
        } catch (error) {
            profileList.textContent =
                error.message || "Could not load profiles.";
        }
    }

    profileEditForm?.addEventListener("submit", async function (event) {
        event.preventDefault();
        const errorBox = document.getElementById("profileEditError");
        errorBox.textContent = "";
        const profileId = document.getElementById("editProfileId").value;
        const details = {};
        profileRoleFields?.querySelectorAll("[data-profile-detail]").forEach(
            function (input) {
                details[input.dataset.profileDetail] = input.value.trim();
            }
        );
        const submitButton = profileEditForm.querySelector(
            'button[type="submit"]'
        );
        submitButton.disabled = true;
        try {
            await apiRequest(
                `/api/auth/profiles/${encodeURIComponent(profileId)}/`,
                "PATCH",
                {
                    display_name: document
                        .getElementById("editProfileDisplayName")
                        .value.trim(),
                    details
                }
            );
            profileEditForm.hidden = true;
            profileEditForm.reset();
            await loadProfiles();
        } catch (error) {
            errorBox.textContent = error.message || translate(
                "profileSaveFailed",
                "Could not save profile changes."
            );
        } finally {
            submitButton.disabled = false;
        }
    });

    document.addEventListener("helpnet:languagechange", loadProfiles);

    profileForm?.addEventListener("submit", async function (event) {
        event.preventDefault();

        const errorBox =
            document.getElementById("profileFormError");

        if (errorBox) errorBox.textContent = "";

        const user = getUser();

        if (isAdminUser(user)) {
            if (errorBox) {
                errorBox.textContent =
                    "Admin accounts cannot change their role through profiles.";
            }
            return;
        }

        if (!typeSelect?.value) {
            if (errorBox) {
                errorBox.textContent = "Choose a profile type.";
            }
            return;
        }

        const details =
            typeSelect.value === "blood_donor"
                ? {
                    blood_group:
                        document.getElementById("donorGroup")?.value.trim(),
                    area:
                        document.getElementById("donorArea")?.value.trim()
                }
                : {};

        if (
            typeSelect.value === "blood_donor" &&
            (!details.blood_group || !details.area)
        ) {
            if (errorBox) {
                errorBox.textContent =
                    "Blood group and area are required for a Blood Donor profile.";
            }
            return;
        }

        try {
            const payload = {
                profile_type: typeSelect.value,
                details
            };
            if (typeSelect.value === "ngo") {
                payload.display_name = document
                    .getElementById("ngoDisplayName")
                    .value.trim();
                if (!payload.display_name) {
                    if (errorBox) {
                        errorBox.textContent = translate(
                            "organizationNameRequired",
                            "Enter the organization/profile name."
                        );
                    }
                    return;
                }
            }
            const response = await apiRequest(
                "/api/auth/profiles/",
                "POST",
                payload
            );

            await apiRequest(
                "/api/auth/active-profile/",
                "PUT",
                { profile_id: response.data.id }
            );

            const updatedUser = getUser();

            if (updatedUser && !isAdminUser(updatedUser)) {
                updatedUser.role =
                    profileTypes[response.data.profile_type] ||
                    response.data.profile_type;

                saveUser(updatedUser);
            }

            location.reload();
        } catch (error) {
            if (errorBox) {
                errorBox.textContent =
                    error.message || "Could not create profile.";
            }
        }
    });

    /* =====================================================
       2. LOGIN CHECK
    ===================================================== */

    if (
        typeof requireLogin === "function" &&
        !requireLogin()
    ) {
        return;
    }

    const user = getUser();

    if (!user) {
        console.warn("HELPNET Dashboard: no stored user found.");
        return;
    }

    /* =====================================================
       3. IDENTIFY USER AND ADMIN
    ===================================================== */

    const userId =
        user.user_id || user.id || user.pk || "";

    const displayName =
        user.full_name ||
        user.name ||
        user.username ||
        "HELPNET User";

    const normalizedRole = String(user.role || "")
        .trim()
        .toLowerCase()
        .replace(/[\s-]+/g, "_");

    // Declare isAdmin only once in this function.
    const isAdmin = isAdminUser(user);

    const role = isAdmin ? "admin" : normalizedRole;

    console.log("HELPNET DASHBOARD USER:", user);
    console.log("HELPNET DASHBOARD ROLE:", role);
    console.log("HELPNET ADMIN STATUS:", isAdmin);
    console.log("HELPNET DASHBOARD USER ID:", userId);

    /* =====================================================
       4. ADMIN REDIRECT
    ===================================================== */

    if (
        isAdmin &&
        window.location.pathname === "/dashboard/"
    ) {
        window.location.replace("/admin-dashboard/");
        return;
    }

    /* =====================================================
       5. ROLE CONFIGURATION
    ===================================================== */

    const roleInfo = {
        citizen: {
            titleKey: "dashboardCitizenTitle",
            descriptionKey: "dashboardCitizenDescription",
            activityTitleKey: "dashboardCitizenActivities",
            title: "Citizen Dashboard",
            description:
                "Access community services, share unused goods, manage waste requests and get help from the community.",
            activityTitle: "Citizen Activities",
            activities: [
                {
                    icon: "♻️",
                    titleKey: "dashboardGoodsExchange",
                    textKey: "dashboardGoodsExchangeDescription",
                    title: "Goods Exchange",
                    text: "Share or claim unused goods."
                },
                {
                    icon: "🩸",
                    titleKey: "dashboardBloodSupport",
                    textKey: "dashboardBloodSupportCitizenDescription",
                    title: "Blood Support",
                    text: "Create or respond to blood-related requests."
                },
                {
                    icon: "🗑️",
                    titleKey: "dashboardWasteManagement",
                    textKey: "dashboardWasteManagementDescription",
                    title: "Waste Management",
                    text: "Manage your waste pickup requests."
                }
            ]
        },

        volunteer: {
            titleKey: "dashboardVolunteerTitle",
            descriptionKey: "dashboardVolunteerDescription",
            activityTitleKey: "dashboardVolunteerActivities",
            title: "Volunteer Dashboard",
            description:
                "Find community events, join volunteer activities and help people through HELPNET.",
            activityTitle: "Volunteer Activities",
            activities: [
                {
                    icon: "🤝",
                    titleKey: "dashboardVolunteerEvents",
                    textKey: "dashboardVolunteerEventsDescription",
                    title: "Volunteer Events",
                    text: "Browse and register for community events."
                },
                {
                    icon: "🩸",
                    titleKey: "dashboardBloodSupport",
                    textKey: "dashboardBloodSupportVolunteerDescription",
                    title: "Blood Support",
                    text: "Help people with blood-related needs."
                },
                {
                    icon: "❤️",
                    titleKey: "dashboardCommunityHelp",
                    textKey: "dashboardCommunityHelpVolunteerDescription",
                    title: "Community Help",
                    text: "Take part in activities that support your community."
                }
            ]
        },

        ngo: {
            titleKey: "dashboardNGOTitle",
            descriptionKey: "dashboardNGODescription",
            activityTitleKey: "dashboardNGOActivities",
            title: "NGO Dashboard",
            description:
                "Organize community activities, manage volunteer events and work with verification services.",
            activityTitle: "NGO Activities",
            activities: [
                {
                    icon: "🤝",
                    titleKey: "dashboardCommunityEvents",
                    textKey: "dashboardCommunityEventsDescription",
                    title: "Community Events",
                    text: "Create and manage volunteer and community events."
                },
                {
                    icon: "🛡️",
                    titleKey: "dashboardVerification",
                    textKey: "dashboardVerificationDescription",
                    title: "Verification",
                    text: "Review available verification requests."
                },
                {
                    icon: "❤️",
                    titleKey: "dashboardCommunitySupport",
                    textKey: "dashboardCommunitySupportNGODescription",
                    title: "Community Support",
                    text: "Support people and community activities."
                }
            ]
        },

        farmer: {
            titleKey: "dashboardFarmerTitle",
            descriptionKey: "dashboardFarmerDescription",
            activityTitleKey: "dashboardFarmerActivities",
            title: "Farmer Dashboard",
            description:
                "Manage your farmer marketplace activities and connect with people looking for local products.",
            activityTitle: "Farmer Activities",
            activities: [
                {
                    icon: "🌾",
                    titleKey: "dashboardFarmerMarket",
                    textKey: "dashboardFarmerMarketDescription",
                    title: "Farmer Market",
                    text: "View and manage farmer marketplace activities."
                },
                {
                    icon: "📦",
                    titleKey: "dashboardProductListings",
                    textKey: "dashboardProductListingsDescription",
                    title: "Product Listings",
                    text: "Manage your available agricultural products."
                },
                {
                    icon: "❤️",
                    titleKey: "dashboardCommunitySupport",
                    textKey: "dashboardCommunitySupportFarmerDescription",
                    title: "Community Support",
                    text: "Connect with the HELPNET community."
                }
            ]
        },

        blood_donor: {
            titleKey: "dashboardBloodDonorTitle",
            descriptionKey: "dashboardBloodDonorDescription",
            activityTitleKey: "dashboardBloodDonationActivities",
            title: "Blood Donor",
            description:
                "Help save lives by donating blood and responding to blood requests.",
            activityTitle: "Blood Donation Activity",
            activities: [
                {
                    icon: "🩸",
                    titleKey: "dashboardBloodDonation",
                    textKey: "dashboardBloodDonationDescription",
                    title: "Blood Donation",
                    text: "Manage your donor profile and help people who need blood."
                },
                {
                    icon: "🔎",
                    titleKey: "dashboardBloodRequests",
                    textKey: "dashboardBloodRequestsDescription",
                    title: "Blood Requests",
                    text: "View blood-related requests and respond when you are available."
                },
                {
                    icon: "❤️",
                    titleKey: "dashboardCommunitySupport",
                    textKey: "dashboardCommunitySupportDonorDescription",
                    title: "Community Support",
                    text: "Help save lives through blood donation."
                }
            ]
        },

        admin: {
            titleKey: "dashboardAdminTitle",
            descriptionKey: "dashboardAdminDescription",
            activityTitleKey: "dashboardAdminActivities",
            title: "Admin Dashboard",
            description:
                "Manage verification, review system activity and access administrative tools.",
            activityTitle: "Administrative Activities",
            activities: [
                {
                    icon: "📋",
                    titleKey: "dashboardReviewQueue",
                    textKey: "dashboardReviewQueueDescription",
                    title: "Review Queue",
                    text: "Review pending system requests."
                },
                {
                    icon: "📜",
                    titleKey: "dashboardActionLog",
                    textKey: "dashboardActionLogDescription",
                    title: "Action Log",
                    text: "View recorded administrative actions."
                },
                {
                    icon: "📊",
                    titleKey: "dashboardReports",
                    textKey: "dashboardReportsDescription",
                    title: "Reports",
                    text: "Access administrative reports."
                }
            ]
        }
    };

    if (!roleInfo[role]) {
        console.error(
            "HELPNET Dashboard: unknown user role:",
            user.role
        );
        loadProfiles();
        return;
    }

    const currentRole = roleInfo[role];

    /* =====================================================
       6. WELCOME NAME AND ROLE
    ===================================================== */

    const welcomeName = document.getElementById("welcomeName");

    if (welcomeName) {
        welcomeName.textContent = displayName + " 👋";
    }

    const dashboardRoleTitle =
        document.getElementById("dashboardRoleTitle");

    if (dashboardRoleTitle) {
        dashboardRoleTitle.textContent = translate(
            currentRole.titleKey,
            currentRole.title
        );
        dashboardRoleTitle.dataset.i18n = currentRole.titleKey;
    }

    const roleSectionTitle =
        document.getElementById("roleSectionTitle");

    if (roleSectionTitle) {
        roleSectionTitle.textContent = translate(
            currentRole.titleKey,
            currentRole.title
        );
        roleSectionTitle.dataset.i18n = currentRole.titleKey;
    }

    const roleSectionDescription =
        document.getElementById("roleSectionDescription");

    if (roleSectionDescription) {
        roleSectionDescription.textContent =
            translate(
                currentRole.descriptionKey,
                currentRole.description
            );
        roleSectionDescription.dataset.i18n =
            currentRole.descriptionKey;
    }

    const userEmail = document.getElementById("userEmail");

    if (userEmail) {
        userEmail.textContent =
            user.email || user.phone_number || user.phone || "-";
    }

    /* =====================================================
       7. TRUST BLOCK
    ===================================================== */

    const trustHost = document.getElementById("dashboardTrust");

    if (trustHost) {
        trustHost.dataset.userId = userId;

        if (typeof window.loadTrustBlock === "function") {
            window.loadTrustBlock(trustHost);
        }
    }

    /* =====================================================
       8. VERIFICATION CALLOUT
    ===================================================== */

    const verifyCallout =
        document.getElementById("verifyCallout");

    if (verifyCallout) {
        const verificationStatus = String(
            user.verification_status ||
            user.nid_status ||
            "unverified"
        ).toLowerCase().trim();

        verifyCallout.hidden =
            verificationStatus === "approved";
    }

    /* =====================================================
       9. ADMIN SECTION
    ===================================================== */

    const adminSection =
        document.getElementById("adminSection");

    if (adminSection) {
        adminSection.hidden = !isAdmin;
    }

    /* =====================================================
       10. ROLE-BASED SERVICE CARDS
    ===================================================== */

    const serviceCards =
        document.querySelectorAll(".role-service");

    serviceCards.forEach(function (card) {
        const allowedRoles = String(card.dataset.roles || "")
            .toLowerCase()
            .split(/\s+/)
            .filter(Boolean);

        card.hidden = !allowedRoles.includes(role);
    });

    /* =====================================================
       11. ROLE ACTIVITIES
    ===================================================== */

    const roleActivityList =
        document.getElementById("roleActivityList");

    if (roleActivityList) {
        roleActivityList.replaceChildren();

        currentRole.activities.forEach(function (activity) {
            const card = document.createElement("div");
            card.className = "activity-card";

            const icon = document.createElement("div");
            icon.className = "activity-icon";
            icon.textContent = activity.icon;

            const content = document.createElement("div");
            content.className = "activity-content";

            const title = document.createElement("strong");
            title.textContent = translate(
                activity.titleKey,
                activity.title
            );
            title.dataset.i18n = activity.titleKey;

            const description = document.createElement("p");
            description.textContent = translate(
                activity.textKey,
                activity.text
            );
            description.dataset.i18n = activity.textKey;

            content.append(title, description);
            card.append(icon, content);
            roleActivityList.append(card);
        });
    }

    const activitySectionTitle =
        document.getElementById("activitySectionTitle");

    if (activitySectionTitle) {
        activitySectionTitle.textContent =
            translate(
                currentRole.activityTitleKey,
                currentRole.activityTitle
            );
        activitySectionTitle.dataset.i18n =
            currentRole.activityTitleKey;
    }

    console.log(
        "HELPNET Dashboard successfully initialized for:",
        role
    );

    /* =====================================================
       12. LOAD PROFILES
    ===================================================== */

    loadProfiles();
});

/* =====================================================
   13. FIND PEOPLE
===================================================== */

const peopleSearchForm =
    document.getElementById("peopleSearchForm");

const peopleSearchInput =
    document.getElementById("peopleSearchInput");

if (peopleSearchForm && peopleSearchInput) {
    peopleSearchForm.addEventListener("submit", function (event) {
        event.preventDefault();

        const query = peopleSearchInput.value.trim();

        if (!query) {
            peopleSearchInput.focus();
            return;
        }

        window.location.href =
            "/user-search/?q=" + encodeURIComponent(query);
    });
}
