import os
from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from apps.blood.models import BloodRequest, DonorProfile
from apps.notifications.models import Notification
from apps.ratings.models import Rating


User = get_user_model()
WAIT_SECONDS = 10


def create_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1280,1000")
    options.add_argument("--disable-dev-shm-usage")
    driver_path = os.environ.get("CHROMEDRIVER")
    service = Service(executable_path=driver_path) if driver_path else Service()
    return webdriver.Chrome(service=service, options=options)


@pytest.fixture
def browser(live_server):
    driver = create_driver()
    driver.set_page_load_timeout(20)
    yield driver
    driver.quit()


@pytest.fixture
def user_factory(db):
    def create_user(**fields):
        suffix = uuid4().hex
        password = f"Test-{suffix}-42"
        user_fields = {
            "phone_number": f"017{uuid4().int % 100_000_000:08d}",
            "email": f"selenium-{suffix}@example.test",
            "full_name": f"HELPNET Selenium {suffix[:8]}",
            "password": password,
        }
        user_fields.update(fields)
        return User.objects.create_user(**user_fields)

    return create_user


def sign_in(browser, live_server, user, path):
    access_token = str(RefreshToken.for_user(user).access_token)
    user_data = {
        "user_id": str(user.user_id),
        "full_name": user.full_name,
        "email": user.email,
        "phone_number": user.phone_number,
        "role": user.role,
    }
    browser.get(f"{live_server.url}/")
    browser.execute_script(
        """
        localStorage.setItem("helpnet_token", arguments[0]);
        localStorage.setItem("helpnet_user", JSON.stringify(arguments[1]));
        localStorage.setItem("helpnet_lang", "en");
        """,
        access_token,
        user_data,
    )
    browser.get(f"{live_server.url}{path}")


def browser_api(browser, method, path, body=None):
    return browser.execute_async_script(
        """
        const [method, path, body, done] = arguments;
        const headers = {
            "Authorization": `Bearer ${localStorage.getItem("helpnet_token")}`
        };
        if (body !== null) headers["Content-Type"] = "application/json";
        fetch(path, {
            method,
            headers,
            body: body === null ? undefined : JSON.stringify(body)
        }).then(async response => {
            const payload = await response.json().catch(() => ({}));
            done({status: response.status, body: payload});
        }).catch(error => done({error: error.message}));
        """,
        method,
        path,
        body,
    )


def wait_for_option(browser, element_id, value):
    WebDriverWait(browser, WAIT_SECONDS).until(
        lambda driver: driver.find_elements(
            By.CSS_SELECTOR, f"#{element_id} option[value='{value}']"
        )
    )


def test_user_can_submit_a_rating_from_the_ratings_page(
    browser, live_server, user_factory
):
    rater = user_factory(full_name="Rating Author")
    rated_user = user_factory(full_name="Rated HELPNET User")
    sign_in(browser, live_server, rater, f"/ratings/?user_id={rated_user.user_id}")

    WebDriverWait(browser, WAIT_SECONDS).until(
        lambda driver: driver.find_element(By.ID, "ratingsContent").is_displayed()
    )
    WebDriverWait(browser, WAIT_SECONDS).until(
        lambda driver: "No ratings yet."
        in driver.find_element(By.ID, "existingRatings").text
    )
    browser.find_element(
        By.CSS_SELECTOR, "#starPicker button[aria-label='5 stars']"
    ).click()
    browser.find_element(By.ID, "ratingComment").send_keys(
        "Reliable community member"
    )
    browser.find_element(
        By.CSS_SELECTOR, "#ratingForm button[type='submit']"
    ).click()

    WebDriverWait(browser, WAIT_SECONDS).until(
        lambda driver: "Rating submitted successfully"
        in driver.find_element(By.ID, "ratingsMessage").text
    )
    rating = Rating.objects.get(rater=rater, rated_user=rated_user)
    assert rating.rating == 5
    assert rating.comment == "Reliable community member"
    assert "Reliable community member" in browser.find_element(
        By.ID, "existingRatings"
    ).text


def test_donor_can_register_and_change_blood_availability(
    browser, live_server, user_factory
):
    donor = user_factory(full_name="Blood Donor")
    sign_in(browser, live_server, donor, "/blood/")
    wait_for_option(browser, "donorArea", "Dhaka")
    Select(browser.find_element(By.ID, "bloodGroup")).select_by_visible_text("O+")
    Select(browser.find_element(By.ID, "donorArea")).select_by_value("Dhaka")
    Select(browser.find_element(By.ID, "donorAvailability")).select_by_value("busy")
    browser.find_element(By.ID, "donorProfileForm").submit()

    WebDriverWait(browser, WAIT_SECONDS).until(
        lambda driver: "Donor profile saved"
        in driver.find_element(By.ID, "bloodMessage").text
    )
    profile = DonorProfile.objects.get(user=donor)
    assert profile.blood_group == "O+"
    assert profile.area == "Dhaka"
    assert profile.availability == DonorProfile.Availability.BUSY
    assert not profile.is_available


def test_blood_request_notifies_a_matching_donor(
    browser, live_server, user_factory
):
    requester = user_factory(full_name="Blood Requester")
    donor = user_factory(full_name="Matching O Positive Donor")
    DonorProfile.objects.create(
        user=donor,
        blood_group="O+",
        area="Dhaka",
        availability=DonorProfile.Availability.AVAILABLE,
    )
    sign_in(browser, live_server, requester, "/blood/")
    wait_for_option(browser, "requestGroup", "O+")
    wait_for_option(browser, "requestArea", "Dhaka")
    Select(browser.find_element(By.ID, "requestGroup")).select_by_value("O+")
    Select(browser.find_element(By.ID, "requestArea")).select_by_value("Dhaka")
    browser.find_element(By.ID, "hospital").send_keys("Dhaka Community Hospital")
    browser.find_element(By.ID, "requestDetails").send_keys(
        "Urgent blood request for a patient"
    )
    browser.find_element(By.ID, "requestForm").submit()

    WebDriverWait(browser, WAIT_SECONDS).until(
        lambda driver: "Blood request created"
        in driver.find_element(By.ID, "bloodMessage").text
    )
    blood_request = BloodRequest.objects.get(requester=requester)
    assert blood_request.status == BloodRequest.Status.OPEN
    assert blood_request.blood_group == "O+"
    alert = Notification.objects.get(user=donor, notification_type="blood_request")
    assert "O+" in alert.message
    assert "Dhaka" in alert.message

    sign_in(browser, live_server, donor, "/notifications/")
    notification_item = WebDriverWait(browser, WAIT_SECONDS).until(
        EC.visibility_of_element_located(
            (By.CSS_SELECTOR, ".notification-item.unread")
        )
    )
    assert "O+" in notification_item.text
    assert "Dhaka" in notification_item.text


def test_notification_can_be_marked_read_and_is_private(
    browser, live_server, user_factory
):
    owner = user_factory(full_name="Notification Owner")
    other_user = user_factory(full_name="Other Notification User")
    notification = Notification.objects.create(
        user=owner,
        message="Urgent O+ blood request in Dhaka.",
        notification_type="blood_request",
    )
    sign_in(browser, live_server, owner, "/notifications/")
    item = WebDriverWait(browser, WAIT_SECONDS).until(
        EC.visibility_of_element_located(
            (By.CSS_SELECTOR, ".notification-item.unread")
        )
    )
    assert notification.message in item.text
    item.find_element(By.CSS_SELECTOR, ".notification-read-button").click()
    WebDriverWait(browser, WAIT_SECONDS).until(
        EC.visibility_of_element_located(
            (By.CSS_SELECTOR, ".notification-status")
        )
    )
    notification.refresh_from_db()
    assert notification.is_read

    sign_in(browser, live_server, other_user, "/notifications/")
    WebDriverWait(browser, WAIT_SECONDS).until(
        EC.visibility_of_element_located(
            (By.CSS_SELECTOR, ".notification-empty")
        )
    )
    response = browser_api(
        browser, "POST", f"/api/notifications/{notification.id}/read/"
    )
    assert response["status"] == 404
