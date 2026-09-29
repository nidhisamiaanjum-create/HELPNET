document.addEventListener("DOMContentLoaded", function () {

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