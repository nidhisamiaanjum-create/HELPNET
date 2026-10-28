/* ============================================================
   HELPNET AUTHENTICATION
   Frontend: HTML + CSS + Vanilla JavaScript
   Backend: Django REST Framework
   ============================================================ */


/* ============================================================
   PHONE VALIDATION
   ============================================================ */

const PHONE_RE = /^(?:\+?88)?(01[3-9]\d{8})$/;

function isValidPhone(value) {
    return PHONE_RE.test(value);
}


/* ============================================================
   PASSWORD VALIDATION
   ============================================================ */

function isValidPassword(value) {

    if (!value || value.length < 8) {
        return false;
    }

    return (
        /[A-Za-z]/.test(value) &&
        /\d/.test(value)
    );
}


/* ============================================================
   REGISTER
   ============================================================ */

function initRegisterPage() {

    const form = document.getElementById("registerForm");

    if (!form) {
        return;
    }

    const button =
        document.getElementById("registerButton");

    form.addEventListener("submit", async function (event) {

        event.preventDefault();

        /* Clear previous errors */

        hideAlert("formAlert");
        clearFieldErrors("registerForm");


        /* Get values */

        const fullName =
            document.getElementById("fullName").value.trim();

        const phone =
            document.getElementById("phoneNumber").value.trim();

        const password =
            document.getElementById("password").value;

        const email =
            document.getElementById("email").value.trim();

        const district =
            document.getElementById("district").value;

        const upazila =
            document.getElementById("upazila").value.trim();
        const accountType =
            document.getElementById("accountType").value;


        /* Validation */

        let valid = true;


        if (fullName.length < 2) {

            showFieldError(
                "fullName",
                t("required")
            );

            valid = false;
        }


        if (!isValidPhone(phone)) {

            showFieldError(
                "phoneNumber",
                t("phoneHint")
            );

            valid = false;
        }


        if (!isValidPassword(password)) {

            showFieldError(
                "password",
                t("passwordHint")
            );

            valid = false;
        }


        if (!email) {

            showFieldError(
                "email",
                t("required")
            );

            valid = false;
        }



        if (!valid) {
            return;
        }


        /* Create location */

        const location = [
            district,
            upazila
        ]
            .filter(Boolean)
            .join(", ");


        setBusy(button, true);


        try {

            console.log("Sending registration request...");


            const data = await apiRequest(
                "/api/auth/register/",
                "POST",
                {
                    full_name: fullName,
                    phone_number: phone,
                    password: password,
                    email: email,
                    location: location,
                    account_type: accountType
                }
            );


            console.log("Registration response:", data);


            /* Success */
            if (accountType === "ngo") {
                showAlert(
                    "formAlert",
                    "NGO registration submitted successfully. Your account is pending administrator approval. You can log in, but NGO services will remain restricted until approval.",
                    "success"
                );
            } else {
                showAlert(
                    "formAlert",
                    data.message || "Registration successful!",
                    "success"
                );
            }

            form.reset();

            if (accountType === "citizen") {
                setTimeout(function () {
                    window.location.href = "/login/";
                }, 1200);
            }
        } catch (error) {

            console.error(
                "Registration error:",
                error
            );


            showAlert(
                "formAlert",
                error.message || "Registration failed.",
                "error"
            );


        } finally {

            setBusy(button, false);
        }

    });
}


/* ============================================================
   LOGIN
   ============================================================ */

/* ============================================================
   LOGIN
   ============================================================ */

function initLoginPage() {

    const form =
        document.getElementById("loginForm");

    if (!form) {
        return;
    }


    const button =
        document.getElementById("loginButton");

    let loginRequestInFlight = false;

    form.addEventListener(
        "submit",
        async function (event) {

            event.preventDefault();


            /* Clear previous errors */

            hideAlert("formAlert");

            clearFieldErrors("loginForm");


            /* Get values */

            const identifier =
                document
                    .getElementById("identifier")
                    .value
                    .trim();


            const password =
                document
                    .getElementById("password")
                    .value;
            console.log("LOGIN IDENTIFIER:", identifier);
            console.log("LOGIN PASSWORD LENGTH:", password.length);

            /* Validation */

            let valid = true;


            if (!identifier) {

                showFieldError(
                    "identifier",
                    t("required")
                );

                valid = false;
            }


            if (!password) {

                showFieldError(
                    "password",
                    t("required")
                );

                valid = false;
            }


            if (!valid) {
                return;
            }

            if (loginRequestInFlight) return;
            loginRequestInFlight = true;

            setBusy(button, true);


            try {

                console.log(
                    "Sending login request..."
                );


                /*
                   Backend accepts either:

                   Email:
                   {
                       identifier: "c@gmail.com",
                       password: "..."
                   }

                   OR phone:
                   {
                       identifier: "01712345671",
                       password: "..."
                   }
                */

                const response =
                    await apiRequest(
                        "/api/auth/login/",
                        "POST",
                        {
                            identifier: identifier,
                            password: password
                        }
                    );


                console.log(
                    "Login response:",
                    response
                );

                console.log("LOGIN RESPONSE DATA:", response.data);

                console.log("LOGIN ADMIN FIELDS:", {
                    role: response.data?.role,
                    is_staff: response.data?.is_staff,
                    is_superuser: response.data?.is_superuser,
                    access: !!response.data?.access,
                    refresh: !!response.data?.refresh
                });
                /* Get user data */

                const user =
                    response.data;
                console.log("FULL LOGIN API RESPONSE:", response);
                console.log("LOGIN USER DATA:", user);
                console.log("ADMIN FLAGS:", {
                    is_staff: user?.is_staff,
                    is_superuser: user?.is_superuser,
                    role: user?.role
                });


                const accessToken =
                    user.access;


                const refreshToken =
                    user.refresh;


                if (!accessToken) {

                    throw new Error(
                        "Login successful, but access token was not received."
                    );
                }


                /* User information */

                const userInfo = {
                    user_id: user.user_id,
                    full_name: user.full_name,
                    email: user.email,
                    phone_number: user.phone_number,
                    role: user.role || "",
                    is_staff: user.is_staff === true,
                    is_superuser: user.is_superuser === true
                };

                console.log("LOGIN RESPONSE USER:", user);
                console.log("LOGIN RESPONSE ROLE:", user.role);

                /* =====================================================
    SAVE NEW LOGIN SESSION
 ===================================================== */

                localStorage.setItem(
                    "helpnet_token",
                    accessToken
                );

                localStorage.setItem(
                    "helpnet_user",
                    JSON.stringify(userInfo)
                );

                if (refreshToken) {
                    localStorage.setItem(
                        "refreshToken",
                        refreshToken
                    );
                }

                console.log(
                    "SESSION SAVED:",
                    JSON.parse(localStorage.getItem("helpnet_user"))
                );

                /* Success */

                showAlert(
                    "formAlert",
                    response.message ||
                    "Login successful!",
                    "success"
                );


                /* Go to dashboard */

                const isAdmin =
                    user.is_superuser === true ||
                    user.is_staff === true ||
                    String(user.role || "").toLowerCase() === "admin";

                window.location.href = isAdmin
                    ? "/admin-dashboard/"
                    : "/dashboard/";

            } catch (error) {

                console.error(
                    "Login error:",
                    error
                );


                showAlert(
                    "formAlert",
                    error.message ||
                    "Login failed.",
                    "error"
                );


            } finally {

                setBusy(button, false);
                loginRequestInFlight = false;
            }

        }
    );
}

window.togglePasswordVisibility = function (toggle) {
    const input = document.getElementById(toggle.dataset.passwordToggle);
    if (!input) return false;

    const showing = input.type === "password";
    input.type = showing ? "text" : "password";
    toggle.setAttribute("aria-pressed", String(showing));
    toggle.textContent = typeof t === "function"
        ? t(showing ? "hidePassword" : "showPassword")
        : (showing ? "Hide password" : "Show password");
    return false;
};


/* ============================================================
   LOGOUT
   ============================================================ */

async function logout() {

    const refreshToken = localStorage.getItem("refreshToken");

    if (refreshToken) {
        try {
            await apiRequest(
                "/api/auth/logout/",
                "POST",
                {
                    refresh: refreshToken
                }
            );
        } catch (error) {
            console.error("Logout API error:", error);
        }
    }

    clearSession();

    localStorage.removeItem("refreshToken");

    window.location.href =
        "/login/";
}


/* ============================================================
   LOGOUT BUTTON
   ============================================================ */

function initLogout() {

    const button =
        document.getElementById("logoutButton");


    if (!button) {
        return;
    }


    button.addEventListener(
        "click",
        function (event) {

            event.preventDefault();

            logout();

        }
    );
}


/* ============================================================
   FORGOT PASSWORD
   ============================================================ */

function initForgotPasswordPage() {

    const form =
        document.getElementById(
            "forgotPasswordForm"
        );


    if (!form) {
        return;
    }


    const button =
        document.getElementById(
            "forgotPasswordButton"
        );


    form.addEventListener(
        "submit",
        async function (event) {

            event.preventDefault();


            hideAlert("formAlert");

            clearFieldErrors(
                "forgotPasswordForm"
            );


            const phone =
                document
                    .getElementById("phoneNumber")
                    .value
                    .trim();


            if (!isValidPhone(phone)) {

                showFieldError(
                    "phoneNumber",
                    t("phoneHint")
                );

                return;
            }


            setBusy(button, true);


            try {

                const data =
                    await apiRequest(
                        "/api/auth/forgot-password/",
                        "POST",
                        {
                            phone_number: phone
                        }
                    );


                showAlert(
                    "formAlert",
                    data.message ||
                    "Password reset request sent.",
                    "success"
                );


            } catch (error) {

                showAlert(
                    "formAlert",
                    error.message ||
                    "Password reset failed.",
                    "error"
                );


            } finally {

                setBusy(button, false);
            }
        }
    );
}


/* ============================================================
   INITIALIZE
   ============================================================ */

document.addEventListener(
    "DOMContentLoaded",
    function () {

        initRegisterPage();

        initLoginPage();

        initForgotPasswordPage();

        initLogout();

    }
);
