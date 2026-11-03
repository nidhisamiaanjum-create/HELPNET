from django.test import TestCase


class SmartBackNavigationPageTests(TestCase):
    pages = (
        "/admin-logs/",
        "/admin-moderation/",
        "/admin-verification/",
        "/admin-volunteers/",
        "/blood/",
        "/collector-details/",
        "/create-goods/",
        "/create-health-question/",
        "/create-opportunity/",
        "/create-produce/",
        "/farmer-market/",
        "/forgot-password/",
        "/goods-list/",
        "/goods-details/",
        "/health-professionals/",
        "/health-questions/",
        "/health-question-details/",
        "/nid-verification/",
        "/notifications/",
        "/produce-details/",
        "/profile/",
        "/ratings/",
        "/reset-password/",
        "/settings/",
        "/user-search/",
        "/volunteer-attendance/",
        "/volunteer-certificate/",
        "/volunteer-certificate/print/",
        "/volunteer-message/",
        "/volunteer-opportunities/",
        "/volunteer-opportunity-details/",
        "/volunteer-profile/",
        "/volunteer-search/",
        "/waste-pickup/",
    )

    def test_pages_with_back_links_load_shared_navigation_behavior(self):
        for page in self.pages:
            with self.subTest(page=page):
                response = self.client.get(page)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "data-smart-back")
                self.assertContains(response, "js/navigation.js")

    def test_health_professional_review_script_is_loaded_on_admin_page(self):
        admin_page = self.client.get("/admin-verification/")
        self.assertEqual(admin_page.status_code, 200)
        self.assertContains(
            admin_page,
            "/static/js/health-verification-admin.js",
        )

        nid_page = self.client.get("/nid-verification/")
        self.assertEqual(nid_page.status_code, 200)
        self.assertNotContains(
            nid_page,
            "health-verification-admin.js",
        )

    def test_ngo_approval_page_has_language_toggle_and_scripts(self):
        response = self.client.get("/admin-ngo-approval/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="langToggle"')
        self.assertContains(response, "/static/js/i18n.js")
        self.assertContains(response, "/static/js/ngo-approval.js")
