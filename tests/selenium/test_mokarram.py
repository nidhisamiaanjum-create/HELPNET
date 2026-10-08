import os
import time

import pytest
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


BASE_URL = os.getenv("HELPNET_BASE_URL", "http://127.0.0.1:8000")
WAIT = 10


# ============================================================
# TEST USERS
# ============================================================

ADMIN_EMAIL = "admin@gmail.com"
ADMIN_PASSWORD = "admin123456789"

DONOR_EMAIL = "doner@gmail.com"
DONOR_PASSWORD = "doner123456789"

NGO_EMAIL = "ngo@gmail.com"
NGO_PASSWORD = "ngo123456789"

FARMER_EMAIL = "farmer@gmaail.com"
FARMER_PASSWORD = "farmer123456789"

VOLUNTEER_EMAIL = "volunteer@gmail.com"
VOLUNTEER_PASSWORD = "volunteer123456789"


# ============================================================
# DRIVER
# ============================================================

@pytest.fixture
def driver():
    options = webdriver.ChromeOptions()

    # Remove this if you want to see the browser.
    # options.add_argument("--headless=new")

    options.add_argument("--window-size=1440,900")

    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(2)

    yield driver

    driver.quit()


# ============================================================
# HELPERS
# ============================================================

def wait_for(driver, by, value, timeout=WAIT):
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, value))
    )


def click(driver, by, value, timeout=WAIT):
    element = WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((by, value))
    )

    driver.execute_script(
        "arguments[0].scrollIntoView({block:'center'});",
        element
    )

    element.click()

    return element


def type_text(driver, by, value, text, clear=True):
    element = wait_for(driver, by, value)

    if clear:
        element.clear()

    element.send_keys(text)

    return element


def text_exists(driver, text):
    return text.lower() in driver.page_source.lower()


def optional_click(driver, selectors):
    # Try several selectors because the existing frontend may
    # use different IDs/classes.
    for by, value in selectors:
        try:
            click(driver, by, value, timeout=3)
            return True
        except Exception:
            continue

    return False


def optional_find(driver, selectors):
    for by, value in selectors:
        try:
            return driver.find_element(by, value)
        except NoSuchElementException:
            continue

    return None


# ============================================================
# LOGIN
# ============================================================

def login(driver, identifier, password):
    driver.get(f"{BASE_URL}/")

    email_field = wait_for(driver, By.ID, "identifier")
    email_field.clear()
    email_field.send_keys(identifier)

    password_field = wait_for(driver, By.ID, "password")
    password_field.clear()
    password_field.send_keys(password)

    login_button = wait_for(driver, By.ID, "loginButton")
    login_button.click()

    time.sleep(2)

    print("LOGIN IDENTIFIER:", identifier)
    print("AFTER LOGIN URL:", driver.current_url)

    try:
        alert = driver.find_element(By.ID, "formAlert")
        print("LOGIN ALERT:", alert.text)
    except NoSuchElementException:
        print("LOGIN ALERT: not found")


# ============================================================
# ST26
# REPORT / FLAG BLOOD REQUEST
# ============================================================

def test_st26_report_blood_request(driver):

    # Login as donor/citizen
    login(driver, DONOR_EMAIL, DONOR_PASSWORD)

    # Open blood page
    driver.get(f"{BASE_URL}/blood/")

    # Wait for blood requests to load
    wait_for(driver, By.ID, "requestList")

    # Find a request from another user
    report_form = wait_for(
        driver,
        By.CSS_SELECTOR,
        "#requestList .blood-report-form"
    )

    # Enter report reason
    textarea = report_form.find_element(
        By.CSS_SELECTOR,
        "textarea"
    )
    textarea.send_keys(
        "This blood request appears to be suspicious."
    )

    # Find submit button
    submit_button = report_form.find_element(
        By.CSS_SELECTOR,
        "button[type='submit']"
    )

    # Scroll button into view
    driver.execute_script(
        "arguments[0].scrollIntoView({block: 'center'});",
        submit_button
    )

    time.sleep(0.5)

    # Click using JavaScript
    driver.execute_script(
        "arguments[0].click();",
        submit_button
    )

    # Verify successful report
    success_message = WebDriverWait(driver, WAIT).until(
        EC.visibility_of_element_located(
            (
                By.CSS_SELECTOR,
                ".blood-report-form .form-message.success"
            )
        )
    )

    assert success_message.is_displayed()


# ============================================================
# ST46
# ADMIN MODERATION
# ============================================================

def test_st46_admin_can_review_flagged_content(driver):

    # Login as admin
    login(driver, ADMIN_EMAIL, ADMIN_PASSWORD)

    # Open the actual moderation page
    driver.get(f"{BASE_URL}/admin-moderation/")

    # Wait for reports section
    reports = wait_for(
        driver,
        By.ID,
        "moderationReports"
    )

    # Wait until at least one report is displayed
    report_card = WebDriverWait(driver, WAIT).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "#moderationReports .admin-item")
        )
    )

    assert report_card.is_displayed()

    # Find reason input
    reason_input = report_card.find_element(
        By.CSS_SELECTOR,
        "input[type='text']"
    )

    reason_input.send_keys(
        "Reviewed by admin."
    )

    # Find Review button
    review_button = report_card.find_element(
        By.CSS_SELECTOR,
        ".small-btn"
    )

    # Scroll into view
    driver.execute_script(
        "arguments[0].scrollIntoView({block: 'center'});",
        review_button
    )

    time.sleep(0.5)

    # Click using JavaScript
    driver.execute_script(
        "arguments[0].click();",
        review_button
    )

    # Verify moderation success message
    success_message = WebDriverWait(driver, WAIT).until(
        EC.visibility_of_element_located(
            (
                By.CSS_SELECTOR,
                "#moderationMessage.form-message.success"
            )
        )
    )

    assert success_message.is_displayed()

# ============================================================
# ST48
# FARMER PRICE RANGE
# ============================================================

def test_st48_farmer_price_range(driver):

    # Login
    login(driver, FARMER_EMAIL, FARMER_PASSWORD)

    # Open farmer marketplace
    driver.get(f"{BASE_URL}/farmer-market/")

    time.sleep(3)

    print("CURRENT URL:", driver.current_url)
    print("PAGE TITLE:", driver.title)
    print("PAGE SOURCE:")
    print(driver.page_source[:5000])

    produce_grid = wait_for(
        driver,
       By.ID,
       "produceGrid"
    )

    # Find a produce listing
    produce_link = WebDriverWait(driver, WAIT).until(
        EC.presence_of_element_located(
            (
                By.CSS_SELECTOR,
                "#produceGrid a[href*='/produce-details/?id=']"
            )
        )
    )

    # Open produce details
    driver.execute_script(
        "arguments[0].scrollIntoView({block: 'center'});",
        produce_link
    )

    driver.execute_script(
        "arguments[0].click();",
        produce_link
    )

    # Wait for price range element
    price_range = WebDriverWait(driver, WAIT).until(
        EC.presence_of_element_located(
            (By.ID, "farmerPriceRange")
        )
    )

    # Wait until price range has actual content
    WebDriverWait(driver, WAIT).until(
        lambda d: price_range.text.strip() != ""
    )

    # Verify price range is displayed
    assert price_range.is_displayed()
    assert price_range.text.strip() != ""

# ============================================================
# ST53
# HEALTH DISCLAIMER
# ============================================================

# def test_st53_health_disclaimer(driver):
#     driver.get(f"{BASE_URL}/health-professionals/")

#     disclaimer = WebDriverWait(driver, WAIT).until(
#         EC.presence_of_element_located(
#             (By.CSS_SELECTOR, "[data-i18n='healthDisclaimer']")
#         )
#     )

#     assert disclaimer.is_displayed()
#     assert "not medical advice" in disclaimer.text.lower()

# # ============================================================
# # ST54
# # ADMIN CONTENT MODERATION
# # ============================================================

# @pytest.mark.parametrize(
#     "section",
#     [
#         "farmer",
#         "goods",
#         "volunteer",
#     ],
# )
# def test_st54_admin_content_moderation(driver, section):
#     # Login as admin.
#     login(
#         driver,
#         ADMIN_EMAIL,
#         ADMIN_PASSWORD,
#     )

#     # Open admin page.
#     driver.get(f"{BASE_URL}/admin.html")

#     time.sleep(1)

#     # Try existing moderation controls.
#     control = optional_find(
#         driver,
#         [
#             (
#                 By.CSS_SELECTOR,
#                 f"[data-section='{section}']",
#             ),
#             (
#                 By.ID,
#                 f"{section}-moderation",
#             ),
#             (
#                 By.ID,
#                 f"moderate-{section}",
#             ),
#             (
#                 By.XPATH,
#                 f"//*[contains("
#                 f"translate(., '{section.upper()}', '{section}'), "
#                 f"'{section}')]",
#             ),
#         ],
#     )

#     assert control is not None, (
#         f"Admin moderation control for {section} was not found."
#     )

#     control.click()

#     time.sleep(0.5)

#     # Check that moderation actions are available.
#     assert (
#         text_exists(driver, "edit")
#         or text_exists(driver, "remove")
#         or text_exists(driver, "delete")
#         or text_exists(driver, "moderate")
#         or text_exists(driver, "এডিট")
#         or text_exists(driver, "মুছে")
#     )


# def test_st54_normal_user_cannot_moderate(driver):
#     # Login as donor.
#     login(
#         driver,
#         DONOR_EMAIL,
#         DONOR_PASSWORD,
#     )

#     # Open admin page.
#     driver.get(f"{BASE_URL}/admin.html")

#     time.sleep(1)

#     # Normal user should not see moderation controls.
#     assert not optional_find(
#         driver,
#         [
#             (By.ID, "admin-moderation"),
#             (By.ID, "moderation"),
#             (By.ID, "content-moderation"),
#         ],
#     )


# # ============================================================
# # ST55
# # NO PROMOTIONAL / ADVERTISING CONTENT
# # ============================================================

# def test_st55_blood_request_has_no_promotional_content(driver):
#     # Open blood request page.
#     driver.get(f"{BASE_URL}/blood-requests.html")

#     time.sleep(1)

#     source = driver.page_source.lower()

#     # These items must not appear on the urgent blood request screen.
#     forbidden = [
#         "advertisement",
#         "advertising",
#         "sponsored",
#         "promotion",
#         "promoted",
#         "leaderboard",
#         "top donors",
#         "donor ranking",
#     ]

#     found = [
#         word for word in forbidden
#         if word in source
#     ]

#     assert not found, (
#         "Promotional/leaderboard content found on urgent "
#         f"blood-request screen: {found}"
#     )


# # ============================================================
# # S4-T06
# # NGO CAN POST / CITIZEN CANNOT
# # ============================================================

# def test_s4_t06_ngo_can_post_opportunity(driver):
#     # Login as NGO.
#     login(
#         driver,
#         NGO_EMAIL,
#         NGO_PASSWORD,
#     )

#     # Open volunteer page.
#     driver.get(f"{BASE_URL}/volunteer.html")

#     # Find opportunity posting button.
#     post_button = optional_find(
#         driver,
#         [
#             (By.ID, "create-opportunity"),
#             (By.ID, "post-opportunity"),
#             (
#                 By.XPATH,
#                 "//button[contains("
#                 "translate(., 'OPPORTUNITY', 'opportunity'), "
#                 "'opportunity')]",
#             ),
#         ],
#     )

#     assert post_button is not None, (
#         "NGO opportunity-posting control not found."
#     )

#     post_button.click()


# def test_s4_t06_citizen_cannot_post_opportunity(driver):
#     # Login as donor.
#     login(
#         driver,
#         DONOR_EMAIL,
#         DONOR_PASSWORD,
#     )

#     # Open volunteer page.
#     driver.get(f"{BASE_URL}/volunteer.html")

#     # Citizen/donor should not see NGO posting button.
#     assert optional_find(
#         driver,
#         [
#             (By.ID, "create-opportunity"),
#             (By.ID, "post-opportunity"),
#         ],
#     ) is None


# # ============================================================
# # S4-T12
# # BROWSE + SIGNUP + DUPLICATE SIGNUP
# # ============================================================

# def test_s4_t12_browse_volunteer_opportunities(driver):
#     # Login as volunteer.
#     login(
#         driver,
#         VOLUNTEER_EMAIL,
#         VOLUNTEER_PASSWORD,
#     )

#     # Open volunteer page.
#     driver.get(f"{BASE_URL}/volunteer.html")

#     time.sleep(1)

#     # Check that volunteer opportunities are displayed.
#     assert (
#         text_exists(driver, "volunteer")
#         or text_exists(driver, "opportunity")
#         or text_exists(driver, "সেচ্ছাসেবক")
#         or text_exists(driver, "সুযোগ")
#     )


# def test_s4_t12_duplicate_signup_blocked(driver):
#     # Login as volunteer.
#     login(
#         driver,
#         VOLUNTEER_EMAIL,
#         VOLUNTEER_PASSWORD,
#     )

#     # Open volunteer page.
#     driver.get(f"{BASE_URL}/volunteer.html")

#     # Find signup button.
#     signup = optional_find(
#         driver,
#         [
#             (By.ID, "signup-opportunity"),
#             (By.CSS_SELECTOR, ".signup-opportunity"),
#             (
#                 By.XPATH,
#                 "//button[contains("
#                 "translate(., 'SIGN UP', 'sign up'), "
#                 "'sign up')]",
#             ),
#         ],
#     )

#     assert signup is not None, "Signup button not found."

#     signup.click()

#     time.sleep(0.5)

#     # Try the same signup again.
#     try:
#         signup.click()
#     except Exception:
#         pass

#     time.sleep(0.5)

#     # Duplicate signup should be rejected.
#     assert (
#         text_exists(driver, "already")
#         or text_exists(driver, "duplicate")
#         or text_exists(driver, "already signed")
#         or text_exists(driver, "ইতিমধ্যে")
#     )


# # ============================================================
# # S4-T19
# # VOLUNTEER PROFILE + CERTIFICATE
# # ============================================================

# def test_s4_t19_volunteer_profile(driver):
#     # Login as volunteer.
#     login(
#         driver,
#         VOLUNTEER_EMAIL,
#         VOLUNTEER_PASSWORD,
#     )

#     # Open volunteer profile.
#     driver.get(f"{BASE_URL}/volunteer-profile.html")

#     # Find name field.
#     name_field = optional_find(
#         driver,
#         [
#             (By.ID, "volunteer-name"),
#             (By.ID, "full-name"),
#             (By.NAME, "full_name"),
#         ],
#     )

#     if name_field:
#         name_field.clear()
#         name_field.send_keys("Selenium Volunteer")

#     # Find save button.
#     save = optional_find(
#         driver,
#         [
#             (By.ID, "save-profile"),
#             (By.ID, "save-volunteer-profile"),
#             (By.CSS_SELECTOR, "button[type='submit']"),
#         ],
#     )

#     assert save is not None, "Save profile button not found."

#     save.click()

#     time.sleep(1)

#     # Check that profile was saved.
#     assert (
#         text_exists(driver, "saved")
#         or text_exists(driver, "success")
#         or text_exists(driver, "সফল")
#         or text_exists(driver, "সংরক্ষণ")
#     )


# def test_s4_t19_certificate_upload_control(driver):
#     # Login as volunteer.
#     login(
#         driver,
#         VOLUNTEER_EMAIL,
#         VOLUNTEER_PASSWORD,
#     )

#     # Open volunteer profile.
#     driver.get(f"{BASE_URL}/volunteer-profile.html")

#     # Find certificate upload field.
#     file_input = optional_find(
#         driver,
#         [
#             (By.ID, "certificate"),
#             (By.ID, "supporting-certificate"),
#             (By.NAME, "certificate"),
#             (By.CSS_SELECTOR, "input[type='file']"),
#         ],
#     )

#     assert file_input is not None, (
#         "Certificate upload control was not found."
#     )


# # ============================================================
# # S4-T24
# # ATTENDANCE
# # ============================================================

# def test_s4_t24_double_checkin_blocked(driver):
#     # Login as volunteer.
#     login(
#         driver,
#         VOLUNTEER_EMAIL,
#         VOLUNTEER_PASSWORD,
#     )

#     # Open volunteer page.
#     driver.get(f"{BASE_URL}/volunteer.html")

#     # Find check-in button.
#     checkin = optional_find(
#         driver,
#         [
#             (By.ID, "check-in"),
#             (By.ID, "checkin"),
#             (
#                 By.XPATH,
#                 "//button[contains("
#                 "translate(., 'CHECK IN', 'check in'), "
#                 "'check in')]",
#             ),
#         ],
#     )

#     assert checkin is not None, "Check-in button not found."

#     checkin.click()

#     time.sleep(0.5)

#     # Try to check in again.
#     try:
#         checkin.click()
#     except Exception:
#         pass

#     time.sleep(0.5)

#     # Second check-in must be rejected.
#     assert (
#         text_exists(driver, "already checked")
#         or text_exists(driver, "already")
#         or text_exists(driver, "ইতিমধ্যে")
#     )


# # ============================================================
# # S4-T39
# # VOLUNTEER SEARCH FILTERS
# # ============================================================

# def test_s4_t39_single_filter(driver):
#     # Login as volunteer.
#     login(
#         driver,
#         VOLUNTEER_EMAIL,
#         VOLUNTEER_PASSWORD,
#     )

#     # Open volunteer search page.
#     driver.get(f"{BASE_URL}/volunteer-search.html")

#     # Find skill filter.
#     skill = optional_find(
#         driver,
#         [
#             (By.ID, "skill-filter"),
#             (By.ID, "skills"),
#             (By.NAME, "skills"),
#         ],
#     )

#     assert skill is not None, "Skill filter not found."

#     skill.send_keys("First Aid")

#     # Find search button.
#     search = optional_find(
#         driver,
#         [
#             (By.ID, "search-volunteers"),
#             (By.ID, "search-btn"),
#             (By.CSS_SELECTOR, "button[type='submit']"),
#         ],
#     )

#     assert search is not None, "Search button not found."

#     search.click()

#     time.sleep(1)

#     # Check that results are displayed.
#     assert (
#         text_exists(driver, "First Aid")
#         or text_exists(driver, "volunteer")
#         or text_exists(driver, "সেচ্ছাসেবক")
#     )


# def test_s4_t39_combined_filters(driver):
#     # Login as volunteer.
#     login(
#         driver,
#         VOLUNTEER_EMAIL,
#         VOLUNTEER_PASSWORD,
#     )

#     # Open volunteer search page.
#     driver.get(f"{BASE_URL}/volunteer-search.html")

#     # Find skill filter.
#     skill = optional_find(
#         driver,
#         [
#             (By.ID, "skill-filter"),
#             (By.ID, "skills"),
#         ],
#     )

#     # Find availability filter.
#     availability = optional_find(
#         driver,
#         [
#             (By.ID, "availability-filter"),
#             (By.ID, "availability"),
#         ],
#     )

#     assert skill is not None
#     assert availability is not None

#     skill.send_keys("First Aid")
#     availability.send_keys("Available")

#     # Find search button.
#     search = optional_find(
#         driver,
#         [
#             (By.ID, "search-volunteers"),
#             (By.ID, "search-btn"),
#         ],
#     )

#     assert search is not None

#     search.click()

#     time.sleep(1)

#     # Check that search results are displayed.
#     assert (
#         text_exists(driver, "volunteer")
#         or text_exists(driver, "result")
#         or text_exists(driver, "সেচ্ছাসেবক")
#     )


# # ============================================================
# # S4-T43
# # ADMIN CSV EXPORT
# # ============================================================

# def test_s4_t43_admin_csv_export(driver):
#     # Login as admin.
#     login(
#         driver,
#         ADMIN_EMAIL,
#         ADMIN_PASSWORD,
#     )

#     # Open admin volunteer page.
#     driver.get(f"{BASE_URL}/admin-volunteers.html")

#     # Find CSV export button.
#     export_button = optional_find(
#         driver,
#         [
#             (By.ID, "export-csv"),
#             (By.ID, "export-volunteers"),
#             (
#                 By.XPATH,
#                 "//button[contains("
#                 "translate(., 'CSV', 'csv'), 'csv')]",
#             ),
#         ],
#     )

#     assert export_button is not None, (
#         "CSV export button was not found."
#     )

#     export_button.click()

#     time.sleep(2)

#     # Check that export/download was triggered.
#     assert (
#         text_exists(driver, "export")
#         or text_exists(driver, "download")
#         or text_exists(driver, "csv")
#         or text_exists(driver, "সফল")
#     )


# # ============================================================
# # LANGUAGE SWITCH
# # ============================================================

# def test_bangla_to_english(driver):
#     # Open home page.
#     driver.get(f"{BASE_URL}/")

#     # Find language button.
#     language_button = optional_find(
#     driver,
#     [
#         (By.ID, "langToggle"),
#     ],
# )

#     assert language_button is not None, (
#         "Existing language toggle was not found."
#     )

#     language_button.click()

#     time.sleep(0.5)

#     # Check that English text exists.
#     assert (
#         "login" in driver.page_source.lower()
#         or "register" in driver.page_source.lower()
#         or "home" in driver.page_source.lower()
#     )


# def test_english_to_bangla(driver):
#     # Open home page.
#     driver.get(f"{BASE_URL}/")

#     # Find language button.
#     language_button = optional_find(
#         driver,
#         [
#             (By.ID, "language-toggle"),
#             (By.ID, "lang-toggle"),
#             (By.CSS_SELECTOR, "[data-language-toggle]"),
#         ],
#     )

#     assert language_button is not None

#     language_button.click()

#     time.sleep(0.5)

#     source = driver.page_source

#     # Check that Bangla Unicode characters exist.
#     bangla_found = any(
#         "\u0980" <= char <= "\u09ff"
#         for char in source
#     )

#     assert bangla_found, (
#         "Bangla text was not found after language switch."
#     )