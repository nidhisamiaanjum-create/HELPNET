import os
from datetime import date, timedelta
from uuid import uuid4

import pytest
from django.contrib.auth import get_user_model
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from rest_framework_simplejwt.tokens import RefreshToken

from apps.blood.models import BloodRequest
from apps.farmer.models import ProduceListing
from apps.health.models import HealthProfessional
from apps.reports.models import Report
from apps.users.models import UserProfile
from apps.volunteer.models import (
    VolunteerAttendance,
    VolunteerOpportunity,
    VolunteerProfile,
    VolunteerSignup,
)


User = get_user_model()
PASSWORD = "Selenium-test-42!"
WAIT = 10


def create_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,1000")
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
    def create_user(role=User.Role.CITIZEN, *, superuser=False, **fields):
        suffix = uuid4().hex[:10]
        user_fields = {
            "phone_number": f"017{uuid4().int % 100_000_000:08d}",
            "email": f"selenium-{suffix}@example.test",
            "full_name": f"HELPNET Selenium {suffix}",
            "role": role,
            **fields,
        }
        if superuser:
            return User.objects.create_superuser(
                password=PASSWORD, **user_fields
            )
        return User.objects.create_user(password=PASSWORD, **user_fields)

    return create_user


@pytest.fixture
def approved_coordinator(user_factory):
    user = user_factory(role=User.Role.NGO)
    UserProfile.objects.create(
        user=user,
        profile_type=UserProfile.Type.NGO,
        status=UserProfile.Status.ACTIVE,
        ngo_approval_status=UserProfile.NGOApprovalStatus.APPROVED,
    )
    return user


@pytest.fixture
def volunteer(user_factory):
    user = user_factory(role=User.Role.VOLUNTEER, location="Dhanmondi, Dhaka")
    VolunteerProfile.objects.create(user=user, skills="First aid")
    return user


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


def wait_for(browser, selector):
    return WebDriverWait(browser, WAIT).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
    )


def click_element(browser, element):
    browser.execute_script(
        "arguments[0].scrollIntoView({block: 'center'});", element
    )
    try:
        element.click()
    except Exception:
        browser.execute_script("arguments[0].click();", element)


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


def test_user_can_report_a_blood_request(browser, live_server, user_factory):
    reporter = user_factory()
    requester = user_factory()
    request = BloodRequest.objects.create(
        requester=requester,
        blood_group="A+",
        area="Dhanmondi",
        hospital="Community Hospital",
        details="Urgent request for a patient.",
    )
    sign_in(browser, live_server, reporter)
    browser.get(f"{live_server.url}/blood/")

    card = WebDriverWait(browser, WAIT).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "#requestList .blood-request-item")
        )
    )
    form = card.find_element(By.CSS_SELECTOR, ".blood-report-form")
    form.find_element(By.TAG_NAME, "textarea").send_keys(
        "Please verify this request."
    )
    click_element(
        browser, form.find_element(By.CSS_SELECTOR, "button[type='submit']")
    )

    WebDriverWait(browser, WAIT).until(
        lambda driver: "success" in form.find_element(
            By.CSS_SELECTOR, ".form-message"
        ).get_attribute("class")
    )
    report = Report.objects.get(reporter=reporter)
    assert report.description == "Please verify this request."
    assert report.content_object == request
    assert report.reported_user == requester
    assert report.status == Report.Status.PENDING


def test_superuser_can_review_a_report(browser, live_server, user_factory):
    reporter = user_factory()
    requester = user_factory()
    request = BloodRequest.objects.create(
        requester=requester,
        blood_group="O+",
        area="Mirpur",
        hospital="City Clinic",
    )
    report = Report.objects.create(
        reporter=reporter,
        reported_user=requester,
        content_object=request,
        category=Report.Category.OTHER,
        description="Review this request.",
    )
    admin = user_factory(role=User.Role.ADMIN, superuser=True)
    sign_in(browser, live_server, admin)
    browser.get(f"{live_server.url}/admin-moderation/")

    card = wait_for(browser, f'#moderationReports [data-report-id="{report.pk}"]')
    click_element(browser, card.find_element(By.CSS_SELECTOR, "button.small-btn"))
    WebDriverWait(browser, WAIT).until(
        lambda driver: "success" in driver.find_element(
            By.ID, "moderationMessage"
        ).get_attribute("class")
    )
    report.refresh_from_db()
    assert report.status == Report.Status.REVIEWED


def test_regular_user_cannot_review_a_report(browser, live_server, user_factory):
    reporter = user_factory()
    requester = user_factory()
    request = BloodRequest.objects.create(
        requester=requester,
        blood_group="B+",
        area="Uttara",
        hospital="General Hospital",
    )
    report = Report.objects.create(
        reporter=reporter,
        reported_user=requester,
        content_object=request,
        category=Report.Category.OTHER,
        description="This must remain pending.",
    )
    sign_in(browser, live_server, reporter)
    browser.get(f"{live_server.url}/admin-moderation/")
    response = browser.execute_async_script(
        """
        const requestId = arguments[0];
        const done = arguments[1];
        fetch("/api/reports/moderation/", {
            method: "POST",
            headers: {
                "Authorization": `Bearer ${localStorage.getItem("helpnet_token")}`,
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                report_id: requestId,
                action: "review",
                reason: "Attempt by a regular user",
            }),
        }).then(response => done(response.status), () => done(0));
        """,
        str(report.pk),
    )
    assert response == 403
    report.refresh_from_db()
    assert report.status == Report.Status.PENDING


def test_health_directory_only_lists_verified_professionals(
    browser, live_server, user_factory
):
    viewer = user_factory()
    HealthProfessional.objects.create(
        name="Verified Community Doctor",
        profession="Doctor",
        contact="verified@example.test",
        verification_status=HealthProfessional.VerificationStatus.VERIFIED,
    )
    HealthProfessional.objects.create(
        name="Pending Doctor",
        profession="Doctor",
        contact="pending@example.test",
        verification_status=HealthProfessional.VerificationStatus.PENDING,
    )
    sign_in(browser, live_server, viewer)
    browser.get(f"{live_server.url}/health-professionals/")

    directory = wait_for(browser, "#healthProfessionals")
    WebDriverWait(browser, WAIT).until(
        lambda driver: "Verified Community Doctor" in directory.text
    )
    assert "Pending Doctor" not in directory.text


def test_farmer_price_range_uses_other_active_local_listings(
    browser, live_server, user_factory
):
    farmer = user_factory(role=User.Role.FARMER)
    ProduceListing.objects.create(
        farmer=farmer,
        produce_name="Local tomatoes",
        category="Vegetables",
        price="50.00",
        quantity="20 kg",
        location="Dhanmondi",
    )
    for price in ("60.00", "80.00"):
        ProduceListing.objects.create(
            farmer=user_factory(role=User.Role.FARMER),
            produce_name=f"Market tomatoes {price}",
            category="Vegetables",
            price=price,
            quantity="30 kg",
            location="Dhanmondi",
        )
    listing = ProduceListing.objects.filter(farmer=farmer).get()
    viewer = user_factory()
    sign_in(browser, live_server, viewer)
    browser.get(f"{live_server.url}/produce-details/?id={listing.pk}")

    price_range = wait_for(browser, "#farmerPriceRange")
    WebDriverWait(browser, WAIT).until(
        lambda driver: "60" in price_range.text and "80" in price_range.text
    )
    assert "60" in price_range.text
    assert "80" in price_range.text


def test_approved_ngo_can_create_opportunity(
    browser, live_server, approved_coordinator
):
    sign_in(browser, live_server, approved_coordinator)
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
    click_element(
        browser,
        browser.find_element(
            By.CSS_SELECTOR, "#opportunityForm button[type='submit']"
        ),
    )

    WebDriverWait(browser, WAIT).until(
        lambda driver: "created" in driver.find_element(
            By.ID, "volunteerMessage"
        ).text.lower()
    )
    event = VolunteerOpportunity.objects.get(title="Community Garden")
    assert event.coordinator == approved_coordinator
    assert event.required_volunteers == 4


def test_citizen_cannot_create_volunteer_opportunity(browser, live_server, user_factory):
    citizen = user_factory(role=User.Role.CITIZEN)
    sign_in(browser, live_server, citizen)
    browser.get(f"{live_server.url}/create-opportunity/")
    browser.find_element(By.ID, "eventTitle").send_keys("Unauthorized event")
    browser.find_element(By.ID, "eventDescription").send_keys("Should be rejected.")
    enter_date(
        browser,
        "eventDate",
        (date.today() + timedelta(days=10)).isoformat(),
    )
    browser.find_element(By.ID, "eventLocation").send_keys("Dhaka")
    browser.find_element(By.ID, "eventRequired").send_keys("2")
    click_element(
        browser,
        browser.find_element(
            By.CSS_SELECTOR, "#opportunityForm button[type='submit']"
        ),
    )

    notice = wait_for(browser, "#volunteerMessage")
    WebDriverWait(browser, WAIT).until(
        lambda driver: "approved ngo coordinators" in notice.text.lower()
    )
    assert not VolunteerOpportunity.objects.filter(
        title="Unauthorized event"
    ).exists()


def test_volunteer_signup_is_saved_once_and_duplicate_control_disappears(
    browser, live_server, volunteer, approved_coordinator
):
    event = VolunteerOpportunity.objects.create(
        title="Neighborhood Cleanup",
        description="Clean the local park.",
        date=date.today() + timedelta(days=7),
        location="Dhanmondi",
        required_volunteers=5,
        coordinator=approved_coordinator,
    )
    sign_in(browser, live_server, volunteer)
    browser.get(f"{live_server.url}/volunteer-opportunities/")

    card = WebDriverWait(browser, WAIT).until(
        lambda driver: next(
            (
                article
                for article in driver.find_elements(
                    By.CSS_SELECTOR, "#opportunityList article"
                )
                if event.title in article.text
            ),
            False,
        )
    )
    click_element(
        browser,
        card.find_element(By.XPATH, ".//button[normalize-space()='Sign up']"),
    )
    WebDriverWait(browser, WAIT).until(
        lambda driver: "successfully" in driver.find_element(
            By.ID, "volunteerMessage"
        ).text.lower()
    )
    assert VolunteerSignup.objects.filter(
        volunteer=volunteer, event=event
    ).count() == 1

    browser.refresh()
    card = WebDriverWait(browser, WAIT).until(
        lambda driver: next(
            (
                article
                for article in driver.find_elements(
                    By.CSS_SELECTOR, "#opportunityList article"
                )
                if event.title in article.text
            ),
            False,
        )
    )
    assert "signed up" in card.text.lower()
    assert not card.find_elements(
        By.XPATH, ".//button[normalize-space()='Sign up']"
    )
    assert VolunteerSignup.objects.filter(
        volunteer=volunteer, event=event
    ).count() == 1


def test_volunteer_profile_can_be_saved(browser, live_server, volunteer):
    sign_in(browser, live_server, volunteer)
    browser.get(f"{live_server.url}/volunteer-profile/")

    skills = wait_for(browser, "#skills")
    skills.clear()
    skills.send_keys("First aid, teaching")
    browser.find_element(By.ID, "availability").send_keys("Weekends")
    browser.find_element(By.ID, "volunteerLocation").send_keys("Dhaka")
    browser.find_element(By.ID, "volunteerBloodGroup").send_keys("A+")
    browser.find_element(By.ID, "certificates").send_keys("First aid course")
    click_element(
        browser,
        browser.find_element(
            By.CSS_SELECTOR, "#volunteerProfileForm button"
        ),
    )

    WebDriverWait(browser, WAIT).until(
        lambda driver: "saved" in driver.find_element(
            By.ID, "profileMessage"
        ).text.lower()
    )
    profile = VolunteerProfile.objects.get(user=volunteer)
    assert profile.skills == "First aid, teaching"
    assert profile.availability == "Weekends"
    assert profile.location == "Dhaka"
    assert profile.blood_group == "A+"
    assert profile.supporting_certificates == "First aid course"


def test_coordinator_cannot_check_in_a_volunteer_twice(
    browser, live_server, volunteer, approved_coordinator
):
    event = VolunteerOpportunity.objects.create(
        title="Food Distribution",
        description="Prepare and distribute food packages.",
        date=date.today() + timedelta(days=5),
        location="Dhaka",
        required_volunteers=2,
        coordinator=approved_coordinator,
    )
    VolunteerSignup.objects.create(volunteer=volunteer, event=event)
    sign_in(browser, live_server, approved_coordinator)
    browser.get(
        f"{live_server.url}/volunteer-attendance/?event_id={event.pk}"
    )

    row = wait_for(browser, "#attendanceList article")
    click_element(
        browser,
        row.find_element(By.XPATH, ".//button[normalize-space()='Check in']"),
    )
    WebDriverWait(browser, WAIT).until(
        lambda driver: VolunteerAttendance.objects.filter(
            event=event, volunteer=volunteer, check_in_time__isnull=False
        ).exists()
    )
    attendance = VolunteerAttendance.objects.get(event=event, volunteer=volunteer)
    first_check_in = attendance.check_in_time

    row = wait_for(browser, "#attendanceList article")
    click_element(
        browser,
        row.find_element(By.XPATH, ".//button[normalize-space()='Check in']"),
    )
    WebDriverWait(browser, WAIT).until(
        lambda driver: "already checked in" in driver.find_element(
            By.ID, "volunteerMessage"
        ).text.lower()
    )
    attendance.refresh_from_db()
    assert attendance.check_in_time == first_check_in
    assert VolunteerAttendance.objects.filter(event=event, volunteer=volunteer).count() == 1


def test_ngo_search_filters_volunteers_by_multiple_fields(
    browser, live_server, user_factory, approved_coordinator
):
    matching = user_factory(role=User.Role.VOLUNTEER)
    VolunteerProfile.objects.create(
        user=matching,
        skills="First aid and logistics",
        availability="Weekends",
        location="Dhanmondi",
        blood_group="A+",
    )
    other = user_factory(role=User.Role.VOLUNTEER)
    VolunteerProfile.objects.create(
        user=other,
        skills="Teaching",
        availability="Weekdays",
        location="Mirpur",
    )
    sign_in(browser, live_server, approved_coordinator)
    browser.get(f"{live_server.url}/volunteer-search/")

    browser.find_element(By.ID, "searchSkills").send_keys("first aid")
    browser.find_element(By.ID, "searchAvailability").send_keys("weekends")
    browser.find_element(By.ID, "searchLocation").send_keys("dhanmondi")
    browser.find_element(By.ID, "searchParticipation").send_keys("no")
    click_element(
        browser,
        browser.find_element(
            By.CSS_SELECTOR, "#volunteerSearchForm button"
        ),
    )
    results = wait_for(browser, "#volunteerSearchResults")
    WebDriverWait(browser, WAIT).until(
        lambda driver: matching.full_name in results.text
    )
    assert matching.full_name in results.text
    assert other.full_name not in results.text


def test_superuser_can_filter_and_export_volunteer_records(
    browser, live_server, user_factory
):
    admin = user_factory(role=User.Role.ADMIN, superuser=True)
    volunteer_user = user_factory(role=User.Role.VOLUNTEER)
    VolunteerProfile.objects.create(
        user=volunteer_user,
        skills="First aid",
        availability="Weekends",
        location="Dhaka",
        blood_group="O+",
    )
    sign_in(browser, live_server, admin)
    browser.get(f"{live_server.url}/admin-volunteers/")
    results = wait_for(browser, "#adminVolunteerResults")
    WebDriverWait(browser, WAIT).until(
        lambda driver: volunteer_user.full_name
        in driver.find_element(By.ID, "adminVolunteerResults").text
    )
    browser.find_element(By.ID, "adminSkills").send_keys("first aid")
    browser.find_element(By.ID, "adminBloodGroup").send_keys("O+")
    click_element(
        browser,
        browser.find_element(
            By.CSS_SELECTOR, "#adminVolunteerFilter button:first-of-type"
        ),
    )
    WebDriverWait(browser, WAIT).until(
        lambda driver: volunteer_user.full_name
        in driver.find_element(By.ID, "adminVolunteerResults").text
    )

    browser.execute_script(
        """
        window.URL.createObjectURL = () => "blob:test";
        HTMLAnchorElement.prototype.click = function () {};
        """
    )
    click_element(browser, browser.find_element(By.ID, "exportVolunteers"))
    WebDriverWait(browser, WAIT).until(
        lambda driver: "csv downloaded" in driver.find_element(
            By.ID, "adminVolunteerMessage"
        ).text.lower()
    )
    assert volunteer_user.full_name in browser.find_element(
        By.ID, "adminVolunteerResults"
    ).text


def test_language_toggle_switches_between_supported_languages(browser, live_server):
    browser.get(f"{live_server.url}/")
    toggle = wait_for(browser, "#langToggle")
    initial_language = browser.execute_script(
        "return document.documentElement.lang"
    )
    click_element(browser, toggle)
    WebDriverWait(browser, WAIT).until(
        lambda driver: driver.execute_script(
            "return document.documentElement.lang"
        )
        != initial_language
    )
    changed_language = browser.execute_script(
        "return document.documentElement.lang"
    )
    assert changed_language in {"en", "bn"}
    click_element(browser, browser.find_element(By.ID, "langToggle"))
    WebDriverWait(browser, WAIT).until(
        lambda driver: driver.execute_script(
            "return document.documentElement.lang"
        )
        == initial_language
    )
