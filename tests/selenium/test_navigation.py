import os
from urllib.request import urlopen

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


PAGE_GET_ROUTES = (
    "/",
    "/user-search/",
    "/login/",
    "/forgot-password/",
    "/reset-password/",
    "/register/",
    "/dashboard/",
    "/profile/",
    "/settings/",
    "/ratings/",
    "/blood/",
    "/notifications/",
    "/goods-list/",
    "/create-goods/",
    "/goods-details/",
    "/goods-chat/",
    "/goods-conversations/",
    "/health-questions/",
    "/create-health-question/",
    "/health-question-details/",
    "/health-professionals/",
    "/volunteer-opportunities/",
    "/volunteer-opportunity-details/",
    "/create-opportunity/",
    "/volunteer-profile/",
    "/volunteer-attendance/",
    "/volunteer-message/",
    "/volunteer-certificate/print/",
    "/volunteer-certificate/",
    "/volunteer-search/",
    "/admin-volunteers/",
    "/blood-donor/",
    "/blood-request/",
    "/blood-requests/",
    "/matching-donors/",
    "/donation-history/",
    "/waste-pickup/",
    "/collector-details/",
    "/farmer-market/",
    "/create-produce/",
    "/produce-details/",
    "/nid-verification/",
    "/admin-verification/",
    "/admin-logs/",
    "/admin-dashboard/",
    "/admin-moderation/",
    "/admin-ngo-approval/",
)


@pytest.fixture
def browser(live_server):
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1280,900")
    options.add_argument("--disable-dev-shm-usage")
    driver_path = os.environ.get("CHROMEDRIVER")
    service = Service(executable_path=driver_path) if driver_path else Service()
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(20)
    yield driver
    driver.quit()


@pytest.mark.parametrize("path", PAGE_GET_ROUTES)
def test_declared_page_get_routes_return_rendered_pages(live_server, path):
    with urlopen(f"{live_server.url}{path}", timeout=10) as response:
        page = response.read().decode("utf-8")

    assert response.status == 200
    assert "<body" in page.lower()
    assert page.strip()


def test_login_forgot_password_back_link_returns_to_login(browser, live_server):
    browser.get(f"{live_server.url}/")
    browser.find_element(By.CSS_SELECTOR, 'a[href="/login/"]').click()
    WebDriverWait(browser, 10).until(EC.url_to_be(f"{live_server.url}/login/"))

    browser.find_element(By.CSS_SELECTOR, 'a[href="/forgot-password/"]').click()
    WebDriverWait(browser, 10).until(
        EC.url_to_be(f"{live_server.url}/forgot-password/")
    )
    back_link = browser.find_element(By.CSS_SELECTOR, "a[data-smart-back]")
    assert back_link.get_attribute("href") == f"{live_server.url}/login/"
    back_link.click()

    WebDriverWait(browser, 10).until(EC.url_to_be(f"{live_server.url}/login/"))
    assert browser.find_element(By.TAG_NAME, "body").text.strip()


def test_direct_forgot_password_open_uses_login_fallback(browser, live_server):
    browser.get(f"{live_server.url}/forgot-password/")
    back_link = browser.find_element(By.CSS_SELECTOR, "a[data-smart-back]")

    assert back_link.get_attribute("href") == f"{live_server.url}/login/"
