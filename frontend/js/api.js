/* ============================================================
   HELPNET API CONNECTION
   Frontend: HTML + CSS + Vanilla JavaScript
   Backend: Django REST Framework
   ============================================================ */

const API_BASE = (typeof window !== "undefined" && window.location && window.location.origin && window.location.origin.startsWith("http")) ? window.location.origin : "http://127.0.0.1:8000";

const TOKEN_KEY = "helpnet_token";
const USER_KEY = "helpnet_user";


/* ============================================================
   SESSION
   ============================================================ */

function saveSession(token, user) {

    localStorage.setItem(
        TOKEN_KEY,
        token
    );

    localStorage.setItem(
        USER_KEY,
        JSON.stringify(user)
    );

    if (
        user &&
        user.preferred_language &&
        typeof setLanguage === "function"
    ) {
        setLanguage(
            user.preferred_language
        );
    }
}


function getToken() {

    return localStorage.getItem(
        TOKEN_KEY
    );
}


function getStoredUser() {

    try {

        return JSON.parse(
            localStorage.getItem(USER_KEY)
        );

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
    localStorage.removeItem("refreshToken");
}


/* ============================================================
   API REQUEST
   ============================================================ */

function isPublicAuthEndpoint(path) {
    const cleanPath = path.split("?")[0].replace(/\/+$/, "") + "/";

    const publicEndpoints = [
        "/api/auth/login/",
        "/api/auth/register/",
        "/api/auth/forgot-password/",
        "/api/auth/reset-password/"
    ];

    return publicEndpoints.includes(cleanPath);
}

function formatApiError(data) {
    if (!data) {
        return "Request failed. Please try again.";
    }

    // SimpleJWT error
    if (data.detail && typeof data.detail === "string") {
        return data.detail;
    }

    if (data.message) {
        if (typeof data.message === "string") {
            return data.message;
        }

        if (typeof data.message === "object") {
            return formatApiError(data.message);
        }
    }

    if (typeof data === "object") {
        const errors = [];

        Object.keys(data).forEach(function (field) {
            const value = data[field];

            if (Array.isArray(value)) {
                value.forEach(function (item) {
                    if (typeof item === "object" && item !== null) {
                        if (item.message) {
                            errors.push(String(item.message));
                        }
                    } else {
                        errors.push(String(item));
                    }
                });
            } else if (typeof value === "object" && value !== null) {
                if (value.message) {
                    errors.push(String(value.message));
                }
            } else {
                errors.push(String(value));
            }
        });

        if (errors.length > 0) {
            return errors.join(" ");
        }
    }

    return "Request failed. Please try again.";
}


async function apiRequest(path, method = "GET", body = null) {
    const url = API_BASE + path;

    console.log("API REQUEST URL:", url);
    console.log("API REQUEST METHOD:", method);
    console.log("API REQUEST BODY:", body);

    const options = {
        method: method,
        headers: {}
    };

    const token = getToken();

    // IMPORTANT:
    // Never send an old JWT to public authentication endpoints.
    if (token && !isPublicAuthEndpoint(path)) {
        options.headers["Authorization"] = "Bearer " + token;
    }

    if (body) {
        if (body instanceof FormData) {
            options.body = body;
        } else {
            options.headers["Content-Type"] = "application/json";
            options.body = JSON.stringify(body);
        }
    }

    console.log("Sending fetch request...");

    let response;

    try {
        response = await fetch(url, options);
        console.log("Fetch completed. HTTP status:", response.status);
    } catch (error) {
        console.error("FETCH ERROR:", error);
        throw new Error("Could not connect to the HELPNET server.");
    }

    let data = null;

    try {
        data = await response.json();
        console.log("API RESPONSE DATA:", data);
    } catch (error) {
        console.error("Could not parse JSON response:", error);
    }

    if (!response.ok) {

        // Invalid/expired JWT on a protected request
        if (
            response.status === 401 &&
            data &&
            (
                data.code === "token_not_valid" ||
                data.detail === "Given token not valid for any token type"
            ) &&
            !isPublicAuthEndpoint(path)
        ) {
            console.warn("Invalid/expired JWT detected. Clearing session.");

            clearSession();

            throw new Error(
                "Your session has expired. Please log in again."
            );
        }

        const message = formatApiError(data);

        console.error("API ERROR:", message);

        throw new Error(message);
    }

    console.log("API REQUEST SUCCESS");

    return data;
}


/* ============================================================
   PAGE GUARDS
   ============================================================ */

function requireLogin() {

    if (!isLoggedIn()) {

        window.location.href =
            "/login/";

        return false;
    }

    return true;
}


function redirectIfLoggedIn() {

    if (isLoggedIn()) {

        window.location.href =
            "/dashboard/";
    }
}


/* ============================================================
   UI HELPERS
   ============================================================ */

function showAlert(
    elementId,
    message,
    type
) {

    const box =
        document.getElementById(
            elementId
        );


    if (!box) return;


    box.textContent =
        message;


    box.className =
        "alert show alert-" +
        (type || "error");
}


function hideAlert(
    elementId
) {

    const box =
        document.getElementById(
            elementId
        );


    if (box) {

        box.className =
            "alert";
    }
}


function setBusy(
    button,
    busy
) {

    if (!button) return;


    if (busy) {

        button.dataset.label =
            button.textContent;


        if (
            typeof t === "function"
        ) {

            button.textContent =
                t("loading");

        } else {

            button.textContent =
                "Loading...";
        }


        button.disabled =
            true;

    }

    else {

        if (
            button.dataset.label
        ) {

            button.textContent =
                button.dataset.label;
        }


        button.disabled =
            false;
    }
}


/* ============================================================
   FIELD VALIDATION UI
   ============================================================ */

function showFieldError(
    fieldId,
    message
) {

    const input =
        document.getElementById(
            fieldId
        );


    const error =
        document.getElementById(
            fieldId + "Error"
        );


    if (input) {

        input.classList.add(
            "invalid"
        );
    }


    if (error) {

        error.textContent =
            message;

        error.classList.add(
            "show"
        );
    }
}


function clearFieldErrors(
    formId
) {

    const form =
        document.getElementById(
            formId
        );


    if (!form) return;


    form.querySelectorAll(
        "input, select"
    ).forEach(
        function (input) {

            input.classList.remove(
                "invalid"
            );
        }
    );


    form.querySelectorAll(
        ".field-error"
    ).forEach(
        function (error) {

            error.classList.remove(
                "show"
            );
        }
    );
}
