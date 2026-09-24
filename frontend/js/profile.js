let selectedRating = 0;

/* ---------- RENDER HELPERS ---------- */

function setText(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value || "—";
}

function setValue(id, value) {
    const el = document.getElementById(id);
    if (el) el.value = value || "";
}

function renderVerificationBadge(isVerified) {
    const badge = document.getElementById("verifiedBadge");

    if (!badge) {
        return;
    }

    badge.hidden = !isVerified;
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

/* ---------- LOAD PROFILE FROM API ---------- */

async function loadProfile() {
    const token = localStorage.getItem("helpnet_token");
    if (!token) {
        window.location.href = "/login/";
        return;
    }

    try {
        const res = await fetch("/api/auth/me/", {
            headers: { Authorization: `Bearer ${token}` },
        });

        if (res.status === 401) {
            localStorage.removeItem("helpnet_token");
            window.location.href = "/login/";
            return;
        }

        const payload = await res.json();
        const user = payload.data || payload;

        /* --- display section --- */
        setText("profileName", user.full_name);
        setText("profileEmail", user.email);
        setText("profilePhone", user.phone_number);
        setText("profileLocation", user.location);
        setText("profileRole", user.role);
        setText("profileBio", user.bio || "");

        renderVerificationBadge(user.is_verified);
        setText(
            "ratingSummary",
            `★ ${user.average_rating === null ? "0.0" : Number(user.average_rating).toFixed(1)} · ${user.rating_count || 0}`
        );
        const ratingsResponse = await apiRequest(`/api/ratings/users/${user.user_id}/`);
        renderExistingRatings(ratingsResponse.data || []);

        /* --- prefill edit form --- */
        setValue("profileFullName", user.full_name);
        setValue("profileBioInput", user.bio);
        setValue("profileLocationInput", user.location);
        setValue("profileDobInput", user.date_of_birth);
        setValue("profileGenderInput", user.gender);
        document.getElementById("showPhone").checked = !!user.is_phone_visible;
        document.getElementById("showEmail").checked = !!user.is_email_visible;
        document.getElementById("showLocation").checked = !!user.is_location_visible;
        document.getElementById("showDob").checked = !!user.is_date_of_birth_visible;

        /* --- profile picture, if set --- */
        if (user.profile_picture) {
            const avatar = document.getElementById("profileAvatar");
            if (avatar) {
                avatar.innerHTML = "";
                const img = document.createElement("img");
                img.src = user.profile_picture;
                img.alt = "Profile picture";
                img.className = "profile-avatar-image";
                avatar.appendChild(img);
            }
        }
    } catch (err) {
        console.error("Failed to load profile:", err);
    }
}

/* ---------- SAVE PROFILE ---------- */

async function saveProfile(event) {
    event.preventDefault();

    const token = localStorage.getItem("helpnet_token");
    const form = event.target;
    const formData = new FormData(form);
    const msg = document.getElementById("profileFormMessage");
    formData.set(
    "is_phone_visible",
    document.getElementById("showPhone").checked
    );

    formData.set(
       "is_email_visible",
      document.getElementById("showEmail").checked
    );

    formData.set(
      "is_location_visible",
       document.getElementById("showLocation").checked
    );

    formData.set(
      "is_date_of_birth_visible",
      document.getElementById("showDob").checked
    );

    try {
        const res = await fetch("/api/auth/me/", {
            method: "PATCH",
            headers: { Authorization: `Bearer ${token}` },
            body: formData,   // FormData works because of profile_picture
        });

        const payload = await res.json();

        if (res.ok) {
            if (msg) {
                msg.textContent = "প্রোফাইল সংরক্ষণ করা হয়েছে।";
                msg.style.color = "green";
            }
            loadProfile();
        } else {
            if (msg) {
                msg.textContent =
                    typeof payload.message === "string"
                        ? payload.message
                        : JSON.stringify(payload.message);
                msg.style.color = "red";
            }
        }
    } catch (err) {
        console.error(err);
        if (msg) {
            msg.textContent = "সংযোগ ব্যর্থ হয়েছে।";
            msg.style.color = "red";
        }
    }
}

/* ---------- INIT ---------- */

document.addEventListener("DOMContentLoaded", () => {
    loadProfile();

    document.getElementById("profileForm")
        ?.addEventListener("submit", saveProfile);
});
