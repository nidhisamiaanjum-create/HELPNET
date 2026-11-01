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
from selenium.webdriver.support.ui import Select, WebDriverWait
from rest_framework_simplejwt.tokens import RefreshToken

from apps.farmer.models import ProduceListing
from apps.ratings.models import Rating
from apps.reports.models import Report
from apps.users.models import UserProfile
from apps.volunteer.models import (
    VolunteerMessage,
    VolunteerOpportunity,
    VolunteerProfile,
    VolunteerSignup,
)
from apps.waste.models import WastePickupRequest


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
    def create_user(role=User.Role.CITIZEN, **fields):
        suffix = uuid4().hex[:10]
        return User.objects.create_user(
            phone_number=f"017{uuid4().int % 100_000_000:08d}",
            email=f"selenium-{suffix}@example.test",
            full_name=f"HELPNET Selenium {suffix}",
            password=PASSWORD,
            role=role,
            **fields,
        )

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


def test_citizen_can_submit_waste_pickup_request(
    browser, live_server, user_factory
):
    citizen = user_factory(location="Dhanmondi, Dhaka")
    collector = user_factory(
        role=User.Role.VOLUNTEER, location="Dhanmondi, Dhaka"
    )
    sign_in(browser, live_server, citizen)
    browser.get(f"{live_server.url}/waste-pickup/")
    wait = WebDriverWait(browser, WAIT)

    Select(wait.until(EC.presence_of_element_located((By.ID, "wasteType")))).select_by_value(
        "Organic"
    )
    browser.find_element(By.ID, "pickupArea").clear()
    browser.find_element(By.ID, "pickupArea").send_keys("Dhanmondi")
    browser.find_element(By.ID, "pickupLocation").send_keys(
        "Road 32, House 10"
    )
    browser.find_element(By.ID, "preferredTime").send_keys("10 AM")
    browser.find_element(By.ID, "notes").send_keys("Two bags of kitchen waste.")
    click_element(browser, browser.find_element(By.ID, "submitWasteBtn"))

    alert = wait.until(EC.visibility_of_element_located((By.ID, "wasteAlert")))
    wait.until(lambda driver: "successfully" in alert.text.lower())
    request = WastePickupRequest.objects.get(requester=citizen)
    assert request.waste_type == WastePickupRequest.WasteType.ORGANIC
    assert request.area == "Dhanmondi"
    assert request.location == "Road 32, House 10"
    assert request.preferred_pickup_time == "10 AM"
    assert request.notes == "Two bags of kitchen waste."
    assert request.status == WastePickupRequest.Status.REQUESTED

    requests = wait_for(browser, "#requestsList")
    wait.until(lambda driver: "organic" in requests.text.lower())
    assert "dhanmondi" in requests.text.lower()
    collectors = wait_for(browser, "#collectorsList")
    wait.until(lambda driver: collector.full_name in collectors.text)
    assert collector.full_name in collectors.text


def test_waste_pickup_validation_does_not_create_request(
    browser, live_server, user_factory
):
    citizen = user_factory()
    sign_in(browser, live_server, citizen)
    browser.get(f"{live_server.url}/waste-pickup/")
    click_element(browser, browser.find_element(By.ID, "submitWasteBtn"))

    error = wait_for(browser, "#wasteTypeError")
    WebDriverWait(browser, WAIT).until(lambda driver: error.text.strip())
    assert "select" in error.text.lower()
    assert not WastePickupRequest.objects.filter(requester=citizen).exists()


def test_citizen_can_rate_and_report_a_volunteer_collector(
    browser, live_server, user_factory
):
    citizen = user_factory()
    collector = user_factory(
        role=User.Role.VOLUNTEER, location="Mirpur, Dhaka"
    )
    sign_in(browser, live_server, citizen)
    browser.get(f"{live_server.url}/collector-details/?id={collector.user_id}")
    wait = WebDriverWait(browser, WAIT)

    wait.until(
        lambda driver: collector.full_name
        in driver.find_element(By.ID, "collectorName").text
    )
    browser.find_element(By.ID, "ratingComment").send_keys(
        "Reliable and punctual service."
    )
    click_element(browser, browser.find_element(By.ID, "submitRatingBtn"))
    alert = wait.until(
        EC.visibility_of_element_located((By.ID, "collectorAlert"))
    )
    wait.until(lambda driver: "rating has been submitted" in alert.text.lower())
    rating = Rating.objects.get(rater=citizen, rated_user=collector)
    assert rating.rating == 5
    assert rating.comment == "Reliable and punctual service."

    Select(browser.find_element(By.ID, "reportCategory")).select_by_value("no_show")
    browser.find_element(By.ID, "reportDescription").send_keys(
        "The collector did not arrive at the agreed time."
    )
    click_element(browser, browser.find_element(By.ID, "submitReportBtn"))
    wait.until(lambda driver: "report submitted" in alert.text.lower())
    report = Report.objects.get(reporter=citizen, reported_user=collector)
    assert report.category == Report.Category.NO_SHOW
    assert report.description == "The collector did not arrive at the agreed time."


def test_farmer_can_publish_produce_listing(browser, live_server, user_factory):
    farmer = user_factory(role=User.Role.FARMER, location="Savar, Dhaka")
    sign_in(browser, live_server, farmer)
    browser.get(f"{live_server.url}/create-produce/")
    browser.find_element(By.ID, "produceName").send_keys("Fresh red carrots")
    browser.find_element(By.ID, "producePrice").send_keys("75")
    browser.find_element(By.ID, "produceQuantity").send_keys("100 kg")
    location = browser.find_element(By.ID, "farmLocation")
    location.clear()
    location.send_keys("Savar, Dhaka")
    browser.find_element(By.ID, "produceDescription").send_keys(
        "Fresh harvest from the farm."
    )
    click_element(browser, browser.find_element(By.ID, "submitProduceBtn"))

    WebDriverWait(browser, WAIT).until(
        EC.url_contains("/farmer-market/")
    )
    grid = wait_for(browser, "#produceGrid")
    WebDriverWait(browser, WAIT).until(
        lambda driver: "fresh red carrots" in grid.text.lower()
    )
    listing = ProduceListing.objects.get(produce_name="Fresh red carrots")
    assert listing.farmer == farmer
    assert listing.price == 75
    assert listing.quantity == "100 kg"
    assert listing.location == "Savar, Dhaka"


def test_produce_form_validation_does_not_create_listing(
    browser, live_server, user_factory
):
    farmer = user_factory(role=User.Role.FARMER)
    sign_in(browser, live_server, farmer)
    browser.get(f"{live_server.url}/create-produce/")
    click_element(browser, browser.find_element(By.ID, "submitProduceBtn"))

    error = wait_for(browser, "#produceNameError")
    WebDriverWait(browser, WAIT).until(lambda driver: error.text.strip())
    assert "produce name" in error.text.lower()
    assert not ProduceListing.objects.filter(farmer=farmer).exists()


def test_marketplace_contact_respects_farmer_phone_privacy(
    browser, live_server, user_factory
):
    farmer = user_factory(role=User.Role.FARMER, is_phone_visible=False)
    listing = ProduceListing.objects.create(
        farmer=farmer,
        produce_name="Fresh red tomatoes",
        category="Vegetables",
        price="50.00",
        quantity="80 kg",
        location="Savar, Dhaka",
        description="Fresh tomatoes from the farm.",
    )
    consumer = user_factory()
    sign_in(browser, live_server, consumer)
    browser.get(f"{live_server.url}/produce-details/?id={listing.pk}")

    title = wait_for(browser, "#detailTitle")
    WebDriverWait(browser, WAIT).until(
        lambda driver: "fresh red tomatoes" in title.text.lower()
    )
    assert farmer.full_name in browser.find_element(By.ID, "farmerName").text
    assert "contact through helpnet profile" in browser.find_element(
        By.ID, "farmerPhone"
    ).text.lower()
    assert farmer.phone_number not in browser.find_element(
        By.ID, "farmerPhone"
    ).text
    body = browser.find_element(By.TAG_NAME, "body").text.lower()
    assert "helpnet does not handle payment or delivery" in body
    assert "between the farmer and consumer" in body


def test_farmer_pages_remain_usable_on_mobile_and_show_disclaimer(
    browser, live_server, user_factory
):
    farmer = user_factory(role=User.Role.FARMER)
    sign_in(browser, live_server, farmer)
    browser.set_window_size(390, 844)
    browser.get(f"{live_server.url}/create-produce/")

    submit = wait_for(browser, "#submitProduceBtn")
    assert submit.is_displayed()
    assert submit.is_enabled()
    assert len(browser.find_elements(By.TAG_NAME, "label")) >= 5

    browser.get(f"{live_server.url}/farmer-market/")
    search = wait_for(browser, "#marketSearchInput")
    assert search.is_displayed()
    body = browser.find_element(By.TAG_NAME, "body").text.lower()
    assert "helpnet does not handle payment or delivery" in body


def test_unauthenticated_user_is_redirected_from_protected_pages(
    browser, live_server
):
    browser.get(f"{live_server.url}/")
    browser.execute_script("localStorage.clear(); sessionStorage.clear();")

    browser.get(f"{live_server.url}/waste-pickup/")
    WebDriverWait(browser, WAIT).until(
        lambda driver: "/login/" in driver.current_url
    )
    assert "/login/" in browser.current_url

    browser.get(f"{live_server.url}/create-produce/")
    WebDriverWait(browser, WAIT).until(
        lambda driver: "/login/" in driver.current_url
    )
    assert "/login/" in browser.current_url


def test_only_event_participants_can_read_and_post_messages(
    browser, live_server, user_factory, approved_coordinator
):
    volunteer = user_factory(role=User.Role.VOLUNTEER)
    outsider = user_factory(role=User.Role.VOLUNTEER)
    event = VolunteerOpportunity.objects.create(
        title="Flood Relief Distribution",
        description="Distribute relief materials.",
        date=date.today() + timedelta(days=8),
        location="Sylhet",
        required_volunteers=5,
        coordinator=approved_coordinator,
    )
    VolunteerSignup.objects.create(volunteer=volunteer, event=event)
    VolunteerMessage.objects.create(
        sender=approved_coordinator,
        event=event,
        message="Meet at the central shelter at 8 AM.",
    )

    sign_in(browser, live_server, outsider)
    browser.get(
        f"{live_server.url}/volunteer-message/?event_id={event.pk}"
    )
    notice = wait_for(browser, "#volunteerMessage")
    WebDriverWait(browser, WAIT).until(
        lambda driver: "sign up for this event" in notice.text.lower()
    )
    message_list = wait_for(browser, "#messageList")
    assert "central shelter" not in message_list.text.lower()

    browser.find_element(By.ID, "eventMessage").send_keys(
        "Unauthorized event message."
    )
    click_element(browser, browser.find_element(By.ID, "sendMessageBtn"))
    WebDriverWait(browser, WAIT).until(
        lambda driver: "only event participants" in notice.text.lower()
        or "sign up" in notice.text.lower()
    )
    assert not VolunteerMessage.objects.filter(
        event=event, message="Unauthorized event message."
    ).exists()
    assert "unauthorized event message" not in message_list.text.lower()

    sign_in(browser, live_server, volunteer)
    browser.get(
        f"{live_server.url}/volunteer-opportunity-details/?event_id={event.pk}"
    )
    thread_button = wait_for(browser, "#messageThreadBtn")
    click_element(browser, thread_button)
    WebDriverWait(browser, WAIT).until(
        EC.url_contains("/volunteer-message/")
    )
    message_list = wait_for(browser, "#messageList")
    WebDriverWait(browser, WAIT).until(
        lambda driver: "central shelter" in message_list.text.lower()
    )
    browser.find_element(By.ID, "eventMessage").send_keys(
        "I will arrive with emergency supplies."
    )
    click_element(browser, browser.find_element(By.ID, "sendMessageBtn"))
    WebDriverWait(browser, WAIT).until(
        lambda driver: "emergency supplies" in message_list.text.lower()
    )
    assert VolunteerMessage.objects.filter(
        event=event,
        sender=volunteer,
        message="I will arrive with emergency supplies.",
    ).exists()
