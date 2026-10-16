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
