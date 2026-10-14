import time
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from django.contrib.auth import get_user_model
from apps.farmer.models import ProduceListing
from apps.waste.models import WastePickupRequest
from apps.volunteer.models import VolunteerOpportunity, VolunteerSignup, VolunteerMessage

User = get_user_model()


@pytest.fixture(scope="function")
def driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,1000")
    options.set_capability("goog:loggingPrefs", {"browser": "ALL"})

    driver_inst = webdriver.Chrome(options=options)
    driver_inst.implicitly_wait(4)
    yield driver_inst
    driver_inst.quit()


@pytest.fixture
def citizen_user(db):
    user, _ = User.objects.get_or_create(
        phone_number="01711112222",
        defaults={
            "email": "citizen_shakil@example.com",
            "full_name": "Citizen Shakil",
            "role": User.Role.CITIZEN,
            "location": "Dhanmondi, Dhaka",
            "is_phone_visible": True,
        },
    )
    user.set_password("Password123!")
    user.save()
    return user


@pytest.fixture
def farmer_user(db):
    user, _ = User.objects.get_or_create(
        phone_number="01722223333",
        defaults={
            "email": "farmer_shakil@example.com",
            "full_name": "Farmer Shakil",
            "role": User.Role.FARMER,
            "location": "Savar, Dhaka",
            "is_phone_visible": True,
        },
    )
    user.set_password("Password123!")
    user.save()
    return user


@pytest.fixture
def collector_user(db):
    user, _ = User.objects.get_or_create(
        phone_number="01733334444",
        defaults={
            "email": "collector_shakil@example.com",
            "full_name": "Collector Shakil",
            "role": User.Role.VOLUNTEER,
            "location": "Dhanmondi, Dhaka",
            "is_phone_visible": True,
        },
    )
    user.set_password("Password123!")
    user.save()
    return user


@pytest.fixture
def ngo_user(db):
    user, _ = User.objects.get_or_create(
        phone_number="01755556666",
        defaults={
            "email": "ngo_shakil@example.com",
            "full_name": "NGO Shakil Coordinator",
            "role": User.Role.NGO,
            "location": "Dhanmondi, Dhaka",
            "is_phone_visible": True,
        },
    )
    user.set_password("Password123!")
    user.save()
    return user


@pytest.fixture
def non_signed_up_volunteer(db):
    user, _ = User.objects.get_or_create(
        phone_number="01766667777",
        defaults={
            "email": "outsider_shakil@example.com",
            "full_name": "Outsider Volunteer Shakil",
            "role": User.Role.VOLUNTEER,
            "location": "Gulshan, Dhaka",
            "is_phone_visible": True,
        },
    )
    user.set_password("Password123!")
    user.save()
    return user


@pytest.fixture
def signed_up_volunteer(db):
    user, _ = User.objects.get_or_create(
        phone_number="01777778888",
        defaults={
            "email": "member_shakil@example.com",
            "full_name": "Member Volunteer Shakil",
            "role": User.Role.VOLUNTEER,
            "location": "Mirpur, Dhaka",
            "is_phone_visible": True,
        },
    )
    user.set_password("Password123!")
    user.save()
    return user


def perform_login(driver, base_url, phone_number, password):
    driver.get(f"{base_url}/login/")
    wait = WebDriverWait(driver, 10)
    
    identifier_input = wait.until(EC.presence_of_element_located((By.ID, "identifier")))
    password_input = wait.until(EC.presence_of_element_located((By.ID, "password")))
    login_btn = wait.until(EC.presence_of_element_located((By.ID, "loginButton")))

    identifier_input.clear()
    identifier_input.send_keys(phone_number)
    password_input.clear()
    password_input.send_keys(password)

    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", login_btn)
    time.sleep(0.3)
    driver.execute_script("arguments[0].click();", login_btn)

    wait.until(lambda d: "/dashboard/" in d.current_url or "/admin-dashboard/" in d.current_url)


def click_element(driver, element):
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
    time.sleep(0.2)
    try:
        element.click()
    except Exception:
        driver.execute_script("arguments[0].click();", element)


# ==============================================================================
# ST 41 — Waste Pickup Tests
# ==============================================================================

@pytest.mark.django_db(transaction=True)
def test_waste_pickup_success(driver, live_server, citizen_user, collector_user):
    """ST 41: Login as citizen, create a waste pickup request, verify success & collector display."""
    perform_login(driver, live_server.url, citizen_user.phone_number, "Password123!")

    driver.get(f"{live_server.url}/waste-pickup/")
    wait = WebDriverWait(driver, 10)

    # Fill pickup request form
    waste_type_select = wait.until(EC.presence_of_element_located((By.ID, "wasteType")))
    area_input = driver.find_element(By.ID, "pickupArea")
    location_input = driver.find_element(By.ID, "pickupLocation")
    time_input = driver.find_element(By.ID, "preferredTime")
    notes_input = driver.find_element(By.ID, "notes")
    submit_btn = driver.find_element(By.ID, "submitWasteBtn")

    from selenium.webdriver.support.ui import Select
    Select(waste_type_select).select_by_value("Organic")

    area_input.clear()
    area_input.send_keys("Dhanmondi")

    location_input.clear()
    location_input.send_keys("Road 32, House 10, Dhanmondi, Dhaka")

    time_input.send_keys("10:00 AM")
    notes_input.send_keys("2 bags of kitchen waste ready for pickup")

    click_element(driver, submit_btn)

    # Verify success alert
    wait.until(lambda d: "successfully" in d.find_element(By.ID, "wasteAlert").text.lower())
    assert "successfully" in driver.find_element(By.ID, "wasteAlert").text.lower()

    # Verify request appears in my requests list
    wait.until(lambda d: "organic" in d.find_element(By.ID, "requestsList").text.lower() and "dhanmondi" in d.find_element(By.ID, "requestsList").text.lower())
    req_text_lower = driver.find_element(By.ID, "requestsList").text.lower()
    assert "organic" in req_text_lower
    assert "dhanmondi" in req_text_lower

    # Verify collector display in area match section
    wait.until(lambda d: collector_user.full_name.lower() in d.find_element(By.ID, "collectorsList").text.lower())
    assert collector_user.full_name.lower() in driver.find_element(By.ID, "collectorsList").text.lower()


@pytest.mark.django_db(transaction=True)
def test_waste_pickup_validation_error(driver, live_server, citizen_user):
    """ST 41 Negative Test: Submit waste pickup without required fields and verify validation error."""
    perform_login(driver, live_server.url, citizen_user.phone_number, "Password123!")

    driver.get(f"{live_server.url}/waste-pickup/")
    wait = WebDriverWait(driver, 10)

    # Submit without filling required fields
    submit_btn = wait.until(EC.presence_of_element_located((By.ID, "submitWasteBtn")))
    click_element(driver, submit_btn)

    # Verify field validation error is displayed
    wait.until(lambda d: d.find_element(By.ID, "wasteTypeError").text.strip() != "")
    assert driver.find_element(By.ID, "wasteTypeError").text.strip() != ""

    # Verify no request is created in DB
    assert WastePickupRequest.objects.count() == 0


# ==============================================================================
# ST 42 — Collector Rating/Report Tests
# ==============================================================================

@pytest.mark.django_db(transaction=True)
def test_collector_rating_and_report(driver, live_server, citizen_user, collector_user):
    """ST 42: Open collector details, submit rating, verify success, submit report, verify success."""
    perform_login(driver, live_server.url, citizen_user.phone_number, "Password123!")

    # Navigate to collector details page
    driver.get(f"{live_server.url}/collector-details/?id={collector_user.user_id}")
    wait = WebDriverWait(driver, 10)

    # Verify collector info loaded
    wait.until(lambda d: collector_user.full_name.lower() in d.find_element(By.ID, "collectorName").text.lower())

    # Submit Rating
    comment_input = driver.find_element(By.ID, "ratingComment")
    rating_submit_btn = driver.find_element(By.ID, "submitRatingBtn")

    comment_input.send_keys("Very punctual and clean service!")
    click_element(driver, rating_submit_btn)

    # Verify rating success alert
    wait.until(lambda d: "submitted" in d.find_element(By.ID, "collectorAlert").text.lower() or "rating" in d.find_element(By.ID, "collectorAlert").text.lower())
    assert "submitted" in driver.find_element(By.ID, "collectorAlert").text.lower() or "rating" in driver.find_element(By.ID, "collectorAlert").text.lower()

    # Submit Report
    from selenium.webdriver.support.ui import Select
    report_cat_select = driver.find_element(By.ID, "reportCategory")
    report_desc_input = driver.find_element(By.ID, "reportDescription")
    report_submit_btn = driver.find_element(By.ID, "submitReportBtn")

    Select(report_cat_select).select_by_value("no_show")
    report_desc_input.clear()
    report_desc_input.send_keys("Collector did not show up at scheduled pickup time.")

    click_element(driver, report_submit_btn)

    # Verify report success alert
    wait.until(lambda d: "report submitted" in d.find_element(By.ID, "collectorAlert").text.lower() or "team will review" in d.find_element(By.ID, "collectorAlert").text.lower())
    assert "report submitted" in driver.find_element(By.ID, "collectorAlert").text.lower() or "team will review" in driver.find_element(By.ID, "collectorAlert").text.lower()


# ==============================================================================
# ST 43 — Farmer Produce Listing Tests
# ==============================================================================

@pytest.mark.django_db(transaction=True)
def test_produce_listing_success(driver, live_server, farmer_user):
    """ST 43: Login as farmer, create produce listing, submit and verify in marketplace."""
    perform_login(driver, live_server.url, farmer_user.phone_number, "Password123!")

    driver.get(f"{live_server.url}/create-produce/")
    wait = WebDriverWait(driver, 10)

    name_input = wait.until(EC.presence_of_element_located((By.ID, "produceName")))
    price_input = driver.find_element(By.ID, "producePrice")
    quantity_input = driver.find_element(By.ID, "produceQuantity")
    location_input = driver.find_element(By.ID, "farmLocation")
    desc_input = driver.find_element(By.ID, "produceDescription")
    submit_btn = driver.find_element(By.ID, "submitProduceBtn")

    name_input.send_keys("Fresh Organic Carrots")
    price_input.send_keys("75")
    quantity_input.send_keys("100 kg")
    location_input.clear()
    location_input.send_keys("Savar, Dhaka")
    desc_input.send_keys("100% chemical free fresh harvest.")

    click_element(driver, submit_btn)

    # Verify redirect to marketplace
    wait.until(lambda d: "/farmer-market/" in d.current_url)

    # Verify listing appears in marketplace grid
    wait.until(lambda d: "fresh organic carrots" in d.find_element(By.ID, "produceGrid").text.lower())
    grid_text = driver.find_element(By.ID, "produceGrid").text.lower()
    assert "fresh organic carrots" in grid_text
    assert "75" in grid_text


@pytest.mark.django_db(transaction=True)
def test_produce_listing_validation_error(driver, live_server, farmer_user):
    """ST 43 Negative Test: Try submitting without required produce info and verify validation error."""
    perform_login(driver, live_server.url, farmer_user.phone_number, "Password123!")

    driver.get(f"{live_server.url}/create-produce/")
    wait = WebDriverWait(driver, 10)

    # Submit form empty
    submit_btn = wait.until(EC.presence_of_element_located((By.ID, "submitProduceBtn")))
    click_element(driver, submit_btn)

    # Verify validation error is shown
    wait.until(lambda d: d.find_element(By.ID, "produceNameError").text.strip() != "")
    assert driver.find_element(By.ID, "produceNameError").text.strip() != ""

    # Verify listing not created in DB
    assert ProduceListing.objects.count() == 0


# ==============================================================================
# ST 44 — Consumer View & Contact Farmer Tests
# ==============================================================================

@pytest.mark.django_db(transaction=True)
def test_consumer_contact_farmer(driver, live_server, citizen_user, farmer_user):
    """ST 44: Login as consumer, view produce details, verify farmer info & direct contact info without payment."""
    # Pre-create produce listing
    produce = ProduceListing.objects.create(
        farmer=farmer_user,
        produce_name="Fresh Red Tomatoes",
        category="Vegetables",
        price=50.00,
        unit="kg",
        quantity="80 kg",
        availability="Available",
        location="Savar, Dhaka",
        description="Fresh red tomatoes directly from field.",
    )

    # Login as consumer/citizen
    perform_login(driver, live_server.url, citizen_user.phone_number, "Password123!")

    # Open produce details page
    driver.get(f"{live_server.url}/produce-details/?id={produce.id}")
    wait = WebDriverWait(driver, 10)

    # Verify details
    wait.until(lambda d: "fresh red tomatoes" in d.find_element(By.ID, "detailTitle").text.lower())

    # Verify farmer info & contact visible
    wait.until(lambda d: farmer_user.full_name.lower() in d.find_element(By.ID, "farmerName").text.lower())
    assert farmer_user.full_name.lower() in driver.find_element(By.ID, "farmerName").text.lower()
    assert farmer_user.phone_number in driver.find_element(By.ID, "farmerPhone").text


# ==============================================================================
# ST 45 — Simple Farmer UI Tests
# ==============================================================================

@pytest.mark.django_db(transaction=True)
def test_farmer_ui_layout_and_responsive(driver, live_server, farmer_user):
    """ST 45: Inspect farmer marketplace & creation UI layout, labels, and mobile responsiveness (390, 844)."""
    perform_login(driver, live_server.url, farmer_user.phone_number, "Password123!")

    # 1. Desktop View - Check buttons and form controls
    driver.get(f"{live_server.url}/create-produce/")
    wait = WebDriverWait(driver, 10)

    submit_btn = wait.until(EC.presence_of_element_located((By.ID, "submitProduceBtn")))
    assert submit_btn.is_displayed()
    assert submit_btn.is_enabled()

    # Check clear labels exist
    labels = driver.find_elements(By.TAG_NAME, "label")
    assert len(labels) >= 5

    # 2. Viewport Resizing (Mobile - 390x844)
    driver.set_window_size(390, 844)
    time.sleep(0.5)

    # Verify important controls remain visible and clickable in mobile viewport
    assert submit_btn.is_displayed()
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_btn)

    # Check marketplace page under mobile viewport
    driver.get(f"{live_server.url}/farmer-market/")
    post_link = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#farmerActionSection a")))
    assert post_link.is_displayed()


# ==============================================================================
# ST 47 — Farmer Marketplace Disclaimer Tests
# ==============================================================================

@pytest.mark.django_db(transaction=True)
def test_farmer_disclaimer_displayed(driver, live_server, citizen_user, farmer_user):
    """ST 47: Verify mandatory disclaimer about HELPNET not handling payment or delivery."""
    produce = ProduceListing.objects.create(
        farmer=farmer_user,
        produce_name="Organic Potatoes",
        category="Vegetables",
        price=30.00,
        unit="kg",
        quantity="200 kg",
        availability="Available",
        location="Bogura",
        description="Fresh organic potatoes.",
    )

    perform_login(driver, live_server.url, citizen_user.phone_number, "Password123!")

    # 1. Verify on marketplace page
    driver.get(f"{live_server.url}/farmer-market/")
    wait = WebDriverWait(driver, 10)

    wait.until(lambda d: "helpnet does not handle payment or delivery" in d.find_element(By.TAG_NAME, "body").text.lower())
    body_text = driver.find_element(By.TAG_NAME, "body").text.lower()
    assert "helpnet does not handle payment or delivery" in body_text
    assert "between the farmer and consumer" in body_text

    # 2. Verify on produce details page
    driver.get(f"{live_server.url}/produce-details/?id={produce.id}")
    wait.until(lambda d: "helpnet does not handle payment or delivery" in d.find_element(By.TAG_NAME, "body").text.lower())
    detail_body_text = driver.find_element(By.TAG_NAME, "body").text.lower()
    assert "helpnet does not handle payment or delivery" in detail_body_text
    assert "between the farmer and consumer" in detail_body_text


# ==============================================================================
# Protected-Action Test (Unauthenticated User Access)
# ==============================================================================

@pytest.mark.django_db(transaction=True)
def test_protected_action_unauthenticated(driver, live_server):
    """Protected-action test: Unauthenticated user cannot access protected pages or perform protected actions."""
    # Ensure driver is unauthenticated / clear session
    driver.get(f"{live_server.url}/login/")
    driver.execute_script("localStorage.clear(); sessionStorage.clear();")

    # Try opening protected waste pickup page
    driver.get(f"{live_server.url}/waste-pickup/")
    time.sleep(1)

    # Expected: Redirected to login page or unauthenticated
    wait = WebDriverWait(driver, 10)
    wait.until(lambda d: "/login/" in d.current_url)
    assert "/login/" in driver.current_url

    # Try opening protected create produce page
    driver.get(f"{live_server.url}/create-produce/")
    time.sleep(1)

    # Expected: Redirected to login page
    wait.until(lambda d: "/login/" in d.current_url)
    assert "/login/" in driver.current_url


# ==============================================================================
# ST 32 / S4-T29 — Event Messages & Access Control Tests
# ==============================================================================

@pytest.mark.django_db(transaction=True)
def test_message_thread_button_availability(driver, live_server, ngo_user, non_signed_up_volunteer):
    """ST 32 / S4-T29: Message-thread UI/button is hidden for non-signed-up users and appears after signup."""
    opportunity = VolunteerOpportunity.objects.create(
        title="Tree Plantation Campaign",
        description="Planting trees across Dhanmondi lake area.",
        date="2026-11-20",
        location="Dhanmondi, Dhaka",
        required_volunteers=10,
        coordinator=ngo_user,
    )

    # Login as volunteer who is not yet signed up
    perform_login(driver, live_server.url, non_signed_up_volunteer.phone_number, "Password123!")

    # 1. View opportunity details before signup
    driver.get(f"{live_server.url}/volunteer-opportunity-details/?event_id={opportunity.id}")
    wait = WebDriverWait(driver, 10)

    wait.until(lambda d: "tree plantation campaign" in d.find_element(By.ID, "opportunityDetail").text.lower())

    # Message-thread button must NOT be shown before signup
    assert len(driver.find_elements(By.ID, "messageThreadBtn")) == 0

    # 2. Sign up for the opportunity
    signup_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Sign up')]")))
    click_element(driver, signup_btn)

    # Wait for signup confirmation
    wait.until(lambda d: "signed up" in d.find_element(By.ID, "opportunityDetail").text.lower())

    # 3. Message-thread UI/button must now appear and be visible
    thread_btn = wait.until(EC.visibility_of_element_located((By.ID, "messageThreadBtn")))
    assert thread_btn.is_displayed()
    assert f"event_id={opportunity.id}" in thread_btn.get_attribute("href")

    # 4. Clicking the message-thread button navigates to the event message thread
    click_element(driver, thread_btn)
    wait.until(lambda d: "/volunteer-message/" in d.current_url)
    assert f"event_id={opportunity.id}" in driver.current_url


@pytest.mark.django_db(transaction=True)
def test_non_signed_up_user_cannot_read_or_post(driver, live_server, ngo_user, signed_up_volunteer, non_signed_up_volunteer):
    """ST 32 / S4-T29: Verify that a non-signed-up user cannot read or post messages, while signed-up user can."""
    opportunity = VolunteerOpportunity.objects.create(
        title="Flood Relief Distribution",
        description="Distribute relief materials to flood victims.",
        date="2026-11-25",
        location="Sylhet",
        required_volunteers=5,
        coordinator=ngo_user,
    )
    VolunteerSignup.objects.create(volunteer=signed_up_volunteer, event=opportunity)

    # Coordinator posts a message to the event thread
    VolunteerMessage.objects.create(
        sender=ngo_user,
        event=opportunity,
        message="Coordination meeting at the central shelter at 8:00 AM.",
    )

    wait = WebDriverWait(driver, 10)

    # --------------------------------------------------------------------------
    # Part 1: Non-signed-up user cannot read messages
    # --------------------------------------------------------------------------
    perform_login(driver, live_server.url, non_signed_up_volunteer.phone_number, "Password123!")

    # Directly open the message thread page for this event
    driver.get(f"{live_server.url}/volunteer-message/?event_id={opportunity.id}")

    # Refusal notice must be displayed
    wait.until(lambda d: "sign up for this event" in d.find_element(By.ID, "volunteerMessage").text.lower())
    notice = driver.find_element(By.ID, "volunteerMessage").text.lower()
    assert "sign up for this event" in notice

    # Message list must NOT disclose the event messages
    message_content = driver.find_element(By.ID, "messageList").text.lower()
    assert "coordination meeting at the central shelter" not in message_content

    # --------------------------------------------------------------------------
    # Part 2: Non-signed-up user cannot post messages
    # --------------------------------------------------------------------------
    message_input = wait.until(EC.presence_of_element_located((By.ID, "eventMessage")))
    message_input.clear()
    message_input.send_keys("Unauthorized message from non-member!")

    send_btn = wait.until(EC.element_to_be_clickable((By.ID, "sendMessageBtn")))
    click_element(driver, send_btn)

    # Posting must be rejected with error notice
    wait.until(lambda d: "only event participants" in d.find_element(By.ID, "volunteerMessage").text.lower() or "sign up" in d.find_element(By.ID, "volunteerMessage").text.lower())

    # Unauthorized message must not be in the DOM or database
    assert "unauthorized message from non-member!" not in driver.find_element(By.ID, "messageList").text.lower()
    assert VolunteerMessage.objects.filter(message="Unauthorized message from non-member!").count() == 0

    # --------------------------------------------------------------------------
    # Part 3: Signed-up volunteer CAN read and post messages
    # --------------------------------------------------------------------------
    perform_login(driver, live_server.url, signed_up_volunteer.phone_number, "Password123!")

    # Open details page and access message thread via the newly available button
    driver.get(f"{live_server.url}/volunteer-opportunity-details/?event_id={opportunity.id}")
    thread_btn = wait.until(EC.visibility_of_element_located((By.ID, "messageThreadBtn")))
    click_element(driver, thread_btn)

    wait.until(lambda d: "/volunteer-message/" in d.current_url)

    # Signed-up user can read coordinator message
    wait.until(lambda d: "coordination meeting at the central shelter" in d.find_element(By.ID, "messageList").text.lower())
    assert "coordination meeting at the central shelter" in driver.find_element(By.ID, "messageList").text.lower()

    # Signed-up user can post a new message
    msg_input = wait.until(EC.presence_of_element_located((By.ID, "eventMessage")))
    msg_input.clear()
    msg_input.send_keys("I will arrive with 3 emergency kits.")

    send_button = wait.until(EC.element_to_be_clickable((By.ID, "sendMessageBtn")))
    click_element(driver, send_button)

    # Verify message posted successfully
    wait.until(lambda d: "emergency kits" in d.find_element(By.ID, "messageList").text.lower())
    assert "emergency kits" in driver.find_element(By.ID, "messageList").text.lower()
    assert VolunteerMessage.objects.filter(event=opportunity, sender=signed_up_volunteer).exists()
