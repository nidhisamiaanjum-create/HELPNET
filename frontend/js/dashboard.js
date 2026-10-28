
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
    const createProfileButton = document.getElementById("createProfileButton");

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

                    // NGO is registration-only; each other type can be created once.
                    const unavailable =
                        option.value === "ngo" ||
                        ownedTypes.has(option.value);

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
                        ? " · Current profile"
                        : ` · ${profile.status}`;

                card.append(title, status);

                const edit = document.createElement("button");
                edit.type = "button";
                edit.className = "btn";
                edit.textContent = "Edit profile";

                edit.addEventListener("click", async function () {
                    try {
                        const name = prompt(
                            "Profile display name",
                            profile.display_name || ""
                        );

                        if (name === null) return;

                        await apiRequest(
                            `/api/auth/profiles/${profile.id}/`,
                            "PATCH",
                            { display_name: name }
                        );

                        if (profile.profile_type === "volunteer") {
                            const current =
                                (await apiRequest(
                                    "/api/volunteer/profile/"
                                )).data || {};

                            const skills = prompt(
                                "Volunteer skills",
                                current.skills || ""
                            );

                            if (skills !== null) {
                                await apiRequest(
                                    "/api/volunteer/profile/",
                                    "PUT",
                                    {
                                        skills,
                                        availability:
                                            current.availability || "",
                                        location: current.location || ""
                                    }
                                );
                            }
                        }

                        if (profile.profile_type === "blood_donor") {
                            const current =
                                (await apiRequest(
                                    "/api/blood/donor-profile/"
                                )).data || {};

                            const blood_group = prompt(
                                "Blood group",
                                current.blood_group || ""
                            );

                            if (blood_group !== null) {
                                const area = prompt(
                                    "Area",
                                    current.area || ""
                                );

                                if (area !== null) {
                                    await apiRequest(
                                        "/api/blood/donor-profile/",
                                        "PUT",
                                        {
                                            blood_group,
                                            area,
                                            availability:
                                                current.availability ||
                                                "available"
                                        }
                                    );
                                }
                            }
                        }

                        location.reload();
                    } catch (error) {
                        alert(
                            error.message ||
                            "Could not update profile."
                        );
                    }
                });

                card.append(edit);

                if (profile.status === "active") {
                    const deactivate = document.createElement("button");
                    deactivate.type = "button";
                    deactivate.className = "btn";
                    deactivate.textContent = "Deactivate";

                    deactivate.addEventListener(
                        "click",
                        async function () {
                            if (!confirm(
                                "Deactivate this profile? Its related records will be retained."
                            )) {
                                return;
                            }

                            try {
                                await apiRequest(
                                    `/api/auth/profiles/${profile.id}/`,
                                    "DELETE"
                                );
                                await loadProfiles();
                            } catch (error) {
                                alert(
                                    error.message ||
                                    "Could not deactivate profile."
                                );
                            }
                        }
                    );

                    card.append(deactivate);
                }

                if (
                    profile.status === "active" &&
                    profile.id !== active?.id
                ) {
                    const switchButton =
                        document.createElement("button");

                    switchButton.type = "button";
                    switchButton.className = "btn";
                    switchButton.textContent = "Switch Profile";

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

        if (typeSelect.value === "ngo") {
            if (errorBox) {
                errorBox.textContent =
                    "NGO profiles can only be created during registration.";
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
            const response = await apiRequest(
                "/api/auth/profiles/",
                "POST",
                {
                    profile_type: typeSelect.value,
                    details
                }
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
            title: "Citizen Dashboard",
            description:
                "Access community services, share unused goods, manage waste requests and get help from the community.",
            activityTitle: "Citizen Activities",
            activities: [
                {
                    icon: "♻️",
                    title: "Goods Exchange",
                    text: "Share or claim unused goods."
                },
                {
                    icon: "🩸",
                    title: "Blood Support",
                    text: "Create or respond to blood-related requests."
                },
                {
                    icon: "🗑️",
                    title: "Waste Management",
                    text: "Manage your waste pickup requests."
                }
            ]
        },

        volunteer: {
            title: "Volunteer Dashboard",
            description:
                "Find community events, join volunteer activities and help people through HELPNET.",
            activityTitle: "Volunteer Activities",
            activities: [
                {
                    icon: "🤝",
                    title: "Volunteer Events",
                    text: "Browse and register for community events."
                },
                {
                    icon: "🩸",
                    title: "Blood Support",
                    text: "Help people with blood-related needs."
                },
                {
                    icon: "❤️",
                    title: "Community Help",
                    text: "Take part in activities that support your community."
                }
            ]
        },

        ngo: {
            title: "NGO Dashboard",
            description:
                "Organize community activities, manage volunteer events and work with verification services.",
            activityTitle: "NGO Activities",
            activities: [
                {
                    icon: "🤝",
                    title: "Community Events",
                    text: "Create and manage volunteer and community events."
                },
                {
                    icon: "🛡️",
                    title: "Verification",
                    text: "Review available verification requests."
                },
                {
                    icon: "❤️",
                    title: "Community Support",
                    text: "Support people and community activities."
                }
            ]
        },

        farmer: {
            title: "Farmer Dashboard",
            description:
                "Manage your farmer marketplace activities and connect with people looking for local products.",
            activityTitle: "Farmer Activities",
            activities: [
                {
                    icon: "🌾",
                    title: "Farmer Market",
                    text: "View and manage farmer marketplace activities."
                },
                {
                    icon: "📦",
                    title: "Product Listings",
                    text: "Manage your available agricultural products."
                },
                {
                    icon: "❤️",
                    title: "Community Support",
                    text: "Connect with the HELPNET community."
                }
            ]
        },

        blood_donor: {
            title: "Blood Donor",
            description:
                "Help save lives by donating blood and responding to blood requests.",
            activityTitle: "Blood Donation Activity",
            activities: [
                {
                    icon: "🩸",
                    title: "Blood Donation",
                    text: "Manage your donor profile and help people who need blood."
                },
                {
                    icon: "🔎",
                    title: "Blood Requests",
                    text: "View blood-related requests and respond when you are available."
                },
                {
                    icon: "❤️",
                    title: "Community Support",
                    text: "Help save lives through blood donation."
                }
            ]
        },

        admin: {
            title: "Admin Dashboard",
            description:
                "Manage verification, review system activity and access administrative tools.",
            activityTitle: "Administrative Activities",
            activities: [
                {
                    icon: "📋",
                    title: "Review Queue",
                    text: "Review pending system requests."
                },
                {
                    icon: "📜",
                    title: "Action Log",
                    text: "View recorded administrative actions."
                },
                {
                    icon: "📊",
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
        dashboardRoleTitle.textContent = currentRole.title;
    }

    const roleSectionTitle =
        document.getElementById("roleSectionTitle");

    if (roleSectionTitle) {
        roleSectionTitle.textContent = currentRole.title;
    }

    const roleSectionDescription =
        document.getElementById("roleSectionDescription");

    if (roleSectionDescription) {
        roleSectionDescription.textContent =
            currentRole.description;
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
            title.textContent = activity.title;

            const description = document.createElement("p");
            description.textContent = activity.text;

            content.append(title, description);
            card.append(icon, content);
            roleActivityList.append(card);
        });
    }

    const activitySectionTitle =
        document.getElementById("activitySectionTitle");

    if (activitySectionTitle) {
        activitySectionTitle.textContent =
            currentRole.activityTitle;
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
