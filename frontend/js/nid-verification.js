/* ============================================================
   HELPNET — NID verification page (S2-T23)
   Matches templates: id="nidVerificationForm", #documentType,
   #verificationDocument, #verificationStatus, #rejectionReason
   ============================================================ */

const NID_RULES = {
    allowedTypes: ["image/jpeg", "image/png", "application/pdf"],
    maxBytes: 5 * 1024 * 1024,
    allowedDocTypes: ["nid", "passport", "birth_certificate"]
};

/* Status -> CSS class + Bengali label.
   Add i18n keys here later if you want language switching on this page. */
const STATUS_MAP = {
    unverified: { cls: "status-unverified", label: "যাচাই করা হয়নি" },
    pending:    { cls: "status-pending",    label: "অপেক্ষমাণ"        },
    approved:   { cls: "status-approved",   label: "যাচাইকৃত"        },
    rejected:   { cls: "status-rejected",   label: "প্রত্যাখ্যাত"     }
};

/* ------------------------------------------------------------
   MOCK STATE — replace bodies of the two stubs when API is ready
   ------------------------------------------------------------ */
let MOCK_STATE = {
    status: "unverified",     // unverified | pending | approved | rejected
    documentType: "nid",
    rejectionReason: "",
    submittedAt: null
};

/* ------------------------------------------------------------
   API STUBS
   ------------------------------------------------------------ */
async function fetchVerificationStatus() {
    // LATER:
    // const res = await fetch("/api/verification/status/", {
    //     headers: { Authorization: "Bearer " + localStorage.getItem("helpnet_token") }
    // });
    // return res.json();
    return { ...MOCK_STATE };
}

async function submitVerification(docType, file) {
    // LATER:
    // const fd = new FormData();
    // fd.append("document_type", docType);
    // fd.append("document", file);
    // const res = await fetch("/api/verification/submit/", {
    //     method: "POST",
    //     headers: { Authorization: "Bearer " + localStorage.getItem("helpnet_token") },
    //     body: fd
    // });
    // if (!res.ok) throw new Error("upload_failed");
    // return res.json();

    // Mock success:
    MOCK_STATE = {
        status: "pending",
        documentType: docType,
        rejectionReason: "",
        submittedAt: new Date().toISOString()
    };
    return { ...MOCK_STATE };
}

/* ------------------------------------------------------------
   VALIDATION
   ------------------------------------------------------------ */
function validate(docType, file) {
    if (!NID_RULES.allowedDocTypes.includes(docType)) return "নথির ধরন সঠিক নয়।";
    if (!file) return "অনুগ্রহ করে একটি ফাইল নির্বাচন করুন।";
    if (!NID_RULES.allowedTypes.includes(file.type)) return "শুধুমাত্র JPG, PNG অথবা PDF গ্রহণযোগ্য।";
    if (file.size > NID_RULES.maxBytes) return "ফাইলের আকার ৫ MB এর বেশি।";
    return null;
}

/* ------------------------------------------------------------
   RENDER
   ------------------------------------------------------------ */
function renderStatus(state) {
    const statusEl = document.getElementById("verificationStatus");
    const rejectEl = document.getElementById("rejectionReason");
    const form     = document.getElementById("nidVerificationForm");
    if (!statusEl) return;

    const cfg = STATUS_MAP[state.status] || STATUS_MAP.unverified;

    // Reset classes then apply the correct one
    statusEl.className = "status " + cfg.cls;
    statusEl.textContent = cfg.label;

    // Rejection reason
    if (state.status === "rejected" && state.rejectionReason) {
        rejectEl.hidden = false;
        rejectEl.textContent = "কারণ: " + state.rejectionReason;
    } else {
        rejectEl.hidden = true;
        rejectEl.textContent = "";
    }

    // Hide form if approved or pending (nothing to submit)
    if (form) {
        const canSubmit = state.status === "unverified" || state.status === "rejected";
        form.hidden = !canSubmit;
    }
}

/* ------------------------------------------------------------
   FORM WIRING
   ------------------------------------------------------------ */
function initForm() {
    const form     = document.getElementById("nidVerificationForm");
    const docType  = document.getElementById("documentType");
    const fileIn   = document.getElementById("verificationDocument");
    if (!form || !docType || !fileIn) return;

    // Inline error element (created on demand — your HTML has none)
    let errorEl = document.getElementById("nidFormError");
    if (!errorEl) {
        errorEl = document.createElement("p");
        errorEl.id = "nidFormError";
        errorEl.className = "form-error";
        errorEl.hidden = true;
        form.insertBefore(errorEl, form.querySelector("button"));
    }

    function showError(msg) {
        if (!msg) { errorEl.hidden = true; errorEl.textContent = ""; return; }
        errorEl.hidden = false;
        errorEl.textContent = msg;
    }

    // Live validation on file pick
    fileIn.addEventListener("change", function () {
        const err = validate(docType.value, fileIn.files[0]);
        showError(err);
    });

    form.addEventListener("submit", async function (e) {
        e.preventDefault();
        showError(null);

        const file = fileIn.files[0];
        const err = validate(docType.value, file);
        if (err) { showError(err); return; }

        const btn = form.querySelector("button");
        const originalLabel = btn.textContent;
        btn.disabled = true;
        btn.textContent = "পাঠানো হচ্ছে…";

        try {
            const next = await submitVerification(docType.value, file);
            MOCK_STATE = next;
            renderStatus(next);
        } catch (ex) {
            showError("আপলোড ব্যর্থ হয়েছে। আবার চেষ্টা করুন।");
        } finally {
            btn.disabled = false;
            btn.textContent = originalLabel;
        }
    });
}

/* ------------------------------------------------------------
   BOOT
   ------------------------------------------------------------ */
document.addEventListener("DOMContentLoaded", async function () {
    // Optional auth guard — only runs if auth.js is loaded on this page
    if (typeof requireLogin === "function" && !requireLogin()) return;

    const state = await fetchVerificationStatus();
    renderStatus(state);
    initForm();
});