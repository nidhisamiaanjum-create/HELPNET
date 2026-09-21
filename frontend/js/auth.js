
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
   Must contain:
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

    /*
       Check if this is actually the register page
       before doing anything else.
    */

    const form =
        document.getElementById("registerForm");

    if (!form) {
        return;
    }

    redirectIfLoggedIn();


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


            const role =
                document
                    .getElementById("role")
                    .value;


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


            /* Role */

            if (!role) {

                showFieldError(
                    "role",
                    "Please select your role."
                );

                valid = false;
            }


            /* Stop if validation failed */

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
               Disable register button
               -------------------------------------------- */

            setBusy(button, true);


            try {

                /* ----------------------------------------
                   Send registration request to Django
                   ---------------------------------------- */

                const data =
                    await apiRequest(
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

                console.error(
                    "Registration error:",
                    error
                );

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

    /*
       Check if this is actually the login page
       before calling redirectIfLoggedIn().
    */

    const form =
        document.getElementById("loginForm");

    if (!form) {
        return;
    }

    redirectIfLoggedIn();


    const button =
        document.getElementById("loginButton");


    form.addEventListener(
        "submit",
        async function (event) {

            event.preventDefault();


            /* --------------------------------------------
               Clear previous errors
               -------------------------------------------- */

            hideAlert("formAlert");

            clearFieldErrors("loginForm");


            /* --------------------------------------------
               Get login values
               -------------------------------------------- */

            const email =
                document
                    .getElementById("email")
                    .value
                    .trim();


            const password =
                document
                    .getElementById("password")
                    .value;


            /* --------------------------------------------
               Validation
               -------------------------------------------- */

            let valid = true;


            /* Email */

            if (!email) {

                showFieldError(
                    "email",
                    t("required")
                );

                valid = false;
            }


            /* Password */

            if (!password) {

                showFieldError(
                    "password",
                    t("required")
                );

                valid = false;
            }


            /* Stop if validation failed */

            if (!valid) {
                return;
            }


            /* --------------------------------------------
               Disable login button
               -------------------------------------------- */

            setBusy(button, true);


            try {

                /* ----------------------------------------
                   Send login request to Django
                   ---------------------------------------- */

                const response =
                    await apiRequest(
                        "/api/auth/login/",
                        "POST",
                        {
                            email: email,
                            password: password
                        }
                    );


                /* ----------------------------------------
                   Get login data
                   ---------------------------------------- */

                const user =
                    response.data;


                const accessToken =
                    user.access;


                /* ----------------------------------------
                   Store user information
                   Role comes from backend
                   ---------------------------------------- */

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


                /* ----------------------------------------
                   Save session
                   ---------------------------------------- */

                saveSession(
                    accessToken,
                    userInfo
                );


                /* ----------------------------------------
                   Success message
                   ---------------------------------------- */

                showAlert(
                    "formAlert",
                    response.message ||
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

                console.error(
                    "Login error:",
                    error
                );

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
       Clear JWT and stored user information.
    */

    clearSession();

    window.location.href =
        "login.html";
}


/* ============================================================
   LOGOUT BUTTON
   ============================================================ */

function initLogout() {

    const button =
        document.getElementById(
            "logoutButton"
        );


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


            /* --------------------------------------------
               Clear previous errors
               -------------------------------------------- */

            hideAlert("formAlert");

            clearFieldErrors(
                "forgotPasswordForm"
            );


            /* --------------------------------------------
               Get phone
               -------------------------------------------- */

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


            /* --------------------------------------------
               Disable button
               -------------------------------------------- */

            setBusy(button, true);


            try {

                /*
                   Password reset endpoint will be
                   implemented separately.
                */

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

        /*
           These functions are safe to call on every page
           because each function first checks whether its
           required form/button exists.
        */

        initRegisterPage();

        initLoginPage();

        initForgotPasswordPage();

        initLogout();
    }
);
