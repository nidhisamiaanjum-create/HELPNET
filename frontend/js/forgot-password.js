document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("forgotPasswordForm");
    const emailInput = document.getElementById("email");
    const message = document.getElementById("forgotPasswordMessage");
    const button = document.getElementById("forgotPasswordButton");

    if (!form) {
        return;
    }

    form.addEventListener("submit", async function (event) {
        event.preventDefault();

        const email = emailInput.value.trim();

        message.hidden = true;
        message.textContent = "";

        if (!email) {
            showMessage("অনুগ্রহ করে আপনার ইমেইল দিন।", "red");
            return;
        }

        button.disabled = true;
        button.textContent = "পাঠানো হচ্ছে...";

        try {
            const response = await fetch(
                "/api/auth/password-reset/",
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        email: email
                    })
                }
            );

            const payload = await response.json();

            if (!response.ok) {
                let errorMessage = "পাসওয়ার্ড রিসেট অনুরোধ ব্যর্থ হয়েছে।";

                if (typeof payload.message === "string") {
                    errorMessage = payload.message;
                }

                showMessage(errorMessage, "red");
                return;
            }

            showMessage(
                payload.message ||
                "যদি এই ইমেইলের অ্যাকাউন্ট থাকে, তাহলে একটি রিসেট লিংক পাঠানো হয়েছে।",
                "green"
            );

            form.reset();

        } catch (error) {
            console.error(
                "Password reset request failed:",
                error
            );

            showMessage(
                "সংযোগ ব্যর্থ হয়েছে। আবার চেষ্টা করুন।",
                "red"
            );

        } finally {
            button.disabled = false;
            button.textContent = "Reset Password";
        }
    });

    function showMessage(text, color) {
        message.hidden = false;
        message.textContent = text;
        message.style.color = color;
    }
});