let selectedRating = 0;
let ratedUserId = "";

function showRatingsMessage(message, type = "") {
    const element = document.getElementById("ratingsMessage");
    if (!element) return;
    element.textContent = message;
    element.className = `form-message ${type}`;
}

function renderRatingPicker() {
    const picker = document.getElementById("starPicker");
    if (!picker) return;
    picker.replaceChildren();
    for (let value = 1; value <= 5; value += 1) {
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = "★";
        button.className = value <= selectedRating ? "selected" : "";
        button.setAttribute("aria-label", `${value} star${value === 1 ? "" : "s"}`);
        button.setAttribute("aria-checked", value === selectedRating ? "true" : "false");
        button.addEventListener("click", () => {
            selectedRating = value;
            renderRatingPicker();
        });
        picker.appendChild(button);
    }
}

function renderExistingRatings(ratings) {
    const container = document.getElementById("existingRatings");
    if (!container) return;
    container.replaceChildren();
    const heading = document.createElement("h3");
    heading.textContent = "Existing ratings";
    container.appendChild(heading);

    if (!ratings.length) {
        const empty = document.createElement("p");
        empty.textContent = "No ratings yet.";
        container.appendChild(empty);
        return;
    }

    ratings.forEach((item) => {
        const article = document.createElement("article");
        article.className = "rating-item";
        const title = document.createElement("strong");
        title.textContent = `${item.rater_name} · ${"★".repeat(item.rating)}`;
        const comment = document.createElement("p");
        comment.textContent = item.comment || "No comment";
        article.append(title, comment);
        container.appendChild(article);
    });
}

async function loadRatings() {
    ratedUserId = document.getElementById("ratedUserId").value.trim();
    if (!ratedUserId) {
        showRatingsMessage("User ID is required.", "error");
        return;
    }

    try {
        const [average, ratings] = await Promise.all([
            apiRequest(`/api/ratings/users/${ratedUserId}/average/`),
            apiRequest(`/api/ratings/users/${ratedUserId}/`),
        ]);
        document.getElementById("ratingsContent").hidden = false;
        const averageValue = average.data.average_rating;
        document.getElementById("averageRating").textContent =
            `Average: ${averageValue === null ? "0.0" : Number(averageValue).toFixed(1)} / 5 · ${average.data.rating_count} ratings`;
        renderExistingRatings(ratings.data);
        showRatingsMessage("");
    } catch (error) {
        showRatingsMessage(error.message, "error");
    }
}

async function submitRating(event) {
    event.preventDefault();
    if (!selectedRating) {
        showRatingsMessage("Choose a rating from 1 to 5 stars.", "error");
        return;
    }

    try {
        await apiRequest("/api/ratings/", "POST", {
            rated_user: ratedUserId,
            rating: selectedRating,
            comment: document.getElementById("ratingComment").value.trim(),
        });
        showRatingsMessage("Rating submitted successfully.", "success");
        selectedRating = 0;
        document.getElementById("ratingComment").value = "";
        renderRatingPicker();
        await loadRatings();
    } catch (error) {
        showRatingsMessage(error.message, "error");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    if (!getToken()) {
        window.location.href = "/login/";
        return;
    }
    const queryUserId = new URLSearchParams(window.location.search).get("user_id");
    if (queryUserId) {
        document.getElementById("ratedUserId").value = queryUserId;
        loadRatings();
    }
    renderRatingPicker();
    document.getElementById("loadRatings").addEventListener("click", loadRatings);
    document.getElementById("ratingForm").addEventListener("submit", submitRating);
});
