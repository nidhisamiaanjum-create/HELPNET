import os
from datetime import date, timedelta
from uuid import uuid4

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from rest_framework_simplejwt.tokens import RefreshToken

from apps.goods.models import GoodsInterest, GoodsListing
from apps.health.models import HealthProfessional, HealthQuestion, HealthReply
from apps.users.models import User, UserProfile
from apps.volunteer.models import VolunteerOpportunity, VolunteerProfile, VolunteerSignup


def create_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1280,1000")
    options.add_argument("--disable-dev-shm-usage")
    options.set_capability("goog:loggingPrefs", {"browser": "ALL"})

    driver_path = os.environ.get("CHROMEDRIVER")
    service = Service(executable_path=driver_path) if driver_path else Service()
    return webdriver.Chrome(service=service, options=options)


@pytest.fixture
def browser(live_server):
    driver = create_driver()
    driver.implicitly_wait(2)
    yield driver
    driver.quit()


@pytest.fixture
def user_factory(db):
    def create_user(role="Citizen", **fields):
        suffix = uuid4().hex[:8]
        return User.objects.create_user(
            phone_number=f"017{uuid4().int % 100_000_000:08d}",
            email=f"selenium-{suffix}@example.test",
            full_name=f"HELPNET Selenium {suffix}",
            password="TestPassword123",
            role=role,
            **fields,
        )

    return create_user


@pytest.fixture
def volunteer(user_factory):
    user = user_factory(role="Volunteer")
    VolunteerProfile.objects.create(user=user, skills="First aid")
    return user


@pytest.fixture
def coordinator(user_factory):
    user = user_factory(role="NGO")
    profile = UserProfile.objects.create(
        user=user,
        profile_type=UserProfile.Type.NGO,
        status=UserProfile.Status.ACTIVE,
        ngo_approval_status=UserProfile.NGOApprovalStatus.APPROVED,
        ngo_verification_status=UserProfile.NGOVerificationStatus.APPROVED,
    )
    user.active_profile = profile
    user.save(update_fields=["active_profile"])
    return user


@pytest.fixture
def opportunity(coordinator):
    return VolunteerOpportunity.objects.create(
        title="Selenium Community Cleanup",
        description="Help clean a local community space.",
        date=date.today() + timedelta(days=7),
        location="Dhaka",
        required_volunteers=5,
        coordinator=coordinator,
    )


def sign_in(browser, live_server, user):
    browser.get(f"{live_server.url}/")
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
    browser.execute_script(
        """
        localStorage.setItem("helpnet_token", arguments[0]);
        localStorage.setItem("helpnet_user", JSON.stringify(arguments[1]));
        localStorage.setItem("helpnet_lang", "en");
        """,
        access_token,
        user_data,
    )


def wait_for(browser, selector):
    return WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
    )


def enter_date(browser, element_id, value):
    browser.execute_script(
        """
        const field = document.getElementById(arguments[0]);
        field.value = arguments[1];
        field.dispatchEvent(new Event("input", { bubbles: true }));
        field.dispatchEvent(new Event("change", { bubbles: true }));
        """,
        element_id,
        value,
    )


def test_home_page_loads(browser, live_server):
    browser.get(f"{live_server.url}/")

    assert browser.title
    assert browser.find_element(By.TAG_NAME, "body").text.strip()


def test_volunteer_can_sign_up_for_open_opportunity(
    browser, live_server, volunteer, opportunity
):
    sign_in(browser, live_server, volunteer)
    browser.get(f"{live_server.url}/volunteer-opportunities/")

    listing = wait_for(browser, "#opportunityList article")
    assert opportunity.title in listing.text
    listing.find_element(By.XPATH, ".//button[normalize-space()='Sign up']").click()

    WebDriverWait(browser, 10).until(
        lambda driver: "successfully" in driver.find_element(
            By.ID, "volunteerMessage"
        ).text.lower()
    )
    assert VolunteerSignup.objects.filter(
        volunteer=volunteer, event=opportunity
    ).exists()


def test_volunteer_profile_can_be_saved(browser, live_server, volunteer):
    sign_in(browser, live_server, volunteer)
    browser.get(f"{live_server.url}/volunteer-profile/")

    skills = wait_for(browser, "#skills")
    skills.clear()
    skills.send_keys("First aid, teaching")
    availability = browser.find_element(By.ID, "availability")
    availability.clear()
    availability.send_keys("Weekends")
    browser.find_element(By.ID, "volunteerLocation").send_keys("Dhaka")
    browser.find_element(By.ID, "volunteerBloodGroup").send_keys("A+")
    browser.find_element(By.ID, "certificates").send_keys("First aid course")
    browser.find_element(
        By.CSS_SELECTOR, "#volunteerProfileForm button"
    ).click()

    WebDriverWait(browser, 10).until(
        lambda driver: "saved" in driver.find_element(
            By.ID, "profileMessage"
        ).text.lower()
    )
    volunteer_profile = VolunteerProfile.objects.get(user=volunteer)
    assert volunteer_profile.skills == "First aid, teaching"
    assert volunteer_profile.availability == "Weekends"
    assert volunteer_profile.location == "Dhaka"
    assert volunteer_profile.blood_group == "A+"
    assert volunteer_profile.supporting_certificates == "First aid course"


def test_approved_ngo_coordinator_can_create_opportunity(
    browser, live_server, coordinator
):
    sign_in(browser, live_server, coordinator)
    browser.get(f"{live_server.url}/create-opportunity/")

    browser.find_element(By.ID, "eventTitle").send_keys("Community Garden")
    browser.find_element(By.ID, "eventDescription").send_keys(
        "Prepare planting beds for the neighborhood."
    )
    enter_date(
        browser,
        "eventDate",
        (date.today() + timedelta(days=10)).isoformat(),
    )
    browser.find_element(By.ID, "eventLocation").send_keys("Dhaka")
    browser.find_element(By.ID, "eventRequired").send_keys("4")
    browser.find_element(
        By.CSS_SELECTOR, "#opportunityForm button[type='submit']"
    ).click()

    notice = WebDriverWait(browser, 10).until(
        lambda driver: driver.find_element(By.ID, "volunteerMessage").text
    )
    assert "created" in notice.lower(), notice
    event = VolunteerOpportunity.objects.get(title="Community Garden")
    assert event.coordinator == coordinator
    assert event.required_volunteers == 4


def test_non_coordinator_cannot_create_opportunity(
    browser, live_server, volunteer
):
    sign_in(browser, live_server, volunteer)
    browser.get(f"{live_server.url}/create-opportunity/")
    browser.find_element(By.ID, "eventTitle").send_keys("Not permitted")
    browser.find_element(By.ID, "eventDescription").send_keys("Test event")
    enter_date(
        browser,
        "eventDate",
        (date.today() + timedelta(days=10)).isoformat(),
    )
    browser.find_element(By.ID, "eventLocation").send_keys("Dhaka")
    browser.find_element(By.ID, "eventRequired").send_keys("2")
    browser.find_element(
        By.CSS_SELECTOR, "#opportunityForm button[type='submit']"
    ).click()

    WebDriverWait(browser, 10).until(
        lambda driver: "approved ngo coordinators" in driver.find_element(
            By.ID, "volunteerMessage"
        ).text.lower()
    )
    assert not VolunteerOpportunity.objects.filter(
        title="Not permitted"
    ).exists()


def test_user_can_create_goods_listing(browser, live_server, user_factory):
    seller = user_factory()
    sign_in(browser, live_server, seller)
    browser.get(f"{live_server.url}/create-goods/")

    browser.find_element(By.ID, "goodsTitle").send_keys("Study desk")
    browser.find_element(By.ID, "goodsDescription").send_keys(
        "A sturdy desk in good condition."
    )
    Select(browser.find_element(By.ID, "goodsCondition")).select_by_visible_text(
        "Good"
    )
    browser.find_element(By.ID, "goodsPrice").send_keys("1200")
    browser.find_element(By.ID, "goodsLocation").send_keys("Dhaka")
    validity = browser.execute_script(
        """
        const form = document.querySelector("#goodsCreateForm");
        return {
            valid: form.checkValidity(),
            fields: [...form.elements].map(field => ({
                id: field.id,
                value: field.value,
                valid: field.checkValidity(),
                message: field.validationMessage,
            })),
        };
        """
    )
    assert validity["valid"], validity
    browser.find_element(
        By.CSS_SELECTOR, "#goodsCreateForm button[type='submit']"
    ).click()

    try:
        WebDriverWait(browser, 10).until(
            lambda driver: "/goods-details/" in driver.current_url
            or driver.execute_script(
                "return document.getElementById('goodsMessage')?.textContent || ''"
            )
        )
    except TimeoutException as error:
        pytest.fail(
            f"Goods create form did not finish: url={browser.current_url!r}, "
            f"body={browser.find_element(By.TAG_NAME, 'body').text[:500]!r}, "
            f"logs={browser.get_log('browser')!r}, "
            f"cause={error}"
        )
    assert "/goods-details/" in browser.current_url, (
        browser.find_element(By.ID, "goodsMessage").text,
        browser.get_log("browser"),
        browser.execute_script(
            "return document.querySelector('#goodsCreateForm').checkValidity()"
        ),
    )
    listing = GoodsListing.objects.get(title="Study desk")
    assert listing.seller == seller
    assert listing.condition == GoodsListing.Condition.GOOD
    assert listing.location == "Dhaka"


def test_user_can_express_interest_in_another_users_goods(
    browser, live_server, user_factory
):
    seller = user_factory()
    buyer = user_factory()
    listing = GoodsListing.objects.create(
        seller=seller,
        title="Used bicycle",
        description="Ready to ride.",
        condition=GoodsListing.Condition.GOOD,
        asking_price="4500.00",
        location="Dhaka",
    )
    sign_in(browser, live_server, buyer)
    browser.get(
        f"{live_server.url}/goods-details/?listing_id={listing.pk}"
    )
    interest_button = wait_for(browser, "#goodsInterestButton")
    WebDriverWait(browser, 10).until(
        lambda driver: not interest_button.get_attribute("disabled")
    )
    interest_button.click()

    WebDriverWait(browser, 10).until(
        lambda driver: "interest" in driver.find_element(
            By.ID, "goodsMessage"
        ).text.lower()
    )
    assert GoodsInterest.objects.filter(
        listing=listing, interested_user=buyer
    ).exists()


def test_user_can_create_and_reply_to_health_question(
    browser, live_server, user_factory
):
    author = user_factory()
    sign_in(browser, live_server, author)
    browser.get(f"{live_server.url}/create-health-question/")

    browser.find_element(By.ID, "healthTitle").send_keys(
        "Where can I find a local clinic?"
    )
    browser.find_element(By.ID, "healthDescription").send_keys(
        "Looking for a clinic in my area."
    )
    browser.find_element(By.ID, "healthCategory").send_keys("Local services")
    browser.find_element(
        By.CSS_SELECTOR, "#healthQuestionForm button[type='submit']"
    ).click()

    WebDriverWait(browser, 10).until(
        EC.url_contains("/health-question-details/?question_id=")
    )
    question = HealthQuestion.objects.get(
        title="Where can I find a local clinic?"
    )
    assert question.author == author

    browser.find_element(By.ID, "healthReply").send_keys(
        "Check the community health center directory."
    )
    browser.find_element(
        By.CSS_SELECTOR, "#healthReplyForm button[type='submit']"
    ).click()
    WebDriverWait(browser, 10).until(
        lambda driver: "community health center" in driver.find_element(
            By.ID, "healthReplies"
        ).text.lower()
    )
    assert HealthReply.objects.filter(
        question=question,
        author=author,
        reply="Check the community health center directory.",
    ).exists()


def test_health_directory_only_shows_verified_professionals(
    browser, live_server, user_factory
):
    viewer = user_factory()
    HealthProfessional.objects.create(
        name="Verified Doctor",
        profession="Doctor",
        contact="verified@example.test",
        verification_status=HealthProfessional.VerificationStatus.VERIFIED,
    )
    HealthProfessional.objects.create(
        name="Pending Applicant",
        profession="Doctor",
        contact="pending@example.test",
        verification_status=HealthProfessional.VerificationStatus.PENDING,
    )
    sign_in(browser, live_server, viewer)
    browser.get(f"{live_server.url}/health-professionals/")

    directory = wait_for(browser, "#healthProfessionals")
    WebDriverWait(browser, 10).until(
        lambda driver: "Verified Doctor" in directory.text
    )
    assert "Pending Applicant" not in directory.text
