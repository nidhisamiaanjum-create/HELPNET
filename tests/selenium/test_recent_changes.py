import os
from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import StaleElementReferenceException

from apps.users.models import NGOVerificationDocument, UserProfile


User = get_user_model()
WAIT = 15
def create_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1440,1100")
    driver_path = os.environ.get("CHROMEDRIVER")
    service = Service(executable_path=driver_path) if driver_path else Service()
    return webdriver.Chrome(service=service, options=options)


@pytest.fixture
def browser(live_server):
    driver = create_driver()
    driver.set_page_load_timeout(25)
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


@pytest.fixture
def private_ngo_storage(tmp_path, settings):
    settings.PRIVATE_MEDIA_ROOT = tmp_path
    storage = NGOVerificationDocument._meta.get_field("file").storage
    original_location = storage._location
    original_base_location = storage.__dict__.get("base_location")
    original_cached_location = storage.__dict__.get("location")
    storage._location = tmp_path
    storage.__dict__.pop("location", None)
    storage.__dict__.pop("base_location", None)

    yield tmp_path

    storage._location = original_location
    storage.__dict__.pop("location", None)
    storage.__dict__.pop("base_location", None)
    if original_base_location is not None:
        storage.__dict__["base_location"] = original_base_location
    if original_cached_location is not None:
        storage.__dict__["location"] = original_cached_location


def sign_in(browser, live_server, user, path):
    user.refresh_from_db()
    access_token = str(RefreshToken.for_user(user).access_token)
    user_data = {
        "user_id": str(user.user_id),
        "full_name": user.full_name,
        "email": user.email,
        "phone_number": user.phone_number,
        "role": user.role,
        "is_staff": user.is_staff,
        "is_superuser": user.is_superuser,
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


def seed_active_profile(user, profile_type, display_name=""):
    profile = UserProfile.objects.create(
        user=user,
        profile_type=profile_type,
        display_name=display_name,
        ngo_approval_status=(
            UserProfile.NGOApprovalStatus.PENDING
            if profile_type == UserProfile.Type.NGO
            else UserProfile.NGOApprovalStatus.NOT_REQUIRED
        ),
    )
    user.active_profile = profile
    user.role = {
        UserProfile.Type.CITIZEN: User.Role.CITIZEN,
        UserProfile.Type.VOLUNTEER: User.Role.VOLUNTEER,
        UserProfile.Type.FARMER: User.Role.FARMER,
        UserProfile.Type.NGO: User.Role.NGO,
        UserProfile.Type.BLOOD_DONOR: User.Role.BLOOD_DONOR,
    }[profile_type]
    user.save(update_fields=["active_profile", "role"])
    return profile


def profile_card(browser, title):
    xpath = (
        "//*[@id='myProfilesList']/div[contains(@class,'card')]"
        f"[.//strong[normalize-space()='{title}']]"
    )
    for _ in range(2):
        try:
            return WebDriverWait(
                browser,
                WAIT,
                ignored_exceptions=(StaleElementReferenceException,),
            ).until(EC.presence_of_element_located((By.XPATH, xpath)))
        except StaleElementReferenceException:
            continue
    raise AssertionError(f"Profile card not found or was repeatedly replaced: {title}")


def profile_card_text(browser, title):
    return browser.execute_script(
        """
        const card = Array.from(
            document.querySelectorAll("#myProfilesList > .card")
        ).find(element =>
            element.querySelector("strong")?.textContent.trim() === arguments[0]
        );
        return card ? card.innerText : "";
        """,
        title,
    )


def profile_card_has_button(browser, title, button_text):
    return browser.execute_script(
        """
        const card = Array.from(
            document.querySelectorAll("#myProfilesList > .card")
        ).find(element =>
            element.querySelector("strong")?.textContent.trim() === arguments[0]
        );
        return Boolean(card && Array.from(card.querySelectorAll("button"))
            .some(button => button.textContent.includes(arguments[1])));
        """,
        title,
        button_text,
    )


def click_center(browser, element):
    browser.execute_script(
        "arguments[0].scrollIntoView({block: 'center'});",
        element,
    )
    browser.execute_script("arguments[0].click();", element)


def wait_visible_by_id(browser, element_id):
    return WebDriverWait(browser, WAIT).until(
        lambda driver: driver.execute_script(
            """
            const element = document.getElementById(arguments[0]);
            return Boolean(element && element.offsetParent !== null);
            """,
            element_id,
        )
    )


def wait_for_profile_cards(browser):
    previous_titles = None
    stable_reads = 0

    def list_is_stable(driver):
        nonlocal previous_titles, stable_reads
        titles = driver.execute_script(
            """
            return Array.from(
                document.querySelectorAll("#myProfilesList > .card strong")
            ).map(element => element.textContent.trim());
            """
        )
        if titles and titles == previous_titles:
            stable_reads += 1
        else:
            previous_titles = titles
            stable_reads = 0
        return titles if stable_reads >= 2 else False

    return WebDriverWait(browser, WAIT, poll_frequency=0.25).until(
        list_is_stable
    )


def browser_document_status(browser, url, token):
    return browser.execute_async_script(
        """
        const [url, token, done] = arguments;
        fetch(url, {headers: {Authorization: `Bearer ${token}`}})
            .then(response => done({
                status: response.status,
                contentDisposition: response.headers.get("Content-Disposition")
            }))
            .catch(error => done({error: error.message}));
        """,
        url,
        token,
    )


def ngo_application_text(browser, organization_name):
    return browser.execute_script(
        """
        const application = Array.from(
            document.querySelectorAll(".ngo-application")
        ).find(element => element.innerText.includes(arguments[0]));
        return application ? application.innerText : "";
        """,
        organization_name,
    )


def create_registration_document(profile, name="registration.pdf"):
    return NGOVerificationDocument.objects.create(
        profile=profile,
        document_type=NGOVerificationDocument.DocumentType.REGISTRATION_CERTIFICATE,
        file=SimpleUploadedFile(
            name,
            b"%PDF-1.7\nHELPNET Selenium evidence\n%%EOF",
            content_type="application/pdf",
        ),
        original_name=name,
    )


def test_profile_management_create_switch_edit_deactivate_and_reactivate(
    browser, live_server, user_factory
):
    user = user_factory()
    citizen = seed_active_profile(
        user, UserProfile.Type.CITIZEN, "Personal Citizen"
    )
    sign_in(browser, live_server, user, "/dashboard/")
    wait_for_profile_cards(browser)
    assert profile_card(browser, "Personal Citizen")

    browser.find_element(By.ID, "createProfileButton").click()
    browser.find_element(By.ID, "newProfileType").send_keys("Volunteer")
    browser.find_element(
        By.CSS_SELECTOR, "#newProfileForm button[type='submit']"
    ).click()
    assert len(wait_for_profile_cards(browser)) == 2
    volunteer = UserProfile.objects.get(
        user=user, profile_type=UserProfile.Type.VOLUNTEER
    )
    assert volunteer.id != citizen.id
    assert profile_card(browser, "Volunteer")

    profile_card(browser, "Personal Citizen").find_element(
        By.XPATH, ".//button[contains(., 'Switch profile')]"
    ).click()
    wait_for_profile_cards(browser)
    WebDriverWait(browser, WAIT).until(
        lambda driver: "Current profile"
        in profile_card_text(driver, "Personal Citizen")
    )
    user.refresh_from_db()
    assert user.active_profile_id == citizen.id

    browser.find_element(By.ID, "createProfileButton").click()
    browser.find_element(By.ID, "newProfileType").send_keys("Farmer")
    browser.find_element(
        By.CSS_SELECTOR, "#newProfileForm button[type='submit']"
    ).click()
    assert "Farmer" in wait_for_profile_cards(browser)
    farmer = UserProfile.objects.get(
        user=user, profile_type=UserProfile.Type.FARMER
    )
    assert farmer.status == UserProfile.Status.ACTIVE

    profile_card(browser, "Volunteer").find_element(
        By.XPATH, ".//button[contains(., 'Switch profile')]"
    ).click()
    wait_for_profile_cards(browser)
    WebDriverWait(browser, WAIT).until(
        lambda driver: "Current profile"
        in profile_card_text(driver, "Volunteer")
    )
    user.refresh_from_db()
    assert user.active_profile_id == volunteer.id

    profile_card(browser, "Farmer").find_element(
        By.XPATH, ".//button[contains(., 'Edit profile')]"
    ).click()
    edit_name = WebDriverWait(browser, WAIT).until(
        EC.visibility_of_element_located((By.ID, "editProfileDisplayName"))
    )
    edit_name.clear()
    edit_name.send_keys("Farm Helper")
    browser.find_element(
        By.CSS_SELECTOR, "#profileEditForm button[type='submit']"
    ).click()
    WebDriverWait(browser, WAIT).until(
        lambda driver: profile_card(driver, "Farm Helper")
    )
    farmer.refresh_from_db()
    assert farmer.display_name == "Farm Helper"

    browser.execute_script("window.confirm = () => true")
    profile_card(browser, "Volunteer").find_element(
        By.XPATH, ".//button[contains(., 'Deactivate')]"
    ).click()
    wait_for_profile_cards(browser)
    assert profile_card_has_button(browser, "Volunteer", "Reactivate")
    volunteer.refresh_from_db()
    assert volunteer.status == UserProfile.Status.INACTIVE
    profile_card(browser, "Volunteer").find_element(
        By.XPATH, ".//button[contains(., 'Reactivate')]"
    ).click()
    wait_for_profile_cards(browser)
    assert profile_card_has_button(browser, "Volunteer", "Deactivate")
    volunteer.refresh_from_db()
    assert volunteer.status == UserProfile.Status.ACTIVE
    assert User.objects.filter(pk=user.pk).exists()
    assert UserProfile.objects.filter(user=user).count() == 3


def test_ngo_owner_creates_profile_uploads_documents_and_sees_pending_status(
    browser, live_server, user_factory, private_ngo_storage, tmp_path
):
    user = user_factory()
    seed_active_profile(user, UserProfile.Type.CITIZEN, "Personal Citizen")
    sign_in(browser, live_server, user, "/dashboard/")
    wait_for_profile_cards(browser)

    browser.find_element(By.ID, "createProfileButton").click()
    browser.find_element(By.ID, "newProfileType").send_keys("NGO")
    browser.find_element(By.ID, "ngoDisplayName").send_keys("Community Support")
    browser.find_element(
        By.CSS_SELECTOR, "#newProfileForm button[type='submit']"
    ).click()
    wait_visible_by_id(browser, "ngoVerificationForm")
    ngo = UserProfile.objects.get(
        user=user, profile_type=UserProfile.Type.NGO
    )

    fields = {
        "ngoOrganizationName": "Community Support",
        "ngoRegistrationNumber": "SELENIUM-NGO-001",
        "ngoOrganizationAddress": "Dhaka, Bangladesh",
        "ngoContactEmail": "contact@example.test",
        "ngoContactPhone": "01722220002",
        "ngoRepresentativeName": "Test Representative",
    }
    for field_id, value in fields.items():
        field = browser.find_element(By.ID, field_id)
        field.clear()
        field.send_keys(value)

    invalid_file = tmp_path / "invalid.exe"
    invalid_file.write_bytes(b"not an accepted document")
    file_input = browser.find_element(By.ID, "ngoRegistrationCertificate")
    file_input.send_keys(str(invalid_file))
    click_center(
        browser,
        browser.find_element(
            By.CSS_SELECTOR, "#ngoVerificationForm button[type='submit']"
        ),
    )
    submit_button = browser.find_element(
        By.CSS_SELECTOR, "#ngoVerificationForm button[type='submit']"
    )
    WebDriverWait(browser, WAIT).until(lambda _: submit_button.is_enabled())
    invalid_type_message = browser.find_element(
        By.ID, "ngoVerificationFormMessage"
    ).text.strip()
    assert invalid_type_message, browser.get_log("browser")
    assert not NGOVerificationDocument.objects.filter(profile=ngo).exists()

    oversized_file = tmp_path / "oversized.pdf"
    oversized_file.write_bytes(b"%PDF-1.7\n" + (b"x" * (10 * 1024 * 1024)))
    file_input = browser.find_element(By.ID, "ngoRegistrationCertificate")
    file_input.clear()
    file_input.send_keys(str(oversized_file))
    click_center(
        browser,
        browser.find_element(
            By.CSS_SELECTOR, "#ngoVerificationForm button[type='submit']"
        ),
    )
    WebDriverWait(browser, WAIT).until(
        lambda driver: "10 MB"
        in driver.find_element(By.ID, "ngoVerificationFormMessage").text
    )
    assert not NGOVerificationDocument.objects.filter(profile=ngo).exists()

    certificate = tmp_path / "registration.pdf"
    certificate.write_bytes(b"%PDF-1.7\nregistration certificate\n%%EOF")
    file_input = browser.find_element(By.ID, "ngoRegistrationCertificate")
    file_input.clear()
    file_input.send_keys(str(certificate))
    optional = tmp_path / "supporting.png"
    optional.write_bytes(b"\x89PNG\r\n\x1a\nHELPNET test image")
    browser.find_element(By.ID, "ngoSupportingDocuments").send_keys(
        str(optional)
    )
    click_center(
        browser,
        browser.find_element(
            By.CSS_SELECTOR, "#ngoVerificationForm button[type='submit']"
        ),
    )
    WebDriverWait(browser, WAIT).until(
        lambda driver: "Pending"
        in driver.find_element(By.ID, "ngoVerificationStatus").text
    )
    ngo.refresh_from_db()
    user.refresh_from_db()
    assert ngo.ngo_registration_number == fields["ngoRegistrationNumber"]
    assert ngo.ngo_submitted_at is not None
    assert NGOVerificationDocument.objects.filter(profile=ngo).count() == 2
    assert not user.is_verified
    assert "Pending" in browser.find_element(
        By.ID, "ngoVerificationStatus"
    ).text
    assert len(browser.find_elements(
        By.CSS_SELECTOR, "#ngoVerificationDocuments a"
    )) == 2

    document = NGOVerificationDocument.objects.filter(profile=ngo).first()
    owner_token = str(RefreshToken.for_user(user).access_token)
    owner_response = browser_document_status(
        browser,
        f"/api/auth/ngo-verification-documents/{document.pk}/",
        owner_token,
    )
    assert owner_response["status"] == 200
    assert "attachment" in owner_response["contentDisposition"].lower()

    outsider = user_factory()
    outsider_token = str(RefreshToken.for_user(outsider).access_token)
    outsider_response = browser_document_status(
        browser,
        f"/api/auth/ngo-verification-documents/{document.pk}/",
        outsider_token,
    )
    assert outsider_response["status"] == 403


@pytest.mark.parametrize(
    ("verification_status", "button_class", "reason"),
    [
        ("approved", "approve-button", ""),
        ("rejected", "reject-button", "Please update the registration."),
        (
            "additional_documents_required",
            "request-documents-button",
            "Please upload an authorization letter.",
        ),
    ],
)
def test_admin_reviews_ngo_application_in_browser(
    browser,
    live_server,
    user_factory,
    private_ngo_storage,
    verification_status,
    button_class,
    reason,
):
    owner = user_factory(role=User.Role.NGO)
    ngo = seed_active_profile(
        owner, UserProfile.Type.NGO, "Browser Review Organization"
    )
    ngo.ngo_registration_number = "REVIEW-001"
    ngo.ngo_address = "Dhaka"
    ngo.ngo_contact_email = "review@example.test"
    ngo.ngo_contact_phone = "01700000001"
    ngo.ngo_representative_name = "Review Representative"
    ngo.ngo_verification_status = UserProfile.NGOVerificationStatus.PENDING
    ngo.ngo_submitted_at = timezone.now()
    ngo.save()
    document = create_registration_document(ngo)

    admin = User.objects.create_superuser(
        phone_number=f"016{uuid4().int % 100_000_000:08d}",
        email=f"admin-{uuid4().hex}@example.test",
        full_name="HELPNET Selenium Administrator",
        password=f"Admin-{uuid4().hex}-42",
    )
    sign_in(browser, live_server, admin, "/admin-ngo-approval/")
    application = WebDriverWait(browser, WAIT).until(
        lambda driver: next(
            (
                card
                for card in driver.find_elements(
                    By.CSS_SELECTOR, ".ngo-application"
                )
                if "Browser Review Organization" in card.text
            ),
            False,
        )
    )
    assert "REVIEW-001" in application.text
    assert document.original_name in application.text

    admin_token = str(RefreshToken.for_user(admin).access_token)
    admin_response = browser_document_status(
        browser,
        f"/api/auth/ngo-verification-documents/{document.pk}/",
        admin_token,
    )
    assert admin_response["status"] == 200

    action_button = application.find_element(
        By.CSS_SELECTOR, f"button.{button_class}"
    )
    if reason:
        application.find_element(
            By.CSS_SELECTOR, "textarea.ngo-review-reason"
        ).send_keys(reason)
    action_button.click()
    if verification_status in (
        UserProfile.NGOVerificationStatus.APPROVED,
        UserProfile.NGOVerificationStatus.REJECTED,
    ):
        WebDriverWait(browser, WAIT).until(EC.alert_is_present())
        browser.switch_to.alert.accept()

    if verification_status == (
        UserProfile.NGOVerificationStatus.ADDITIONAL_DOCUMENTS_REQUIRED
    ):
        WebDriverWait(browser, WAIT).until(
            lambda driver: "Additional documents required"
            in ngo_application_text(driver, "Browser Review Organization")
        )
    else:
        WebDriverWait(browser, WAIT).until(
            lambda driver: not ngo_application_text(
                driver, "Browser Review Organization"
            )
        )
    ngo.refresh_from_db()
    owner.refresh_from_db()
    assert ngo.ngo_reviewed_at is not None
    if reason:
        assert ngo.ngo_verification_reason == reason
    if verification_status == UserProfile.NGOVerificationStatus.APPROVED:
        assert ngo.ngo_approval_status == UserProfile.NGOApprovalStatus.APPROVED
        assert not owner.is_verified


def test_profile_language_toggle_translates_dynamic_content_and_persists(
    browser, live_server, user_factory
):
    user = user_factory(
        role=User.Role.FARMER,
        gender=User.Gender.FEMALE,
        full_name="Language Test Farmer",
    )
    seed_active_profile(user, UserProfile.Type.FARMER, "Language Farmer")
    sign_in(browser, live_server, user, "/profile/")
    WebDriverWait(browser, WAIT).until(
        EC.visibility_of_element_located((By.ID, "profileName"))
    )

    assert browser.find_element(
        By.CSS_SELECTOR, '[data-i18n="personalInformation"]'
    ).text == "Personal information"
    browser.find_element(By.ID, "langToggle").click()
    WebDriverWait(browser, WAIT).until(
        lambda driver: driver.find_element(
            By.CSS_SELECTOR, '[data-i18n="personalInformation"]'
        ).text
        == "ব্যক্তিগত তথ্য"
    )
    assert browser.find_element(By.ID, "profileRole").text == "কৃষক"
    assert browser.find_element(By.ID, "infoGender").text == "নারী"
    assert browser.execute_script(
        "return localStorage.getItem('helpnet_lang')"
    ) == "bn"

    browser.refresh()
    WebDriverWait(browser, WAIT).until(
        lambda driver: driver.find_element(
            By.CSS_SELECTOR, '[data-i18n="personalInformation"]'
        ).text
        == "ব্যক্তিগত তথ্য"
    )

    browser.get(f"{live_server.url}/profile/?user_id={user.user_id}")
    WebDriverWait(browser, WAIT).until(
        EC.visibility_of_element_located((By.ID, "rateUserSection"))
    )
    assert browser.find_element(
        By.CSS_SELECTOR, '[data-i18n="rateThisUser"]'
    ).text == "এই ব্যবহারকারীকে রেটিং দিন"
    assert browser.find_element(
        By.ID, "profileRatingComment"
    ).get_attribute("placeholder") == "মন্তব্য লিখুন..."

    browser.find_element(By.ID, "langToggle").click()
    WebDriverWait(browser, WAIT).until(
        lambda driver: driver.find_element(
            By.CSS_SELECTOR, '[data-i18n="rateThisUser"]'
        ).text
        == "Rate this user"
    )
    assert browser.find_element(
        By.CSS_SELECTOR, "#existingRatings h3"
    ).text == "Existing ratings"

    browser.get(f"{live_server.url}/profile/")
    WebDriverWait(browser, WAIT).until(
        lambda driver: driver.find_element(By.ID, "myListingsTitle").text
        == "My farm products"
    )
    browser.find_element(By.ID, "langToggle").click()
    WebDriverWait(browser, WAIT).until(
        lambda driver: driver.find_element(By.ID, "myListingsTitle").text
        == "আমার কৃষি পণ্য"
    )
    browser.refresh()
    WebDriverWait(browser, WAIT).until(
        lambda driver: driver.find_element(By.ID, "myListingsTitle").text
        == "আমার কৃষি পণ্য"
    )
    browser.get(f"{live_server.url}/dashboard/")
    WebDriverWait(browser, WAIT).until(
        lambda driver: "আমার প্রোফাইলগুলো"
        in driver.find_element(By.CSS_SELECTOR, '[data-i18n="myprofile"]').text
    )
    browser.find_element(By.ID, "langToggle").click()
    WebDriverWait(browser, WAIT).until(
        lambda driver: "My Profiles"
        in driver.find_element(By.CSS_SELECTOR, '[data-i18n="myprofile"]').text
    )
    browser.refresh()
    WebDriverWait(browser, WAIT).until(
        lambda driver: "My Profiles"
        in driver.find_element(By.CSS_SELECTOR, '[data-i18n="myprofile"]').text
    )


def test_profile_details_can_be_edited_and_saved_from_the_profile_page(
    browser, live_server, user_factory
):
    user = user_factory(full_name="Profile Before Edit")
    sign_in(browser, live_server, user, "/profile/")
    WebDriverWait(browser, WAIT).until(
        EC.visibility_of_element_located((By.ID, "profileName"))
    )

    name = browser.find_element(By.ID, "profileFullName")
    name.clear()
    name.send_keys("Profile After Edit")
    browser.find_element(By.ID, "profileBioInput").send_keys(
        "Updated through the profile page."
    )
    browser.find_element(By.ID, "profileLocationInput").send_keys(
        "Dhaka"
    )
    save_button = browser.find_element(
        By.CSS_SELECTOR, "#profileForm button[type='submit']"
    )
    click_center(browser, save_button)

    WebDriverWait(browser, WAIT).until(
        lambda driver: driver.find_element(
            By.ID, "profileFormMessage"
        ).text.strip()
    )
    WebDriverWait(browser, WAIT).until(
        lambda driver: driver.find_element(By.ID, "profileName").text
        == "Profile After Edit"
    )
    user.refresh_from_db()
    assert user.full_name == "Profile After Edit"
    assert user.bio == "Updated through the profile page."
    assert user.location == "Dhaka"
