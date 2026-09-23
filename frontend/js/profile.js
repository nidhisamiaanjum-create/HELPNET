let selectedRating = 0;

/* ---------- RENDER HELPERS ---------- */

function setText(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value || "—";
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
        const res = await fetch("/api/users/me/", {
            headers: { Authorization: `Bearer ${token}` },
        });

        if (res.status === 401) {
            localStorage.removeItem("helpnet_token");
            window.location.href = "/login/";
            return;
        }

        const payload = await res.json();
        const user = payload.data || payload;

        setText("profileName", user.full_name);
        setText("profileEmail", user.email);
        setText("profilePhone", user.phone_number);
        setText("profileLocation", user.location);
        setText("profileRole", user.role);
        setText("profileBio", user.bio || "");

        renderVerificationBadge(user.verification_status);

        // Pre-fill the edit form
        const setVal = (id, v) => {
            const el = document.getElementById(id);
            if (el) el.value = v || "";
        };
        setVal("profileFullName", user.full_name);
        setVal("profileBioInput", user.bio);
        setVal("profileLocationInput", user.location);
        setVal("profileDobInput", user.date_of_birth);
        setVal("profileGenderInput", user.gender);
    } catch (err) {
        console.error("Failed to load profile:", err);
    }
}

/* ---------- PROFILE UPDATE ---------- */

async function saveProfile(event) {
    event.preventDefault();

    const token = localStorage.getItem("helpnet_token");
    const form = event.target;
    const formData = new FormData(form);
    const body = Object.fromEntries(formData.entries());

    try {
        const res = await fetch("/api/users/me/", {
            method: "PATCH",
            headers: {
                Authorization: `Bearer ${token}`,
                "Content-Type": "application/json",
            },
            body: JSON.stringify(body),
        });

        const payload = await res.json();
        const msg = document.getElementById("profileFormMessage");

        if (res.ok) {
            if (msg) msg.textContent = "প্রোফাইল সংরক্ষণ করা হয়েছে।";
            loadProfile();
        } else {
            if (msg) msg.textContent = JSON.stringify(payload.message);
        }
    } catch (err) {
        console.error(err);
    }
}

/* ---------- INIT ---------- */

document.addEventListener("DOMContentLoaded", () => {
    loadProfile();
    renderRatingStars();

    const trust = document.getElementById("trust-component");
    if (trust) {
        renderTrustComponent(trust, {
            userId: "demo-user",
            verificationStatus: "approved",
            averageRating: 4.5,
            ratingCount: 12,
        });
    }

    document.getElementById("submitRating")?.addEventListener("click", prepareRatingSubmission);
    document.getElementById("profileForm")?.addEventListener("submit", saveProfile);
});

function prepareRatingSubmission() {
    if (!selectedRating) {
        alert("অনুগ্রহ করে একটি রেটিং নির্বাচন করুন। ");
        return;
    }
    alert("রেটিং প্রস্তুত করা হয়েছে। API সংযোগ পরে যোগ করা হবে। ");
}