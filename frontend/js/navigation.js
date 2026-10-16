/* Return to the previous HELPNET page when one is available. The link's href
   remains the safe parent-page fallback for direct opens and external referrers. */
document.addEventListener("click", event => {
    const target = event.target instanceof Element ? event.target : null;
    const link = target?.closest("a[data-smart-back]");
    if (!link || event.defaultPrevented || event.button !== 0 ||
        event.metaKey || event.ctrlKey || event.shiftKey || event.altKey ||
        (link.target && link.target !== "_self")) {
        return;
    }

    let referrer;
    try {
        referrer = new URL(document.referrer);
    } catch {
        return;
    }

    if (referrer.origin === window.location.origin && window.history.length > 1) {
        event.preventDefault();
        window.history.back();
    }
});
