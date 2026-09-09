
/* ============================================================
   HELPNET AUTHENTICATION
   Frontend: HTML + CSS + Vanilla JavaScript
   Backend: Django REST Framework
   ============================================================ */


/* ============================================================
   PHONE VALIDATION
   Bangladesh phone number format
   Examples:
   01712345678
   01812345678
   +8801712345678
   008801712345678
   ============================================================ */

const PHONE_RE = /^(?:\+?88)?(01[3-9]\d{8})$/;


function isValidPhone(value) {
    return PHONE_RE.test(value);
}


/* ============================================================
   PASSWORD VALIDATION
   Minimum 8 characters
   Must contain at least:
   - one letter
   - one number
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
   REGISTER PAGE
   ============================================================ */

function initRegisterPage() {

    redirectIfLoggedIn();

    const form =
        document.getElementById("registerForm");

    if (!form) {
        return;
    }

    const button =
        document.getElementById("registerButton");


    form.addEventListener(
        "submit",
        async function (event) {

            event.preventDefault();


            /* --------------------------------------------
               Clear previous errors
               -------------------------------------------- */

            hideAlert("formAlert");

            clearFieldErrors("registerForm");


            /* --------------------------------------------
               Get form values
               -------------------------------------------- */

            const fullName =
                document
                    .getElementById("fullName")
                    .value
                    .trim();

            const phone =
                document
                    .getElementById("phoneNumber")
                    .value
                    .trim();

            const password =
                document
                    .getElementById("password")
                    .value;

            const email =
                document
                    .getElementById("email")
                    .value
                    .trim();

            const district =
                document
                    .getElementById("district")
                    .value;

            const upazila =
                document
                    .getElementById("upazila")
                    .value
                    .trim();


            /* --------------------------------------------
               Frontend validation
               -------------------------------------------- */

            let valid = true;


            /* Full name */

            if (fullName.length < 2) {

                showFieldError(
                    "fullName",
                    t("required")
                );

                valid = false;
            }


            /* Phone */

            if (!isValidPhone(phone)) {

                showFieldError(
                    "phoneNumber",
                    t("phoneHint")
                );

                valid = false;
            }


            /* Password */

            if (!isValidPassword(password)) {

                showFieldError(
                    "password",
                    t("passwordHint")
                );

                valid = false;
            }


            /* Email */

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


            /* --------------------------------------------
               Create location
               -------------------------------------------- */

            const location = [
                district,
                upazila
            ]
            .filter(Boolean)
            .join(", ");


            /* --------------------------------------------
               Disable button
               -------------------------------------------- */

            setBusy(button, true);


            try {

                /* ----------------------------------------
                   Send registration request to Django
                   ---------------------------------------- */

                const data = await apiRequest(
                    "/api/auth/register/",
                    "POST",
                    {
                        full_name: fullName,

                        phone_number: phone,

                        password: password,

                        email: email,

                        role: "Citizen",

                        location: location
                    }
                );


                /* ----------------------------------------
                   Registration successful
                   ---------------------------------------- */

                showAlert(
                    "formAlert",
                    data.message ||
                    t("registerSuccess"),
                    "success"
                );


                form.reset();


                /* ----------------------------------------
                   Redirect to login
                   ---------------------------------------- */

                setTimeout(
                    function () {

                        window.location.href =
                            "login.html";

                    },
                    1200
                );


            } catch (error) {

                showAlert(
                    "formAlert",
                    error.message,
                    "error"
                );

            } finally {

                setBusy(button, false);
            }
        }
    );
}


/* ============================================================
   LOGIN PAGE
   ============================================================ */

function initLoginPage() {

    redirectIfLoggedIn();

    const form =
        document.getElementById("loginForm");

    if (!form) {
        return;
    }

    const button =
        document.getElementById("loginButton");


    form.addEventListener(
        "submit",
        async function (event) {

            event.preventDefault();


            hideAlert("formAlert");

            clearFieldErrors("loginForm");


            /* --------------------------------------------
               Get values
               -------------------------------------------- */

            const phone =
                document
                    .getElementById("phoneNumber")
                    .value
                    .trim();

            const password =
                document
                    .getElementById("password")
                    .value;


            /* --------------------------------------------
               Validate
               -------------------------------------------- */

            let valid = true;


            if (!isValidPhone(phone)) {

                showFieldError(
                    "phoneNumber",
                    t("phoneHint")
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


            setBusy(button, true);


            try {

                /* ----------------------------------------
                   Django SimpleJWT login endpoint
                   ---------------------------------------- */

                const data = await apiRequest(
                    "/api/auth/login/",
                    "POST",
                    {
                        phone_number: phone,
                        password: password
                    }
                );


                /* ----------------------------------------
                   Save JWT + user information
                   ---------------------------------------- */

                saveSession(
                    data.access,
                    data.user
                );


                showAlert(
                    "formAlert",
                    data.message ||
                    t("loginSuccess"),
                    "success"
                );


                /* ----------------------------------------
                   Go to dashboard
                   ---------------------------------------- */

                setTimeout(
                    function () {

                        window.location.href =
                            "dashboard.html";

                    },
                    700
                );


            } catch (error) {

                showAlert(
                    "formAlert",
                    error.message,
                    "error"
                );

            } finally {

                setBusy(button, false);
            }
        }
    );
}


/* ============================================================
   LOGOUT
   ============================================================ */

function logout() {

    /*
       JWT is currently stored on the frontend.

       Clearing the token logs the user out from this browser.
    */

    clearSession();

    window.location.href = "login.html";
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
   FORGOT PASSWORD PAGE
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


            /* --------------------------------------------
               Validate phone
               -------------------------------------------- */

            if (!isValidPhone(phone)) {

                showFieldError(
                    "phoneNumber",
                    t("phoneHint")
                );

                return;
            }


            setBusy(button, true);


            try {

                /*
                   Password reset endpoint will be implemented
                   with OTP by Arnob in Sprint 1.
                */

                const data = await apiRequest(
                    "/api/auth/forgot-password/",
                    "POST",
                    {
                        phone_number: phone
                    }
                );


                showAlert(
                    "formAlert",
                    data.message ||
                    t("resetSuccess"),
                    "success"
                );


            } catch (error) {

                showAlert(
                    "formAlert",
                    error.message,
                    "error"
                );

            } finally {

                setBusy(button, false);
            }
        }
    );
}


/* ============================================================
   INITIALIZE AUTH PAGES
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
