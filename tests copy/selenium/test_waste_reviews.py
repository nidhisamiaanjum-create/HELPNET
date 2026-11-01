from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from rest_framework_simplejwt.tokens import RefreshToken
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from apps.waste.models import WasteCollector, WasteCollectorRating


User = get_user_model()


class WasteCollectorReviewSeleniumTests(StaticLiveServerTestCase):
    def setUp(self):
        self.viewer = User.objects.create_user(
            phone_number="01788880001",
            email="reviewer@example.test",
            full_name="Review Viewer",
            password="Password123!",
            role="Citizen",
            location="Dhanmondi, Dhaka",
        )
        self.volunteer = User.objects.create_user(
            phone_number="01788880002",
            email="volunteer@example.test",
            full_name="Volunteer Candidate",
            password="Password123!",
            role="Volunteer",
            location="Dhanmondi, Dhaka",
        )
        self.collector = WasteCollector.objects.create(
            name="Listed Local Collector",
            phone="01788880003",
            area="Dhanmondi",
            shared_by=self.viewer,
        )
        WasteCollectorRating.objects.create(
            collector=self.collector,
            user=self.volunteer,
            rating=4,
            review="Arrived on time and left the area clean.",
        )

        options = webdriver.EdgeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1280,900")
        self.browser = webdriver.Edge(options=options)
        self.wait = WebDriverWait(self.browser, 10)

    def tearDown(self):
        try:
            self.browser.quit()
        finally:
            super().tearDown()

    def test_persisted_collector_reviews_show_and_volunteer_has_no_dead_rate_button(self):
        token = str(RefreshToken.for_user(self.viewer).access_token)
        self.browser.get(f"{self.live_server_url}/login/")
        self.browser.execute_script(
            "localStorage.setItem('helpnet_token', arguments[0]);", token
        )
        self.browser.get(f"{self.live_server_url}/waste-pickup/")

        def card_named(name):
            for card in self.browser.find_elements(By.CSS_SELECTOR, ".collector-card"):
                heading = card.find_element(By.CSS_SELECTOR, ".collector-name")
                if heading.text == name:
                    return card
            return False

        collector_card = self.wait.until(lambda _browser: card_named("Listed Local Collector"))
        volunteer_card = self.wait.until(lambda _browser: card_named("Volunteer Candidate"))

        self.assertEqual(len(volunteer_card.find_elements(By.CSS_SELECTOR, ".btn-rate")), 0)
        self.assertEqual(len(volunteer_card.find_elements(By.CSS_SELECTOR, ".btn-view-reviews")), 0)

        collector_card.find_element(By.CSS_SELECTOR, ".btn-view-reviews").click()
        self.wait.until(
            EC.text_to_be_present_in_element(
                (By.CSS_SELECTOR, ".collector-review p"),
                "Arrived on time and left the area clean.",
            )
        )

        self.browser.set_window_size(390, 844)
        has_horizontal_overflow = self.browser.execute_script(
            "return document.documentElement.scrollWidth > window.innerWidth;"
        )
        self.assertFalse(has_horizontal_overflow, "Waste pickup overflows at mobile width.")
