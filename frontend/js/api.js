/* ============================================================
   HELPNET API CONNECTION
   Frontend: HTML + CSS + Vanilla JavaScript
   Backend: Django REST Framework
   ============================================================ */

const API_BASE = "http://127.0.0.1:8000";

const TOKEN_KEY = "helpnet_token";
const USER_KEY = "helpnet_user";


/* ============================================================
   SESSION
   ============================================================ */

function saveSession(token, user) {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));

    if (user && user.preferred_language) {
        setLanguage(user.preferred_language);
    }
}


function getToken() {
    return localStorage.getItem(TOKEN_KEY);
}


function getStoredUser() {
    try {
        return JSON.parse(localStorage.getItem(USER_KEY));
    } catch (error) {
        return null;
    }
}


function isLoggedIn() {
    return !!getToken();
}


function clearSession() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
}


/* ============================================================
   API REQUEST
   ============================================================ */

async function apiRequest(path, method = "GET", body = null) {

    const options = {
        method: method,
        headers: {
            "Content-Type": "application/json"
        }
    };

    /*
       Add JWT token when we implement login.
    */
    const token = getToken();

    if (token) {
        options.headers["Authorization"] = "Bearer " + token;
    }

    if (body) {
        options.body = JSON.stringify(body);
    }

    let response;

    try {
        response = await fetch(API_BASE + path, options);
    } catch (error) {
        throw new Error(
            "Could not connect to the HELPNET server."
        );
    }


    /* ========================================================
       READ RESPONSE
       ======================================================== */

    let data = null;

    try {
        data = await response.json();
    } catch (error) {
        data = null;
    }


    /* ========================================================
       HANDLE ERRORS
       ======================================================== */

    if (!response.ok) {

    let message = "Request failed. Please try again.";

    if (data) {

        /* --------------------------------------------
           Django response with message
           -------------------------------------------- */

        if (data.message) {

            if (typeof data.message === "string") {

                message = data.message;

            } else if (typeof data.message === "object") {

                const errors = [];

                Object.keys(data.message).forEach(function (field) {

                    const value = data.message[field];

                    if (Array.isArray(value)) {

                        errors.push(
                            value.join(" ")
                        );

                    } else {

                        errors.push(
                            String(value)
                        );
                    }
                });

                if (errors.length > 0) {

                    message = errors.join(" ");
                }
            }
        }

        /* --------------------------------------------
           Direct Django REST Framework errors
           -------------------------------------------- */

        else if (typeof data === "object") {

            const errors = [];

            Object.keys(data).forEach(function (field) {

                const value = data[field];

                if (Array.isArray(value)) {

                    errors.push(
                        value.join(" ")
                    );

                } else {

                    errors.push(
                        String(value)
                    );
                }
            });

            if (errors.length > 0) {

                message = errors.join(" ");
            }
        }
    }

    throw new Error(message);
}


    /* ========================================================
       SUCCESS
       ======================================================== */

    return data;
}


/* ============================================================
   PAGE GUARDS
   ============================================================ */

function requireLogin() {

    if (!isLoggedIn()) {
        window.location.href = "login.html";
        return false;
    }

    return true;
}


function redirectIfLoggedIn() {

    if (isLoggedIn()) {
        window.location.href = "dashboard.html";
    }
}


/* ============================================================
   UI HELPERS
   ============================================================ */

function showAlert(elementId, message, type) {

    const box = document.getElementById(elementId);

    if (!box) return;

    box.textContent = message;

    box.className =
        "alert show alert-" + (type || "error");
}


function hideAlert(elementId) {

    const box = document.getElementById(elementId);

    if (box) {
        box.className = "alert";
    }
}


function setBusy(button, busy) {

    if (!button) return;

    if (busy) {

        button.dataset.label = button.textContent;

        button.textContent = t("loading");

        button.disabled = true;

    } else {

        if (button.dataset.label) {
            button.textContent = button.dataset.label;
        }

        button.disabled = false;
    }
}


/* ============================================================
   FIELD VALIDATION UI
   ============================================================ */

function showFieldError(fieldId, message) {

    const input = document.getElementById(fieldId);

    const error =
        document.getElementById(fieldId + "Error");

    if (input) {
        input.classList.add("invalid");
    }

    if (error) {

        error.textContent = message;

        error.classList.add("show");
    }
}


function clearFieldErrors(formId) {

    const form = document.getElementById(formId);

    if (!form) return;

    form.querySelectorAll("input, select").forEach(
        function (input) {
            input.classList.remove("invalid");
        }
    );

    form.querySelectorAll(".field-error").forEach(
        function (error) {
            error.classList.remove("show");
        }
    );
}