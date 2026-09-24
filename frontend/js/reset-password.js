document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("resetPasswordForm");
    const newPassword = document.getElementById("newPassword");
    const confirmPassword = document.getElementById("confirmPassword");
    const message = document.getElementById("resetPasswordMessage");
    const button = document.getElementById("resetPasswordButton");

    if (!form) {
        return;
    }

    const params = new URLSearchParams(window.location.search);
    const uid = params.get("uid");
    const token = params.get("token");

    if (!uid || !token) {
        showMessage(
            "পাসওয়ার্ড রিসেট লিংকটি অসম্পূর্ণ বা অবৈধ।",
            "red"
        );

        button.disabled = true;
        return;
    }

    form.addEventListener("submit", async function (event) {
        event.preventDefault();

        const password = newPassword.value;
        const confirmation = confirmPassword.value;

        if (password.length < 8) {
            showMessage(
                "পাসওয়ার্ড কমপক্ষে ৮ অক্ষরের হতে হবে।",
                "red"
            );
            return;
        }

        if (password !== confirmation) {
            showMessage(
                "দুইটি পাসওয়ার্ড একই নয়।",
                "red"
            );
            return;
        }

        message.hidden = true;
        message.textContent = "";

        button.disabled = true;
        button.textContent = "পরিবর্তন করা হচ্ছে...";

        try {
            const response = await fetch(
                "/api/auth/password-reset-confirm/",
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        uid: uid,
                        token: token,
                        new_password: password
                    })
                }
            );

            const payload = await response.json();

            if (!response.ok) {
                let errorMessage =
                    "পাসওয়ার্ড পরিবর্তন করা যায়নি।";

                if (typeof payload.message === "string") {
                    errorMessage = payload.message;
                }

                showMessage(errorMessage, "red");
                return;
            }

            showMessage(
                payload.message ||
                "পাসওয়ার্ড সফলভাবে পরিবর্তন হয়েছে।",
                "green"
            );

            form.reset();

            setTimeout(function () {
                window.location.href = "/login/";
            }, 1500);

        } catch (error) {
            console.error(
                "Password reset failed:",
                error
            );

            showMessage(
                "সংযোগ ব্যর্থ হয়েছে। আবার চেষ্টা করুন।",
                "red"
            );

        } finally {
            button.disabled = false;
            button.textContent = "পাসওয়ার্ড পরিবর্তন করুন";
        }
    });

    function showMessage(text, color) {
        message.hidden = false;
        message.textContent = text;
        message.style.color = color;
    }
});