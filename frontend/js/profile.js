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

function renderVerificationBadge(status) {
    const badge = document.getElementById("verifiedBadge");
    if (badge) badge.hidden = status !== "approved";
}

function renderRatingStars() {
    const picker = document.getElementById("starPicker");
    if (!picker) return;
    picker.replaceChildren();
    for (let score = 1; score <= 5; score += 1) {
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = "★";
        button.className = score <= selectedRating ? "selected" : "";
        button.setAttribute("aria-label", `${score} তারকা`);
        button.addEventListener("click", () => {
            selectedRating = score;
            renderRatingStars();
        });
        picker.appendChild(button);
    }
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

        renderVerificationBadge(user.is_verified ? "approved" : "pending");

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
    renderRatingStars();

    const trust = document.getElementById("trust-component");
    if (trust && typeof renderTrustComponent === "function") {
        renderTrustComponent(trust, {
            userId: "demo-user",
            verificationStatus: "approved",
            averageRating: 4.5,
            ratingCount: 12,
        });
    }

    document.getElementById("submitRating")
        ?.addEventListener("click", prepareRatingSubmission);

    document.getElementById("profileForm")
        ?.addEventListener("submit", saveProfile);
});

function prepareRatingSubmission() {
    if (!selectedRating) {
        alert("অনুগ্রহ করে একটি রেটিং নির্বাচন করুন। ");
        return;
    }
    alert("রেটিং প্রস্তুত করা হয়েছে। API সংযোগ পরে যোগ করা হবে। ");
}
