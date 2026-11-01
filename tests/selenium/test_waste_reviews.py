import os
from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from apps.waste.models import WasteCollector, WasteCollectorRating, WastePickupRequest


User = get_user_model()


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


@pytest.fixture
def user_factory(db):
    def create_user(role="Citizen", **fields):
        suffix = uuid4().hex[:8]
        return User.objects.create_user(
            phone_number=f"017{uuid4().int % 100_000_000:08d}",
            email=f"waste-selenium-{suffix}@example.test",
            full_name=f"HELPNET Waste {suffix}",
            password="selenium-test-password",
            role=role,
            **fields,
        )

    return create_user


def sign_in(browser, live_server, user):
    browser.get(f"{live_server.url}/")
    token = str(RefreshToken.for_user(user).access_token)
    user_data = {
        "user_id": str(user.user_id),
        "full_name": user.full_name,
        "email": user.email,
        "phone_number": user.phone_number,
        "role": user.role,
        "location": user.location,
        "is_staff": user.is_staff,
        "is_superuser": user.is_superuser,
    }
    browser.execute_script(
        """
        localStorage.setItem("helpnet_token", arguments[0]);
        localStorage.setItem("helpnet_user", JSON.stringify(arguments[1]));
        localStorage.setItem("helpnet_lang", "en");
        """,
        token,
        user_data,
    )


def waste_collector_card(browser, name):
    for card in browser.find_elements(By.CSS_SELECTOR, ".collector-card"):
        if card.find_element(By.CSS_SELECTOR, ".collector-name").text == name:
            return card
    return False


def test_citizen_can_request_pickup_and_share_a_collector(
    browser, live_server, user_factory
):
    citizen = user_factory(location="Selenium Ward")
    another_citizen = user_factory(location="Elsewhere")
    private_request = WastePickupRequest.objects.create(
        requester=another_citizen,
        waste_type=WastePickupRequest.WasteType.GENERAL,
        area="Elsewhere",
        location="Private test address",
    )

    sign_in(browser, live_server, citizen)
    browser.get(f"{live_server.url}/waste-pickup/")
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.ID, "wastePickupForm"))
    )

    area = browser.find_element(By.ID, "pickupArea")
    area.clear()
    area.send_keys("Selenium Ward")
    Select(browser.find_element(By.ID, "wasteType")).select_by_value("Organic")
    browser.find_element(By.ID, "pickupLocation").send_keys(
        "House 12, Selenium Road"
    )
    browser.find_element(By.ID, "preferredTime").send_keys("10 AM")
    browser.find_element(By.ID, "notes").send_keys("Please call on arrival.")
    submit_request = browser.find_element(By.ID, "submitWasteBtn")
    browser.execute_script(
        "arguments[0].scrollIntoView({block: 'center'}); arguments[0].click();",
        submit_request,
    )

    WebDriverWait(browser, 10).until(
        lambda _driver: WastePickupRequest.objects.filter(
            requester=citizen, location="House 12, Selenium Road"
        ).exists()
    )
    pickup = WastePickupRequest.objects.get(
        requester=citizen, location="House 12, Selenium Road"
    )
    assert pickup.waste_type == WastePickupRequest.WasteType.ORGANIC
    assert pickup.area.strip() == "Selenium Ward"
    assert pickup.status == WastePickupRequest.Status.REQUESTED
    assert pickup.preferred_pickup_time == "10 AM"
    assert pickup.notes == "Please call on arrival."

    requests_text = browser.find_element(By.ID, "requestsList").text
    assert "House 12, Selenium Road" in requests_text
    assert "Private test address" not in requests_text

    private_request_url = f"/api/waste/requests/{private_request.id}/"
    private_request_status = browser.execute_async_script(
        """
        const done = arguments[arguments.length - 1];
        fetch(arguments[0], {
            headers: { Authorization: `Bearer ${localStorage.getItem("helpnet_token")}` }
        }).then(response => done(response.status)).catch(() => done(0));
        """,
        private_request_url,
    )
    assert private_request_status == 404

    browser.find_element(By.ID, "collectorName").send_keys("Ward Waste Service")
    browser.find_element(By.ID, "collectorPhone").send_keys("01711112222")
    browser.find_element(By.ID, "collectorArea").send_keys("Selenium Ward")
    browser.find_element(By.ID, "collectorWasteTypes").send_keys("Organic, paper")
    browser.find_element(By.ID, "collectorNotes").send_keys("Open weekdays.")
    share_collector = browser.find_element(By.ID, "shareCollectorBtn")
    browser.execute_script(
        "arguments[0].scrollIntoView({block: 'center'}); arguments[0].click();",
        share_collector,
    )

    WebDriverWait(browser, 10).until(
        lambda _driver: WasteCollector.objects.filter(
            name="Ward Waste Service", shared_by=citizen
        ).exists()
    )
    collector = WasteCollector.objects.get(
        name="Ward Waste Service", shared_by=citizen
    )
    assert collector.phone == "01711112222"
    assert collector.area == "Selenium Ward"
    assert collector.waste_types == "Organic, paper"
    assert collector.notes == "Open weekdays."


def test_shared_collector_reviews_and_authenticated_rating_work_in_ui(
    browser, live_server, user_factory
):
    viewer = user_factory(location="Selenium District")
    reviewer = user_factory(location="Selenium District")
    volunteer = user_factory(
        role="Volunteer",
        location="Selenium District",
    )
    collector = WasteCollector.objects.create(
        name="Listed Local Collector",
        phone="01711113333",
        area="Selenium District",
        shared_by=reviewer,
    )
    WasteCollectorRating.objects.create(
        collector=collector,
        user=reviewer,
        rating=4,
        review="Arrived on time and left the area clean.",
    )

    sign_in(browser, live_server, viewer)
    browser.get(f"{live_server.url}/waste-pickup/")

    shared_card = WebDriverWait(browser, 10).until(
        lambda driver: waste_collector_card(driver, "Listed Local Collector")
    )
    volunteer_card = WebDriverWait(browser, 10).until(
        lambda driver: waste_collector_card(driver, volunteer.full_name)
    )
    assert not volunteer_card.find_elements(By.CSS_SELECTOR, ".btn-rate")
    assert not volunteer_card.find_elements(By.CSS_SELECTOR, ".btn-view-reviews")

    shared_card.find_element(By.CSS_SELECTOR, ".btn-view-reviews").click()
    WebDriverWait(browser, 10).until(
        EC.text_to_be_present_in_element(
            (By.CSS_SELECTOR, ".collector-review p"),
            "Arrived on time and left the area clean.",
        )
    )

    shared_card.find_element(By.CSS_SELECTOR, ".btn-rate").click()
    WebDriverWait(browser, 5).until(
        EC.visibility_of_element_located((By.ID, "ratingModal"))
    )
    browser.find_element(
        By.CSS_SELECTOR, '.rating-star[data-value="5"]'
    ).click()
    browser.find_element(By.ID, "collectorReview").send_keys(
        "Friendly and careful with recycling."
    )
    browser.find_element(By.ID, "submitCollectorRating").click()

    WebDriverWait(browser, 10).until(
        lambda _driver: WasteCollectorRating.objects.filter(
            collector=collector,
            user=viewer,
            rating=5,
            review="Friendly and careful with recycling.",
        ).exists()
    )
    saved_rating = WasteCollectorRating.objects.get(
        collector=collector,
        user=viewer,
    )
    assert saved_rating.collector_id == collector.id
    assert saved_rating.user_id == viewer.pk
    assert collector.average_rating == 4.5
    assert collector.rating_count == 2

    refreshed_card = WebDriverWait(browser, 10).until(
        lambda driver: waste_collector_card(driver, "Listed Local Collector")
    )
    assert "4.5" in refreshed_card.text
    assert "2 ratings" in refreshed_card.text
    refreshed_card.find_element(By.CSS_SELECTOR, ".btn-view-reviews").click()
    WebDriverWait(browser, 10).until(
        EC.text_to_be_present_in_element(
            (By.CSS_SELECTOR, ".collector-reviews"),
            "Friendly and careful with recycling.",
        )
    )
    review_text = browser.find_element(
        By.CSS_SELECTOR, ".collector-reviews"
    ).text
    assert reviewer.full_name in review_text
    assert viewer.full_name in review_text
    assert "4/5" in review_text
    assert "5/5" in review_text
