console.log("🔥 NEW PROFILE.JS LOADED 🔥");
let selectedRating = 0;
let profileRatings = [];
let currentProfileRole = "";
let currentProfileGender = "";

/* ---------- RENDER HELPERS ---------- */

function setText(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value || "—";
}

function setValue(id, value) {
    const el = document.getElementById(id);
    if (el) el.value = value || "";
}

function translateProfileValue(value) {
    const normalized = String(value || "").trim().toLowerCase().replace(/[\s-]+/g, "_");
    const key = {
        male: "male",
        female: "female",
        other: "other",
        citizen: "profileRoleCitizen",
        ngo: "profileRoleNGO",
        donor: "profileRoleDonor",
        farmer: "profileRoleFarmer",
        volunteer: "profileRoleVolunteer",
        blood_donor: "profileRoleBloodDonor",
        admin: "profileRoleAdmin",
    }[normalized];
    return key ? t(key) : value;
}

function renderTranslatedProfileValues() {
    setText("profileRole", translateProfileValue(currentProfileRole));
    setText("infoGender", translateProfileValue(currentProfileGender));
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
    profileRatings = Array.isArray(ratings) ? ratings : [];
    container.replaceChildren();
    const heading = document.createElement("h3");
    heading.textContent = t("existingRatings");
    container.appendChild(heading);
    if (!profileRatings.length) {
        const empty = document.createElement("p");
        empty.textContent = t("noRatingsYet");
        container.appendChild(empty);
        return;
    }
    profileRatings.forEach((item) => {
        const article = document.createElement("article");
        article.className = "rating-item";
        const title = document.createElement("strong");
        title.textContent = `${item.rater_name} · ${"★".repeat(item.rating)}`;
        const comment = document.createElement("p");
        comment.textContent = item.comment || t("noComment");
        article.append(title, comment);
        container.appendChild(article);
    });
}


function setupProfileMode(isPublicProfile) {
     document.body.classList.toggle("public-profile", isPublicProfile);
    if (!isPublicProfile) {
        return;
    }

    console.log("PUBLIC PROFILE MODE");

    // Hide NID Verification / Verify Now
    const verification = document.getElementById("verificationAction");
    if (verification) {
        verification.hidden = true;
    }

    // Hide Edit Profile section
    const editProfile = document.getElementById("edit-profile");
    if (editProfile) {
        editProfile.hidden = true;
    }

    // Hide Edit Profile button/link
    const editLink = document.getElementById("editProfileLink");
    if (editLink) {
        editLink.hidden = true;
    }

    // Hide Settings
    document.querySelectorAll('a[href="/settings/"]').forEach((el) => {
        el.hidden = true;
    });

    // Hide profile picture upload/change
    const uploadLabel = document.querySelector(".profile-picture-upload");
    if (uploadLabel) {
        uploadLabel.hidden = true;
    }

    const uploadInput = document.getElementById("profilePictureInputTop");
    if (uploadInput) {
        uploadInput.disabled = true;
    }

    // Hide ALL "My Activities"
    const activities = document.querySelector(".profile-menu");
    if (activities) {
        activities.hidden = true;
    }

    // Hide entire profile actions EXCEPT logout
    const profileActions = document.getElementById("profileActions");

    if (profileActions) {
        profileActions.querySelectorAll("a, button").forEach((element) => {
            if (element.id === "logoutButton") {
                element.hidden = false;
            } else {
                element.hidden = true;
            }
        });
    }

    // Make sure logout stays visible
    const logoutButton = document.getElementById("logoutButton");
    if (logoutButton) {
        logoutButton.hidden = false;
    }
}

function setupRatingForm(isPublicProfile, targetUserId) {
    const section = document.getElementById("rateUserSection");
    const picker = document.getElementById("profileStarPicker");
    const submitButton = document.getElementById("submitProfileRating");
    const commentInput = document.getElementById("profileRatingComment");
    const message = document.getElementById("ratingMessage");

    if (!section || !picker || !submitButton) {
        return;
    }

    // Only show rating form on another user's profile
    section.hidden = !isPublicProfile;

    if (!isPublicProfile) {
        return;
    }

    // Star selection
    picker.querySelectorAll("button").forEach((button) => {
        button.addEventListener("click", () => {
            selectedRating = Number(button.dataset.rating);

            picker.querySelectorAll("button").forEach((star) => {
                star.classList.toggle(
                    "selected",
                    Number(star.dataset.rating) <= selectedRating
                );
            });
        });
    });

    // Submit rating
    submitButton.addEventListener("click", async () => {
        if (!selectedRating) {
            message.textContent = t("ratingSelectRequired");
            return;
        }

        submitButton.disabled = true;
        message.textContent = t("ratingSubmitting");

        try {
            const response = await fetch("/api/ratings/create/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${localStorage.getItem("helpnet_token")}`,
                },
                body: JSON.stringify({
                    rated_user: targetUserId,
                    rating: selectedRating,
                    comment: commentInput.value.trim(),
                }),
            });

            const payload = await response.json();

            if (!response.ok) {
                message.textContent =
                    payload.message || t("ratingSubmitFailed");
                return;
            }

            message.textContent = t("ratingSubmitSuccess");

            // Reset form
            selectedRating = 0;
            commentInput.value = "";

            picker.querySelectorAll("button").forEach((star) => {
                star.classList.remove("selected");
            });

            // Reload ratings
            const ratingsResponse = await apiRequest(
                `/api/ratings/users/${targetUserId}/`
            );

            renderExistingRatings(ratingsResponse.data || []);

        } catch (error) {
            console.error("Rating error:", error);
            message.textContent = t("connectionFailed");
        } finally {
            submitButton.disabled = false;
        }
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
        const targetUserId = new URLSearchParams(window.location.search).get("user_id");
        const isPublicProfile = !!targetUserId;
        const profileUrl = isPublicProfile
            ? `/api/users/${targetUserId}/`
            : "/api/auth/me/";
        const res = await fetch(profileUrl, {
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
        currentProfileRole = user.role;
        setText("profileBio", user.bio || "");
        setText("infoFullName", user.full_name);
setText("infoEmail", user.email);
setText("infoPhone", user.phone_number);
setText("infoLocation", user.location);
setText("infoDob", user.date_of_birth);
currentProfileGender = user.gender;
renderTranslatedProfileValues();

        renderVerificationBadge(user.is_verified);
        setText(
            "ratingSummary",
            `★ ${user.average_rating == null ? "—" : Number(user.average_rating).toFixed(1)} · ${user.rating_count || 0}`
        );
        const ratingsResponse = await apiRequest(`/api/ratings/users/${user.user_id}/`);
        renderExistingRatings(ratingsResponse.data || []);

        setupProfileMode(isPublicProfile);
        setupRatingForm(isPublicProfile, targetUserId);

        /* --- prefill edit form --- */
        if (isPublicProfile) return;
        setValue("profileFullName", user.full_name);
        setValue("profileBioInput", user.bio);
        setValue("profileLocationInput", user.location);
        setValue("profileDobInput", user.date_of_birth);
        setValue("profileGenderInput", user.gender);
        const visibilityFields = {
            showPhone: "is_phone_visible",
            showEmail: "is_email_visible",
            showLocation: "is_location_visible",
            showDob: "is_date_of_birth_visible",
        };
        Object.entries(visibilityFields).forEach(([id, field]) => {
            const input = document.getElementById(id);
            if (input) input.checked = !!user[field];
        });

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
    const visibilityFields = {
        showPhone: "is_phone_visible",
        showEmail: "is_email_visible",
        showLocation: "is_location_visible",
        showDob: "is_date_of_birth_visible",
    };
    Object.entries(visibilityFields).forEach(([id, field]) => {
        const input = document.getElementById(id);
        if (input) formData.set(field, input.checked);
    });

    try {
        const res = await fetch("/api/auth/me/", {
            method: "PATCH",
            headers: { Authorization: `Bearer ${token}` },
            body: formData,   // FormData works because of profile_picture
        });

        const payload = await res.json();

        if (res.ok) {
            if (msg) {
                msg.textContent = t("profileSaved");
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
            msg.textContent = t("connectionFailed");
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

document.addEventListener("helpnet:languagechange", () => {
    renderExistingRatings(profileRatings);
    renderTranslatedProfileValues();
});
