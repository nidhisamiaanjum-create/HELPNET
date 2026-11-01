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
from selenium.webdriver.support.ui import WebDriverWait

from apps.users.models import UserProfile
from apps.verification.models import VerificationRequest


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
        user = User.objects.create_user(**user_fields)
        user.selenium_password = password
        return user

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


def test_registration_creates_a_citizen_profile_from_the_browser(
    browser, live_server
):
    suffix = uuid4().hex
    phone = f"017{uuid4().int % 100_000_000:08d}"
    email = f"registration-{suffix}@example.test"
    password = f"Register-{suffix}-42"
    full_name = "Selenium Registration"

    browser.get(f"{live_server.url}/register/")
    WebDriverWait(browser, WAIT_SECONDS).until(
        EC.visibility_of_element_located((By.ID, "registerForm"))
    )
    browser.find_element(By.ID, "fullName").send_keys(full_name)
    browser.find_element(By.ID, "phoneNumber").send_keys(phone)
    browser.find_element(By.ID, "password").send_keys(password)
    browser.find_element(By.ID, "email").send_keys(email)
    register_button = browser.find_element(By.ID, "registerButton")
    browser.execute_script(
        "arguments[0].scrollIntoView({block: 'center'});", register_button
    )
    browser.execute_script("arguments[0].click();", register_button)

    WebDriverWait(browser, WAIT_SECONDS).until(
        lambda _: User.objects.filter(email=email).exists()
    )
    user = User.objects.get(email=email)
    profile = UserProfile.objects.get(user=user)
    assert user.check_password(password)
    assert user.phone_number == phone
    assert profile.profile_type == UserProfile.Type.CITIZEN
    assert profile == user.active_profile


def test_login_accepts_fixture_credentials_and_sets_a_session(
    browser, live_server, user_factory
):
    user = user_factory()
    browser.get(f"{live_server.url}/login/")
    WebDriverWait(browser, WAIT_SECONDS).until(
        EC.visibility_of_element_located((By.ID, "loginForm"))
    )
    browser.find_element(By.ID, "identifier").send_keys(user.phone_number)
    browser.find_element(By.ID, "password").send_keys(user.selenium_password)
    browser.find_element(By.ID, "loginButton").click()

    WebDriverWait(browser, WAIT_SECONDS).until(
        EC.url_contains("/dashboard/")
    )
    assert browser.execute_script(
        "return localStorage.getItem('helpnet_token')"
    )
    stored_user = browser.execute_script(
        "return JSON.parse(localStorage.getItem('helpnet_user'))"
    )
    assert stored_user["user_id"] == str(user.user_id)


def test_invalid_login_stays_on_login_and_shows_an_error(
    browser, live_server, user_factory
):
    user = user_factory()
    browser.get(f"{live_server.url}/login/")
    WebDriverWait(browser, WAIT_SECONDS).until(
        EC.visibility_of_element_located((By.ID, "loginForm"))
    )
    browser.find_element(By.ID, "identifier").send_keys(user.email)
    browser.find_element(By.ID, "password").send_keys(
        f"{user.selenium_password}-invalid"
    )
    browser.find_element(By.ID, "loginButton").click()

    alert = WebDriverWait(browser, WAIT_SECONDS).until(
        lambda driver: (
            element
            if (element := driver.find_element(By.ID, "formAlert")).is_displayed()
            and element.text.strip()
            else False
        )
    )
    assert "login/" in browser.current_url
    assert alert.text.strip()
    assert not browser.execute_script(
        "return localStorage.getItem('helpnet_token')"
    )


def test_authenticated_profile_can_be_updated_and_rendered(
    browser, live_server, user_factory
):
    user = user_factory(full_name="Profile Before Edit")
    sign_in(browser, live_server, user, "/profile/")
    profile_name = WebDriverWait(browser, WAIT_SECONDS).until(
        EC.visibility_of_element_located((By.ID, "profileName"))
    )
    assert profile_name.text == user.full_name

    result = browser_api(
        browser,
        "PATCH",
        "/api/auth/me/",
        {"bio": "A HELPNET community member", "location": "Dhaka"},
    )
    assert result["status"] == 200
    user.refresh_from_db()
    assert user.bio == "A HELPNET community member"
    assert user.location == "Dhaka"

    browser.refresh()
    WebDriverWait(browser, WAIT_SECONDS).until(
        lambda driver: driver.find_element(By.ID, "profileBio").text
        == "A HELPNET community member"
    )
    assert browser.find_element(By.ID, "profileLocation").text == "Dhaka"


def test_verification_document_submission_updates_status(
    browser, live_server, user_factory
):
    user = user_factory()
    sign_in(browser, live_server, user, "/nid-verification/")
    status = WebDriverWait(browser, WAIT_SECONDS).until(
        EC.visibility_of_element_located((By.ID, "verificationStatus"))
    )
    assert "যাচাই করা হয়নি" in status.text

    browser.execute_script(
        """
        const file = new File(
            ["%PDF-1.4\\n%%EOF"],
            "verification.pdf",
            {type: "application/pdf"}
        );
        const input = document.getElementById("verificationDocument");
        const transfer = new DataTransfer();
        transfer.items.add(file);
        input.files = transfer.files;
        input.dispatchEvent(new Event("change", {bubbles: true}));
        """
    )
    browser.find_element(By.ID, "submitVerification").click()

    try:
        WebDriverWait(browser, WAIT_SECONDS).until(
            lambda driver: "অপেক্ষমাণ"
            in driver.find_element(By.ID, "verificationStatus").text
        )
        request = VerificationRequest.objects.get(user=user)
        user.refresh_from_db()
        assert request.document_type == VerificationRequest.DocumentType.NID
        assert request.status == VerificationRequest.Status.PENDING
        assert not user.is_verified
        assert browser_api(browser, "GET", "/api/verification/status/")[
            "body"
        ]["data"]["status"] == VerificationRequest.Status.PENDING
    finally:
        request = VerificationRequest.objects.filter(user=user).first()
        if request and request.document:
            request.document.delete(save=False)
