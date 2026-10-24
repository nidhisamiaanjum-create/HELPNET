document.addEventListener("DOMContentLoaded", function () {

    const profileTypes = {citizen:"Citizen", volunteer:"Volunteer", farmer:"Farmer", ngo:"NGO", blood_donor:"Blood Donor"};
    const profileList = document.getElementById("myProfilesList");
    const profileForm = document.getElementById("newProfileForm");
    const typeSelect = document.getElementById("newProfileType");
    const donorFields = document.getElementById("donorFields");
    const createProfileButton = document.getElementById("createProfileButton");
    if (createProfileButton && profileForm) {
        createProfileButton.setAttribute("aria-expanded", "false");
        createProfileButton.addEventListener("click", event => {
            event.preventDefault();
            const opening = profileForm.hasAttribute("hidden");
            if (opening) profileForm.removeAttribute("hidden");
            else profileForm.setAttribute("hidden", "");
            createProfileButton.setAttribute("aria-expanded", String(opening));
            if (opening) {
                profileForm.scrollIntoView({behavior: "smooth", block: "center"});
                typeSelect?.focus();
            }
        });
    }
    typeSelect?.addEventListener("change", () => { donorFields.hidden = typeSelect.value !== "blood_donor"; });
    async function loadProfiles() {
        if (!profileList || typeof apiRequest !== "function" || !getToken()) return;
        try {
            const [result, activeResult] = await Promise.all([apiRequest("/api/auth/profiles/"), apiRequest("/api/auth/active-profile/")]);
            const profiles = result.data || [];
            const active = activeResult.data;
            profileList.replaceChildren();
            profiles.forEach(profile => {
                const card = document.createElement("div"); card.className = "card";
                const title = document.createElement("strong"); title.textContent = profile.display_name || profileTypes[profile.profile_type] || profile.profile_type;
                const status = document.createElement("span"); status.textContent = profile.id === active?.id ? " · Current profile" : ` · ${profile.status}`;
                card.append(title, status);
                const edit = document.createElement("button"); edit.type = "button"; edit.className = "btn"; edit.textContent = "Edit profile";
                edit.addEventListener("click", async () => { try {
                    await apiRequest("/api/auth/active-profile/", "PUT", {profile_id: profile.id}); const owner = getStoredUser() || {}; owner.role = profileTypes[profile.profile_type]; localStorage.setItem("helpnet_user", JSON.stringify(owner));
                    const name = prompt("Profile display name", profile.display_name || ""); if (name === null) return;
                    await apiRequest(`/api/auth/profiles/${profile.id}/`, "PATCH", {display_name: name});
                    if (profile.profile_type === "volunteer") { const current = (await apiRequest("/api/volunteer/profile/")).data || {}; const skills = prompt("Volunteer skills", current.skills || ""); if (skills !== null) await apiRequest("/api/volunteer/profile/", "PUT", {skills, availability: current.availability || "", location: current.location || ""}); }
                    if (profile.profile_type === "blood_donor") { const current = (await apiRequest("/api/blood/donor-profile/")).data || {}; const blood_group = prompt("Blood group", current.blood_group || ""); if (blood_group !== null) { const area = prompt("Area", current.area || ""); if (area !== null) await apiRequest("/api/blood/donor-profile/", "PUT", {blood_group, area, availability: current.availability || "available"}); } }
                    location.reload();
                } catch (error) { alert(error.message || "Could not update profile."); } }); card.append(edit);
                if (profile.status === "active") { const deactivate = document.createElement("button"); deactivate.type = "button"; deactivate.className = "btn"; deactivate.textContent = "Deactivate"; deactivate.addEventListener("click", async () => { if (!confirm("Deactivate this profile? Its related records will be retained.")) return; try { await apiRequest(`/api/auth/profiles/${profile.id}/`, "DELETE"); loadProfiles(); } catch (error) { alert(error.message || "Could not deactivate profile."); } }); card.append(deactivate); }
                if (profile.status === "active" && profile.id !== active?.id) {
                    const button = document.createElement("button"); button.type = "button"; button.className = "btn"; button.textContent = "Switch Profile";
                    button.addEventListener("click", async () => { await apiRequest("/api/auth/active-profile/", "PUT", {profile_id: profile.id}); const user = getStoredUser() || {}; user.role = profileTypes[profile.profile_type]; localStorage.setItem("helpnet_user", JSON.stringify(user)); location.reload(); }); card.append(button);
                }
                profileList.append(card);
            });
            if (active) { const user = getStoredUser() || {}; const role = profileTypes[active.profile_type]; if (role && user.role !== role) { user.role = role; localStorage.setItem("helpnet_user", JSON.stringify(user)); } }
        } catch (error) { profileList.textContent = error.message || "Could not load profiles."; }
    }
    profileForm?.addEventListener("submit", async event => {
        event.preventDefault(); const errorBox = document.getElementById("profileFormError"); errorBox.textContent = "";
        const details = typeSelect.value === "blood_donor" ? {blood_group: document.getElementById("donorGroup").value.trim(), area: document.getElementById("donorArea").value.trim()} : {};
        try { const response = await apiRequest("/api/auth/profiles/", "POST", {profile_type: typeSelect.value, details}); await apiRequest("/api/auth/active-profile/", "PUT", {profile_id: response.data.id}); const user = getStoredUser() || {}; user.role = profileTypes[response.data.profile_type]; localStorage.setItem("helpnet_user", JSON.stringify(user)); location.reload(); }
        catch (error) { errorBox.textContent = error.message || "Could not create profile."; }
    });
    loadProfiles();

    /* =====================================================
       1. LOGIN CHECK
    ===================================================== */

    if (
        typeof requireLogin === "function" &&
        !requireLogin()
    ) {
        return;
    }


    /* =====================================================
       2. GET LOGGED-IN USER
    ===================================================== */

    let user = null;

    if (typeof getStoredUser === "function") {
        user = getStoredUser();
    }

    /*
       Fallback: directly read localStorage.
       This makes the dashboard independent of any
       possible getStoredUser() issue.
    */

    if (!user) {

        try {

            const storedUser =
                localStorage.getItem("helpnet_user");

            if (storedUser) {
                user = JSON.parse(storedUser);
            }

        } catch (error) {

            console.error(
                "Could not read stored user:",
                error
            );
        }
    }


    if (!user) {

        console.warn(
            "HELPNET Dashboard: no stored user found."
        );

        return;
    }


    /* =====================================================
       3. USER INFORMATION
    ===================================================== */

    const userId =
        user.user_id ||
        user.id ||
        user.pk ||
        "";

    const displayName =
        user.full_name ||
        user.name ||
        user.username ||
        "HELPNET User";


    /*
       IMPORTANT:
       Always normalize the role.
    */

   const role =
    String(user.role || "")
        .trim()
        .toLowerCase()
        .replace(/\s+/g, "_");


    console.log(
        "===================================="
    );

    console.log(
        "HELPNET DASHBOARD USER:",
        user
    );

    console.log(
        "HELPNET DASHBOARD ROLE:",
        role
    );

    console.log(
        "HELPNET DASHBOARD USER ID:",
        userId
    );

    console.log(
        "===================================="
    );


    /* =====================================================
       4. ROLE INFORMATION
    ===================================================== */

    const roleInfo = {

        citizen: {

            title: "Citizen Dashboard",

            description:
                "Access community services, share unused goods, manage waste requests and get help from the community.",

            activityTitle:
                "Citizen Activities",

            activities: [

                {
                    icon: "♻️",
                    title: "Goods Exchange",
                    text:
                        "Share or claim unused goods."
                },

                {
                    icon: "🩸",
                    title: "Blood Support",
                    text:
                        "Create or respond to blood-related requests."
                },

                {
                    icon: "🗑️",
                    title: "Waste Management",
                    text:
                        "Manage your waste pickup requests."
                }

            ]
        },


        volunteer: {

            title: "Volunteer Dashboard",

            description:
                "Find community events, join volunteer activities and help people through HELPNET.",

            activityTitle:
                "Volunteer Activities",

            activities: [

                {
                    icon: "🤝",
                    title: "Volunteer Events",
                    text:
                        "Browse and register for community events."
                },

                {
                    icon: "🩸",
                    title: "Blood Support",
                    text:
                        "Help people with blood-related needs."
                },

                {
                    icon: "❤️",
                    title: "Community Help",
                    text:
                        "Take part in activities that support your community."
                }

            ]
        },


        ngo: {

            title: "NGO Dashboard",

            description:
                "Organize community activities, manage volunteer events and work with verification services.",

            activityTitle:
                "NGO Activities",

            activities: [

                {
                    icon: "🤝",
                    title: "Community Events",
                    text:
                        "Create and manage volunteer and community events."
                },

                {
                    icon: "🛡️",
                    title: "Verification",
                    text:
                        "Review available verification requests."
                },

                {
                    icon: "❤️",
                    title: "Community Support",
                    text:
                        "Support people and community activities."
                }

            ]
        },


        farmer: {

            title: "Farmer Dashboard",

            description:
                "Manage your farmer marketplace activities and connect with people looking for local products.",

            activityTitle:
                "Farmer Activities",

            activities: [

                {
                    icon: "🌾",
                    title: "Farmer Market",
                    text:
                        "View and manage farmer marketplace activities."
                },

                {
                    icon: "📦",
                    title: "Product Listings",
                    text:
                        "Manage your available agricultural products."
                },

                {
                    icon: "❤️",
                    title: "Community Support",
                    text:
                        "Connect with the HELPNET community."
                }

            ]
        },

    
        blood_donor: {
        title: "Blood Donor",

        description:
            "Help save lives by donating blood and responding to blood requests.",

        activityTitle:
            "Blood Donation Activity",

        activities: [

            {
                icon: "🩸",
                title: "Blood Donation",
                text:
                    "Manage your donor profile and help people who need blood."
            },

            {
                icon: "🔎",
                title: "Blood Requests",
                text:
                    "View blood-related requests and respond when you are available."
            },

            {
                icon: "❤️",
                title: "Community Support",
                text:
                    "Help save lives through blood donation."
            }

        ]
    },

        admin: {

            title: "Admin Dashboard",

            description:
                "Manage verification, review system activity and access administrative tools.",

            activityTitle:
                "Administrative Activities",

            activities: [

                {
                    icon: "📋",
                    title: "Review Queue",
                    text:
                        "Review pending system requests."
                },

                {
                    icon: "📜",
                    title: "Action Log",
                    text:
                        "View recorded administrative actions."
                },

                {
                    icon: "📊",
                    title: "Reports",
                    text:
                        "Access administrative reports."
                }

            ]
        }

    };


    /* =====================================================
       5. VALIDATE ROLE
    ===================================================== */

    if (!roleInfo[role]) {

        console.error(
            "HELPNET Dashboard: unknown user role:",
            user.role
        );

        return;
    }


    const currentRole =
        roleInfo[role];


    console.log(
        "HELPNET Dashboard active role:",
        role
    );

    console.log(
        "HELPNET Dashboard configuration:",
        currentRole.title
    );


    /* =====================================================
       6. WELCOME NAME
    ===================================================== */

    const welcomeName =
        document.getElementById(
            "welcomeName"
        );

    if (welcomeName) {

        welcomeName.textContent =
            displayName + " 👋";
    }


    /* =====================================================
       7. ROLE TITLE
    ===================================================== */

    const dashboardRoleTitle =
        document.getElementById(
            "dashboardRoleTitle"
        );

    if (dashboardRoleTitle) {

        dashboardRoleTitle.textContent =
            currentRole.title;
    }


    /* =====================================================
       8. ROLE SECTION
    ===================================================== */

    const roleSectionTitle =
        document.getElementById(
            "roleSectionTitle"
        );

    if (roleSectionTitle) {

        roleSectionTitle.textContent =
            currentRole.title;
    }


    const roleSectionDescription =
        document.getElementById(
            "roleSectionDescription"
        );

    if (roleSectionDescription) {

        roleSectionDescription.textContent =
            currentRole.description;
    }


    /* =====================================================
       9. USER EMAIL / PHONE
    ===================================================== */

    const userEmail =
        document.getElementById(
            "userEmail"
        );

    if (userEmail) {

        userEmail.textContent =
            user.email ||
            user.phone_number ||
            user.phone ||
            "-";
    }


    /* =====================================================
       10. TRUST BLOCK
    ===================================================== */

    const trustHost =
        document.getElementById(
            "dashboardTrust"
        );

    if (trustHost) {

        trustHost.dataset.userId =
            userId;

        if (
            typeof window.loadTrustBlock ===
            "function"
        ) {

            window.loadTrustBlock(
                trustHost
            );
        }
    }


    /* =====================================================
       11. NID VERIFICATION CALLOUT
    ===================================================== */

    const verifyCallout =
        document.getElementById(
            "verifyCallout"
        );

    if (verifyCallout) {

        const status =
            String(
                user.verification_status ||
                user.nid_status ||
                "unverified"
            )
            .toLowerCase()
            .trim();


        /*
           Only show verification reminder when
           the user's verification is not approved.
        */

        verifyCallout.hidden =
            status === "approved";
    }


    /* =====================================================
       12. ADMIN SECTION
    ===================================================== */

    const adminSection =
        document.getElementById(
            "adminSection"
        );

    const isAdmin =
        role === "admin" ||
        user.is_staff === true ||
        user.is_superuser === true;

    if (adminSection) {

        adminSection.hidden =
            !isAdmin;
    }


    /* =====================================================
       13. ROLE BASED SERVICE CARDS
    ===================================================== */

    const serviceCards =
        document.querySelectorAll(
            ".role-service"
        );


    console.log(
        "HELPNET service cards found:",
        serviceCards.length
    );


    serviceCards.forEach(function (card) {

        const allowedRoles =
            String(
                card.dataset.roles || ""
            )
            .toLowerCase()
            .split(/\s+/)
            .filter(Boolean);


        const shouldShow =
            allowedRoles.includes(role);


        card.hidden =
            !shouldShow;


        console.log(
            "SERVICE:",
            card.textContent.trim(),
            "| allowed:",
            allowedRoles,
            "| current:",
            role,
            "| visible:",
            shouldShow
        );

    });


    /* =====================================================
       14. ROLE SPECIFIC ACTIVITIES
    ===================================================== */

    const roleActivityList =
        document.getElementById(
            "roleActivityList"
        );


    if (roleActivityList) {

        roleActivityList.innerHTML = "";


        currentRole.activities.forEach(
            function (activity) {

                const card =
                    document.createElement(
                        "div"
                    );


                card.className =
                    "activity-card";


                card.innerHTML = `

                    <div class="activity-icon">
                        ${activity.icon}
                    </div>

                    <div class="activity-content">

                        <strong>
                            ${activity.title}
                        </strong>

                        <p>
                            ${activity.text}
                        </p>

                    </div>

                `;


                roleActivityList.appendChild(
                    card
                );

            }
        );
    }


    /* =====================================================
       15. ACTIVITY SECTION TITLE
    ===================================================== */

    const activitySectionTitle =
        document.getElementById(
            "activitySectionTitle"
        );

    if (activitySectionTitle) {

        activitySectionTitle.textContent =
            currentRole.activityTitle;
    }


    /* =====================================================
       16. DASHBOARD ROLE DEBUG
    ===================================================== */

    console.log(
        "HELPNET Dashboard successfully initialized for:",
        role
    );

});

/* =====================================================
   FIND PEOPLE
===================================================== */

const peopleSearchForm =
    document.getElementById("peopleSearchForm");

const peopleSearchInput =
    document.getElementById("peopleSearchInput");

if (peopleSearchForm && peopleSearchInput) {

    peopleSearchForm.addEventListener("submit", function (event) {
        event.preventDefault();

        const query =
            peopleSearchInput.value.trim();

        if (!query) {
            peopleSearchInput.focus();
            return;
        }

        window.location.href =
            "/user-search/?q=" +
            encodeURIComponent(query);
    });

}
