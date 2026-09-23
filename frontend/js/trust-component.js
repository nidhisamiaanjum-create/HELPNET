/* Reuse in blood, marketplace, and volunteer modules with renderTrustComponent(container, data). */
function renderTrustComponent(container, data) {
    if (!container) return;
    const status = data.verificationStatus === "approved";
    const ratingCount = Number(data.ratingCount) || 0;
    const average = ratingCount ? Number(data.averageRating || 0).toFixed(1) : "এখনও নেই";
    container.className = "trust-component";
    container.replaceChildren();
    const label = document.createElement("strong"); label.textContent = "ট্রাস্ট";
    const verification = document.createElement("span"); verification.className = status ? "verified-badge" : "status status-pending"; verification.textContent = status ? "✓ যাচাইকৃত" : "যাচাই হয়নি";
    const rating = document.createElement("p"); rating.textContent = `★ ${average} · ${ratingCount}টি রেটিং`;
    container.append(label, verification, rating);
}
