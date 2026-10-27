
/**
 * HELPNET Admin Dashboard
 * File: frontend/js/admin-dashboard.js
 *
 * Supports:
 * - Admin / staff / superuser detection
 * - JWT authentication
 * - Current-user verification
 * - Logout
 * - Admin navigation
 * - Optional dashboard statistics
 */

"use strict";

document.addEventListener("DOMContentLoaded", initAdminDashboard);

async function initAdminDashboard() {
    console.log("HELPNET Admin Dashboard JS loaded");

    const TOKEN_KEY = "helpnet_token";
    const USER_KEY = "helpnet_user";
    const LOGIN_URL = "/login/";
    const DASHBOARD_URL = "/admin-dashboard/";

    const token = localStorage.getItem(TOKEN_KEY);
    let user = getStoredUser();

    // 1. Authentication check
    if (!token) {
        redirectToLogin();
        return;
    }

    // 2. Verify the saved user using the backend
    // The backend response is preferred over stale localStorage data.
    try {
        const response = await fetch("/api/auth/me/", {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${token}`,
                "Accept": "application/json"
            }
        });

        if (response.status === 401 || response.status === 403) {
            clearSession();
            redirectToLogin();
            return;
        }

        if (response.ok) {
            const result = await response.json();
            const serverUser = result.data || result.user || result;

            if (serverUser && typeof serverUser === "object") {
                user = {
                    ...user,
                    ...serverUser
                };

                localStorage.setItem(USER_KEY, JSON.stringify(user));
            }
        } else {
            console.warn(
                "Could not verify user through /api/auth/me/:",
                response.status
            );
        }
    } catch (error) {
        console.error("Unable to verify current user:", error);
        showMessage(
            "Could not verify your session. Check your internet or server connection.",
            "error"
        );
        return;
    }

    // 3. Admin permission check
    if (!isAdmin(user)) {
        showMessage("Admin access required.", "error");
        window.location.replace("/dashboard/");
        return;
    }

    console.log("HELPNET ADMIN STATUS: true");
    console.log("HELPNET ADMIN USER:", user);

    // 4. Initialize the dashboard
    renderAdminIdentity(user);
    setupNavigation();
    setupLogout();
    setupMobileMenu();
    setupRefresh();
    setupConfiguredStats();

    document.documentElement.classList.add("admin-dashboard-ready");

    console.log("HELPNET Admin Dashboard initialized successfully");


    // -------------------------------
    // Helper functions
    // -------------------------------

    function getStoredUser() {
        try {
            const saved = localStorage.getItem(USER_KEY);
            return saved ? JSON.parse(saved) : {};
        } catch (error) {
            console.error("Invalid saved user data:", error);
            return {};
        }
    }

    function isAdmin(currentUser) {
        if (!currentUser) return false;

        const role = String(currentUser.role || "")
            .trim()
            .toLowerCase()
            .replace(/[\s-]+/g, "_");

        return (
            currentUser.is_superuser === true ||
            currentUser.is_staff === true ||
            role === "admin"
        );
    }

    function clearSession() {
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(USER_KEY);
        localStorage.removeItem("refreshToken");
        localStorage.removeItem("helpnet_refresh");
    }

    function redirectToLogin() {
        if (window.location.pathname !== LOGIN_URL) {
            window.location.replace(LOGIN_URL);
        }
    }

    function showMessage(message, type = "info") {
        let box = document.getElementById("adminMessage");

        if (!box) {
            box = document.createElement("div");
            box.id = "adminMessage";
            box.setAttribute("role", "status");
            box.style.cssText = `
                position: fixed;
                top: 16px;
                right: 16px;
                z-index: 99999;
                max-width: 360px;
                padding: 12px 18px;
                border-radius: 10px;
                background: #ffffff;
                color: #263238;
                box-shadow: 0 4px 18px rgba(0,0,0,.15);
                font-size: 14px;
            `;
            document.body.appendChild(box);
        }

        box.textContent = message;
        box.dataset.type = type;
    }

    function renderAdminIdentity(currentUser) {
        const name =
            currentUser.full_name ||
            currentUser.username ||
            "Admin";

        const email = currentUser.email || "";

        // Update elements only when they exist in the HTML.
        const nameSelectors = [
            "#adminName",
            "#adminUserName",
            "[data-admin-name]"
        ];

        const emailSelectors = [
            "#adminEmail",
            "[data-admin-email]"
        ];

        nameSelectors.forEach(selector => {
            document.querySelectorAll(selector).forEach(element => {
                element.textContent = name;
            });
        });

        emailSelectors.forEach(selector => {
            document.querySelectorAll(selector).forEach(element => {
                element.textContent = email;
            });
        });

        document.querySelectorAll("[data-admin-role]").forEach(element => {
            element.textContent = "Administrator";
        });
    }

    function setupNavigation() {
        const currentPath = window.location.pathname.replace(/\/+$/, "");

        document.querySelectorAll(
            ".admin-sidebar a, .admin-nav a, [data-admin-nav]"
        ).forEach(link => {
            const href = link.getAttribute("href");
            if (!href || href.startsWith("#")) return;

            try {
                const linkPath = new URL(href, window.location.origin)
                    .pathname.replace(/\/+$/, "");

                if (linkPath === currentPath) {
                    link.classList.add("active");
                    link.setAttribute("aria-current", "page");
                } else {
                    link.classList.remove("active");
                    link.removeAttribute("aria-current");
                }
            } catch (error) {
                console.warn("Invalid navigation link:", href);
            }
        });
    }

    function setupLogout() {
        const logoutButtons = document.querySelectorAll(
            "#logoutButton, #adminLogout, [data-admin-logout]"
        );

        logoutButtons.forEach(button => {
            button.addEventListener("click", async event => {
                event.preventDefault();

                button.disabled = true;

                try {
                    const currentToken = localStorage.getItem(TOKEN_KEY);

                    // Attempt backend logout if the endpoint is available.
                    if (currentToken) {
                        await fetch("/api/auth/logout/", {
                            method: "POST",
                            headers: {
                                "Authorization": `Bearer ${currentToken}`,
                                "Content-Type": "application/json",
                                "Accept": "application/json"
                            },
                            body: JSON.stringify({
                                refresh: localStorage.getItem("refreshToken")
                            })
                        });
                    }
                } catch (error) {
                    console.warn(
                        "Backend logout request failed; clearing local session.",
                        error
                    );
                } finally {
                    clearSession();
                    window.location.replace(LOGIN_URL);
                }
            });
        });
    }

    function setupMobileMenu() {
        const toggle = document.querySelector(
            "#adminMenuToggle, #sidebarToggle, [data-admin-menu-toggle]"
        );

        const sidebar = document.querySelector(
            "#adminSidebar, .admin-sidebar"
        );

        if (!toggle || !sidebar) return;

        toggle.addEventListener("click", () => {
            const isOpen = sidebar.classList.toggle("open");
            toggle.setAttribute("aria-expanded", String(isOpen));
        });
    }

    function setupRefresh() {
        document.querySelectorAll(
            "#refreshDashboard, [data-admin-refresh]"
        ).forEach(button => {
            button.addEventListener("click", () => {
                window.location.reload();
            });
        });
    }

    async function setupConfiguredStats() {
        const statElements = document.querySelectorAll("[data-admin-stat]");

        for (const element of statElements) {
            const endpoint = element.dataset.api;
            if (!endpoint) continue;

            try {
                const response = await fetch(endpoint, {
                    headers: {
                        "Authorization": `Bearer ${token}`,
                        "Accept": "application/json"
                    }
                });

                if (!response.ok) {
                    console.warn(
                        "Admin statistic request failed:",
                        endpoint,
                        response.status
                    );
                    continue;
                }

                const result = await response.json();
                const key = element.dataset.adminStat;
                const data = result.data || result;

                if (Object.prototype.hasOwnProperty.call(data, key)) {
                    element.textContent = String(data[key]);
                }
            } catch (error) {
                console.error("Failed to load admin statistic:", error);
            }
        }
    }
}
