from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from django.contrib.staticfiles.testing import StaticLiveServerTestCase


class BackNavigationSeleniumTests(StaticLiveServerTestCase):
    def setUp(self):
        options = webdriver.EdgeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1280,900")
        self.browser = webdriver.Edge(options=options)
        self.browser.set_page_load_timeout(20)
        self.wait = WebDriverWait(self.browser, 10)

    def tearDown(self):
        try:
            self.browser.quit()
        finally:
            super().tearDown()

    def test_back_link_returns_to_previous_internal_page(self):
        self.browser.get(f"{self.live_server_url}/")
        self.browser.find_element(By.CSS_SELECTOR, 'a[href="/login/"]').click()
        self.browser.find_element(By.CSS_SELECTOR, 'a[href="/forgot-password/"]').click()
        self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a[data-smart-back]"))).click()

        self.wait.until(lambda browser: browser.current_url.endswith("/login/"))

    def test_direct_open_uses_parent_page_fallback(self):
        self.browser.get(f"{self.live_server_url}/forgot-password/")
        self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a[data-smart-back]"))).click()

        self.wait.until(lambda browser: browser.current_url.endswith("/login/"))

    def test_module_pages_have_dashboard_fallbacks(self):
        for page in ("/goods-list/", "/health-questions/"):
            with self.subTest(page=page):
                self.browser.get(f"{self.live_server_url}/login/")
                self.browser.execute_script("localStorage.setItem('helpnet_token', 'test-token');")
                self.browser.get(f"{self.live_server_url}{page}")
                back_link = self.wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "a[data-smart-back]"))
                )
                self.assertEqual(back_link.get_attribute("href"), f"{self.live_server_url}/dashboard/")
