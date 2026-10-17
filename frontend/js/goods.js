const GOODS_DISCLAIMER = "HELPNET does not handle payments and does not guarantee item condition. Exchanges are arranged directly between users. HELPNET does not process or guarantee payments. HELPNET does not guarantee item condition, authenticity, ownership, or quality. Buyers and sellers arrange exchanges directly between themselves, and users should inspect items carefully before agreeing to any exchange.";

function goodsShowMessage(elementId, message, type = "") {
    const element = document.getElementById(elementId);
    if (!element) return;
    element.textContent = message;
    element.className = `form-message ${type}`;
}

function goodsAddText(parent, tag, text, className = "") {
    const element = document.createElement(tag);
    element.textContent = text;
    if (className) element.className = className;
    parent.appendChild(element);
    return element;
}

function goodsListingId() {
    return new URLSearchParams(window.location.search).get("listing_id");
}

function goodsApiError(data, fallback) {
    if (!data || !data.message) return fallback;
    if (typeof data.message === "string") return data.message;
    return Object.values(data.message).flat().join(" ") || fallback;
}

async function goodsRequest(path, method = "GET", body = null) {
    if (!(body instanceof FormData)) return apiRequest(path, method, body);
    let response;
    try {
        response = await fetch(`${API_BASE}${path}`, {
            method,
            headers: {Authorization: `Bearer ${getToken()}`},
            body,
        });
    } catch (error) {
        throw new Error("Could not connect to the HELPNET server.");
    }
    const data = await response.json().catch(() => null);
    if (!response.ok) throw new Error(goodsApiError(data, "Request failed. Please try again."));
    return data;
}

async function loadGoodsList() {
    const target = document.getElementById("goodsList");
    if (!target) return;
    try {
        const response = await goodsRequest("/api/goods/listings/");
        target.replaceChildren();
        if (!response.data.length) {
            goodsAddText(target, "p", "No available goods listings.", "hint");
            return;
        }
        response.data.forEach(listing => {
            const card = document.createElement("article");
            card.className = "admin-item";
            goodsAddText(card, "h2", listing.title);
            goodsAddText(card, "p", `Condition: ${listing.condition}`);
            goodsAddText(card, "p", `Asking price: ${listing.asking_price}`);
            goodsAddText(card, "p", `Location: ${listing.location}`);
            if (listing.image_url) {
                const image = document.createElement("img");
                image.src = listing.image_url;
                image.alt = listing.title;
                image.loading = "lazy";
                image.style.maxWidth = "100%";
                image.style.maxHeight = "280px";
                card.appendChild(image);
                card.appendChild(document.createElement("br"));
                card.appendChild(document.createElement("br"));
            }
            const details = document.createElement("a");
            details.className = "small-btn";
            details.href = `/goods-details/?listing_id=${encodeURIComponent(listing.id)}`;
            details.textContent =
                typeof t === "function" ? t("details") : "Details";
            card.appendChild(details);
            target.appendChild(card);
        });
    } catch (error) {
        goodsShowMessage("goodsMessage", error.message, "error");
    }
}

async function createGoodsListing(event) {
    event.preventDefault();
    const submitButton = event.currentTarget.querySelector('[type="submit"]');
    if (submitButton) submitButton.disabled = true;
    const formData = new FormData();
    formData.append("title", document.getElementById("goodsTitle").value.trim());
    formData.append("description", document.getElementById("goodsDescription").value.trim());
    formData.append("condition", document.getElementById("goodsCondition").value);
    formData.append("asking_price", document.getElementById("goodsPrice").value);
    formData.append("location", document.getElementById("goodsLocation").value.trim());
    const image = document.getElementById("goodsImage").files[0];
    if (image) {
        const acceptedTypes = ["image/jpeg", "image/png", "image/webp"];
        if (!acceptedTypes.includes(image.type)) {
            goodsShowMessage("goodsMessage", "Only JPG, PNG, and WebP images are allowed.", "error");
            if (submitButton) submitButton.disabled = false;
            return;
        }
        if (image.size > 5 * 1024 * 1024) {
            goodsShowMessage("goodsMessage", "Image size must not exceed 5 MB.", "error");
            if (submitButton) submitButton.disabled = false;
            return;
        }
    }
    if (image) formData.append("image", image);
    try {
        const response = await goodsRequest("/api/goods/listings/", "POST", formData);
        goodsShowMessage("goodsMessage", response.message || "Listing created.", "success");
        window.location.href = `/goods-details/?listing_id=${encodeURIComponent(response.data.id)}`;
    } catch (error) {
        goodsShowMessage("goodsMessage", error.message, "error");
    } finally {
        if (submitButton) submitButton.disabled = false;
    }
}

function renderSellerContact(container, contact) {
    goodsAddText(container, "h2", "Seller");
    goodsAddText(container, "p", contact.full_name);
    if (contact.location) goodsAddText(container, "p", `Location: ${contact.location}`);
    if (contact.phone_number) goodsAddText(container, "p", `Phone: ${contact.phone_number}`);
    if (contact.email) goodsAddText(container, "p", `Email: ${contact.email}`);
    if (!contact.phone_number && !contact.email) {
        goodsAddText(container, "p", "Contact details are shared only after a valid interest request is confirmed.", "hint");
    }
}

async function loadGoodsDetails() {
    const target = document.getElementById("goodsDetails");
    const listingId = goodsListingId();
    if (!listingId || !/^\d+$/.test(listingId)) {
        goodsShowMessage("goodsMessage", "This listing link is missing a valid listing ID.", "error");
        return;
    }
    try {
        const response = await goodsRequest(`/api/goods/listings/${encodeURIComponent(listingId)}/`);
        const listing = response.data;
        target.replaceChildren();
        goodsAddText(target, "h1", listing.title);
        goodsAddText(target, "p", listing.description);
        goodsAddText(target, "p", `Condition: ${listing.condition}`);
        goodsAddText(target, "p", `Asking price: ${listing.asking_price}`);
        goodsAddText(target, "p", `Location: ${listing.location}`);
        goodsAddText(target, "p", `Status: ${listing.status}`);
        if (listing.image_url) {
            const image = document.createElement("img");
            image.src = listing.image_url;
            image.alt = listing.title;
            image.style.maxWidth = "100%";
            image.style.maxHeight = "420px";
            target.appendChild(image);
        }
        renderSellerContact(target, listing.seller_contact);
        const ownerControls = document.getElementById("goodsOwnerControls");
        ownerControls.hidden = !listing.is_owner;
        document.getElementById("goodsStatus").value = listing.status;
        document.getElementById("goodsInterestControls").hidden = listing.is_owner || listing.status !== "Available";
        const interestButton = document.getElementById("goodsInterestButton");
        if (interestButton) {
            interestButton.disabled = Boolean(listing.user_has_interest);
            interestButton.textContent = listing.user_has_interest
                ? (typeof t === "function" ? t("interestSent") : "Interest sent")
                : (typeof t === "function" ? t("expressInterest") : "Express Interest");
        }
        const openChat = document.getElementById("goodsOpenChat");
        if (openChat) openChat.hidden = !listing.user_has_interest;
        if (listing.user_has_interest && openChat && !openChat.href) {
            const conversations = await goodsRequest("/api/goods/conversations/");
            const conversation = conversations.data.find(item => Number(item.listing_id) === Number(listing.id));
            if (conversation) openChat.href = conversation.url;
        }
        const ownerSection = document.getElementById("goodsInterestedUsersSection");
        if (ownerSection) {
            ownerSection.hidden = !listing.is_owner;
            if (listing.is_owner) await loadInterestedUsers(listing.id);
        }
        document.getElementById("goodsReportForm").dataset.listingId = listing.id;
        document.getElementById("goodsReportForm").hidden = listing.is_owner;
    } catch (error) {
        goodsShowMessage("goodsMessage", error.message, "error");
    }
}

async function expressGoodsInterest() {
    const listingId = goodsListingId();
    if (!listingId) return goodsShowMessage("goodsMessage", "This listing link is missing its ID.", "error");
    const button = document.getElementById("goodsInterestButton");
    if (button) button.disabled = true;
    try {
        const response = await goodsRequest(`/api/goods/listings/${encodeURIComponent(listingId)}/interest/`, "POST", {});
        goodsShowMessage("goodsMessage", response.message || "Interest sent.", "success");
        const openChat = document.getElementById("goodsOpenChat");
        if (openChat && response.data?.conversation_url) {
            openChat.href = response.data.conversation_url;
            openChat.hidden = false;
        }
        const button = document.getElementById("goodsInterestButton");
        if (button) {
            button.disabled = true;
            button.textContent = typeof t === "function" ? t("interestSent") : "Interest sent";
        }
        await loadGoodsDetails();
    } catch (error) {
        goodsShowMessage("goodsMessage", error.message, "error");
        if (button) button.disabled = false;
    }
}

async function loadInterestedUsers(listingId) {
    const target = document.getElementById("goodsInterestedUsers");
    if (!target) return;
    try {
        const response = await goodsRequest(`/api/goods/listings/${encodeURIComponent(listingId)}/interested-users/`);
        target.replaceChildren();
        if (!response.data.length) return goodsAddText(target, "p", "No one has expressed interest yet.", "hint");
        response.data.forEach(person => {
            const row = document.createElement("article");
            goodsAddText(row, "p", `${person.user_name} · ${new Date(person.created_at).toLocaleString()}`);
            const chat = document.createElement("a"); chat.className = "small-btn"; chat.href = person.conversation_url; chat.textContent = "Message";
            row.appendChild(chat); target.appendChild(row);
        });
    } catch (error) { goodsShowMessage("goodsMessage", error.message, "error"); }
}

async function updateGoodsStatus() {
    const listingId = goodsListingId();
    if (!listingId) return goodsShowMessage("goodsMessage", "This listing link is missing its ID.", "error");
    const button = document.getElementById("saveGoodsStatus");
    if (button) button.disabled = true;
    goodsShowMessage("goodsMessage", "Updating listing status…");
    try {
        const response = await goodsRequest(`/api/goods/listings/${encodeURIComponent(listingId)}/status/`, "PATCH", {
            status: document.getElementById("goodsStatus").value,
        });
        goodsShowMessage("goodsMessage", response.message || "Status updated.", "success");
        await loadGoodsDetails();
    } catch (error) {
        goodsShowMessage("goodsMessage", error.message, "error");
    } finally {
        if (button) button.disabled = false;
    }
}

async function reportGoodsListing(event) {
    event.preventDefault();
    const listingId = event.currentTarget.dataset.listingId || goodsListingId();
    if (!listingId) return goodsShowMessage("goodsReportMessage", "This listing link is missing its ID.", "error");
    try {
        const response = await goodsRequest(`/api/goods/listings/${encodeURIComponent(listingId)}/reports/`, "POST", {
            reason: document.getElementById("goodsReportReason").value.trim(),
            description: document.getElementById("goodsReportDescription").value.trim(),
        });
        event.currentTarget.reset();
        goodsShowMessage("goodsReportMessage", response.message || "Listing reported.", "success");
    } catch (error) {
        goodsShowMessage("goodsReportMessage", error.message, "error");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    if (!requireLogin()) return;
    document.getElementById("goodsList") && loadGoodsList();
    document.getElementById("goodsCreateForm")?.addEventListener("submit", createGoodsListing);
    if (document.getElementById("goodsDetails")) loadGoodsDetails();
    document.getElementById("goodsInterestButton")?.addEventListener("click", expressGoodsInterest);
    document.getElementById("saveGoodsStatus")?.addEventListener("click", updateGoodsStatus);
    document.getElementById("goodsReportForm")?.addEventListener("submit", reportGoodsListing);
});
