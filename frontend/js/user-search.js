document.addEventListener("DOMContentLoaded", function () {

    const form = document.getElementById("userSearchForm");
    const input = document.getElementById("userSearchInput");
    const results = document.getElementById("userSearchResults");
    const message = document.getElementById("userSearchMessage");

    if (!form || !input || !results || !message) {
        console.error("User search elements not found.");
        return;
    }

    const params = new URLSearchParams(window.location.search);
    const initialQuery = params.get("q") || "";

    if (initialQuery) {
        input.value = initialQuery;
        searchUsers(initialQuery);
    }

    form.addEventListener("submit", function (event) {
        event.preventDefault();

        const query = input.value.trim();

        if (!query) {
            message.textContent =
                "Please enter a name, role or area.";
            results.innerHTML = "";
            return;
        }

        const newUrl =
            "/user-search/?q=" +
            encodeURIComponent(query);

        window.history.replaceState({}, "", newUrl);

        searchUsers(query);
    });


    async function searchUsers(query) {

        message.textContent = "Searching...";
        results.innerHTML = "";

        try {

            const token =
                localStorage.getItem("helpnet_token");

            if (!token) {
                message.textContent =
                    "Please log in to search HELPNET members.";
                return;
            }

            const response = await fetch(
                "http://127.0.0.1:8000/api/users/search/?q=" +
                encodeURIComponent(query),
                {
                    method: "GET",
                    headers: {
                        "Authorization": "Bearer " + token
                    }
                }
            );

            console.log("User search status:", response.status);

            if (!response.ok) {

                if (response.status === 401) {
                    message.textContent =
                        "Your session has expired. Please log in again.";
                    return;
                }

                throw new Error(
                    "Search request failed: " +
                    response.status
                );
            }

            const data = await response.json();

            console.log("User search response:", data);

            const users =
                Array.isArray(data)
                    ? data
                    : Array.isArray(data.data)
                        ? data.data
                        : Array.isArray(data.results)
                            ? data.results
                            : [];

            if (users.length === 0) {
                message.textContent =
                    "No HELPNET members found.";
                return;
            }

            message.textContent =
                `${users.length} member(s) found.`;

            renderUsers(users);

        } catch (error) {

            console.error("User search error:", error);

            message.textContent =
                "Could not search users. Please try again.";
        }
    }


    function renderUsers(users) {

        results.innerHTML = "";

        users.forEach(function (user) {

            const card =
                document.createElement("article");

            card.className = "user-result-card";

            const name =
                user.full_name ||
                user.name ||
                "HELPNET User";

            const role =
                user.role || "Member";

            const area =
                user.location ||
                user.area ||
                "Location not provided";

            card.innerHTML = `
                <div class="user-result-info">
                    <h2>${escapeHtml(name)}</h2>
                    <p>${escapeHtml(role)}</p>
                    <p>📍 ${escapeHtml(area)}</p>
                </div>

                <a
                    class="btn user-profile-btn"
                    href="/profile/?user_id=${encodeURIComponent(user.user_id)}">
                    View Profile
                </a>
            `;

            results.appendChild(card);
        });
    }


    function escapeHtml(value) {

        return String(value)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

});