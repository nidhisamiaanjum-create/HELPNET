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

        const role =
            document.getElementById("role").value;

        const district =
            document.getElementById("district").value;

        const upazila =
            document.getElementById("upazila").value.trim();


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


        if (!role) {

            showFieldError(
                "role",
                t("selectRole")
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
                    role: role,
                    location: location
                }
            );


            console.log("Registration response:", data);


            /* Success */

            showAlert(
                "formAlert",
                data.message || "Registration successful!",
                "success"
            );


            form.reset();


            /*
               Go to login page after registration.
            */

            setTimeout(function () {

                window.location.href = "/login/";

            }, 1200);


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


                /* Get user data */

                const user =
                    response.data;


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

                    user_id:
                        user.user_id,

                    full_name:
                        user.full_name,

                    email:
                        user.email,

                    phone_number:
                        user.phone_number,

                    role:
                        user.role
                };

                console.log("LOGIN RESPONSE USER:", user);
                console.log("LOGIN RESPONSE ROLE:", user.role);

                /* Save session */

                saveSession(
                    accessToken,
                    userInfo
                );


                /*
                   Save refresh token separately.
                */

                if (refreshToken) {

                     localStorage.setItem("helpnet_token", accessToken);
                     localStorage.setItem("refreshToken", refreshToken);
                }


                /* Success */

                showAlert(
                    "formAlert",
                    response.message ||
                    "Login successful!",
                    "success"
                );


                /* Go to dashboard */

                window.location.href = user.role && user.role.toLowerCase() === "admin"
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
