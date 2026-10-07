from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time


BASE_URL = "http://127.0.0.1:8000"

EMAIL = "volunteer@gmail.com"
PASSWORD = "volunteer123456789"


def create_driver():
    options = Options()
    options.add_argument("--start-maximized")
    return webdriver.Chrome(options=options)


def login(driver):
    driver.get(BASE_URL + "/login/")

    driver.find_element(
        By.ID,
        "identifier"
    ).send_keys(EMAIL)

    driver.find_element(
        By.ID,
        "password"
    ).send_keys(PASSWORD)

    driver.find_element(
        By.ID,
        "loginButton"
    ).click()

    time.sleep(4)


def test_website_opens():
    driver = create_driver()

    try:
        driver.get(BASE_URL)

        assert driver.current_url.startswith(BASE_URL)

    finally:
        driver.quit()


def test_volunteer_opportunity():
    driver = create_driver()

    try:
        login(driver)

        print("\nLOGIN CHECK")
        print("URL:", driver.current_url)

        token = driver.execute_script(
            "return localStorage.getItem('helpnet_token');"
        )

        user = driver.execute_script(
            "return localStorage.getItem('helpnet_user');"
        )

        refresh = driver.execute_script(
            "return localStorage.getItem('refreshToken');"
        )

        print("helpnet_token:", token)
        print("helpnet_user:", user)
        print("refreshToken:", refresh)

        assert token is not None, (
            "Login failed: helpnet_token was not saved."
        )

        driver.get(
            BASE_URL + "/create-opportunity/"
        )

        time.sleep(2)

        print("\nOPPORTUNITY")
        print("URL:", driver.current_url)

        assert "/login/" not in driver.current_url

        assert (
            "/create-opportunity/"
            in driver.current_url
        )

        title = driver.find_element(
            By.ID,
            "eventTitle"
        )

        date = driver.find_element(
            By.ID,
            "eventDate"
        )

        location = driver.find_element(
            By.ID,
            "eventLocation"
        )

        required = driver.find_element(
            By.ID,
            "eventRequired"
        )

        description = driver.find_element(
            By.ID,
            "eventDescription"
        )

        print("\nFORM FIELDS:")
        print("eventTitle: FOUND")
        print("eventDate: FOUND")
        print("eventLocation: FOUND")
        print("eventRequired: FOUND")
        print("eventDescription: FOUND")

        title.send_keys(
            "Selenium Test Volunteer Opportunity"
        )

        date.send_keys(
            "10/10/2026"
        )

        location.send_keys(
            "Dhaka"
        )

        required.send_keys(
            "5"
        )

        description.send_keys(
            "This is a Selenium test volunteer opportunity."
        )

        print("\nFORM FILLED SUCCESSFULLY")

        submit_button = driver.find_element(
            By.CSS_SELECTOR,
            "button[type='submit']"
        )

        print("SUBMIT BUTTON: FOUND")

        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});",
            submit_button
        )

        time.sleep(1)

        driver.execute_script(
            "arguments[0].click();",
            submit_button
        )

        time.sleep(3)

        print("\nFINAL RESULT")
        print("FINAL URL:", driver.current_url)

        print("\nFINAL PAGE:")

        print(
            driver.find_element(
                By.TAG_NAME,
                "body"
            ).get_attribute("innerText")
        )

    finally:
        driver.quit()


def test_volunteer_signup():
    driver = create_driver()

    try:
        login(driver)

        print("\nVOLUNTEER SIGNUP")
        print(
            "LOGIN URL:",
            driver.current_url
        )

        driver.get(
            BASE_URL + "/volunteer-opportunities/"
        )

        time.sleep(2)

        print(
            "OPPORTUNITY URL:",
            driver.current_url
        )

        assert (
            "/volunteer-opportunities/"
            in driver.current_url
        )

        signup_buttons = driver.find_elements(
            By.XPATH,
            "//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'sign up')]"
        )

        print(
            "\nSIGN UP BUTTONS FOUND:",
            len(signup_buttons)
        )

        assert len(signup_buttons) > 0, (
            "No Sign up button found."
        )

        first_signup = signup_buttons[0]

        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});",
            first_signup
        )

        time.sleep(1)

        driver.execute_script(
            "arguments[0].click();",
            first_signup
        )

        time.sleep(3)

        print("\nSIGNUP RESULT")

        print(
            "FINAL URL:",
            driver.current_url
        )

        print("\nFINAL PAGE:")

        page_text = driver.find_element(
            By.TAG_NAME,
            "body"
        ).get_attribute("innerText")

        print(page_text)

        assert (
            "already signed up"
            in page_text.lower()
            or
            "signed up"
            in page_text.lower()
        )

    finally:
        driver.quit()


def test_volunteer_profile():
    driver = create_driver()

    try:
        login(driver)

        print("\nVOLUNTEER PROFILE")

        print(
            "LOGIN URL:",
            driver.current_url
        )

        driver.get(
            BASE_URL + "/volunteer-profile/"
        )

        time.sleep(2)

        print(
            "PROFILE URL:",
            driver.current_url
        )

        assert (
            "/volunteer-profile/"
            in driver.current_url
        )

        page_text = driver.find_element(
            By.TAG_NAME,
            "body"
        ).get_attribute("innerText")

        print("\nPROFILE PAGE:")

        print(page_text)

        assert len(
            page_text.strip()
        ) > 0

        print(
            "\nVOLUNTEER PROFILE PAGE: FOUND"
        )

    finally:
        driver.quit()


def test_volunteer_attendance():
    driver = create_driver()

    try:
        login(driver)

        print("\nVOLUNTEER ATTENDANCE")

        print(
            "LOGIN URL:",
            driver.current_url
        )

        driver.get(
            BASE_URL + "/volunteer-attendance/"
        )

        time.sleep(2)

        print(
            "ATTENDANCE URL:",
            driver.current_url
        )

        assert (
            "/volunteer-attendance/"
            in driver.current_url
        )

        page_text = driver.find_element(
            By.TAG_NAME,
            "body"
        ).get_attribute("innerText")

        print("\nATTENDANCE PAGE:")

        print(page_text)

        assert len(
            page_text.strip()
        ) > 0

        buttons = driver.find_elements(
            By.TAG_NAME,
            "button"
        )

        print(
            "\nBUTTONS FOUND:",
            len(buttons)
        )

        for button in buttons:
            print(
                "BUTTON:",
                button.text
            )

        print(
            "\nVOLUNTEER ATTENDANCE PAGE: FOUND"
        )

    finally:
        driver.quit()


def test_volunteer_message():
    driver = create_driver()

    try:
        login(driver)

        print("\nVOLUNTEER MESSAGE")

        print(
            "LOGIN URL:",
            driver.current_url
        )

        driver.get(
            BASE_URL + "/volunteer-message/"
        )

        time.sleep(2)

        print(
            "MESSAGE URL:",
            driver.current_url
        )

        assert (
            "/volunteer-message/"
            in driver.current_url
        )

        page_text = driver.find_element(
            By.TAG_NAME,
            "body"
        ).text

        print("\nMESSAGE PAGE:")

        print(page_text)

        assert len(
            page_text.strip()
        ) > 0

        print(
            "\nVOLUNTEER MESSAGE PAGE: FOUND"
        )

    finally:
        driver.quit()


def test_volunteer_certificate():
    driver = create_driver()

    try:
        login(driver)

        print("\nVOLUNTEER CERTIFICATE")

        print(
            "LOGIN URL:",
            driver.current_url
        )

        driver.get(
            BASE_URL + "/volunteer-certificate/"
        )

        time.sleep(2)

        print(
            "CERTIFICATE URL:",
            driver.current_url
        )

        assert (
            "/volunteer-certificate/"
            in driver.current_url
        )

        page_text = driver.find_element(
            By.TAG_NAME,
            "body"
        ).text

        print("\nCERTIFICATE PAGE:")

        print(page_text)

        assert len(
            page_text.strip()
        ) > 0

        print(
            "\nVOLUNTEER CERTIFICATE PAGE: FOUND"
        )

    finally:
        driver.quit()


def test_volunteer_search():
    driver = create_driver()

    try:
        login(driver)

        print("\nVOLUNTEER SEARCH")

        print(
            "LOGIN URL:",
            driver.current_url
        )

        driver.get(
            BASE_URL + "/volunteer-search/"
        )

        time.sleep(2)

        print(
            "SEARCH URL:",
            driver.current_url
        )

        assert (
            "/volunteer-search/"
            in driver.current_url
        )

        page_text = driver.find_element(
            By.TAG_NAME,
            "body"
        ).text

        print("\nVOLUNTEER SEARCH PAGE:")

        print(page_text)

        assert len(
            page_text.strip()
        ) > 0

        buttons = driver.find_elements(
            By.TAG_NAME,
            "button"
        )

        inputs = driver.find_elements(
            By.TAG_NAME,
            "input"
        )

        print(
            "\nINPUTS FOUND:",
            len(inputs)
        )

        for item in inputs:
            print(
                "INPUT:",
                item.get_attribute("name"),
                "|",
                item.get_attribute("id"),
                "|",
                item.get_attribute("placeholder")
            )

        print(
            "\nBUTTONS FOUND:",
            len(buttons)
        )

        for button in buttons:
            print(
                "BUTTON:",
                button.text
            )

        print(
            "\nVOLUNTEER SEARCH PAGE: FOUND"
        )

    finally:
        driver.quit()


def test_admin_volunteers():
    driver = create_driver()

    try:
        login(driver)

        print("\nADMIN VOLUNTEERS")

        print(
            "LOGIN URL:",
            driver.current_url
        )

        driver.get(
            BASE_URL + "/admin-volunteers/"
        )

        time.sleep(2)

        print(
            "ADMIN VOLUNTEERS URL:",
            driver.current_url
        )

        page_text = driver.find_element(
            By.TAG_NAME,
            "body"
        ).text

        print("\nADMIN VOLUNTEERS PAGE:")

        print(page_text)

        assert len(
            page_text.strip()
        ) > 0

        print(
            "\nBUTTONS FOUND:",
            len(
                driver.find_elements(
                    By.TAG_NAME,
                    "button"
                )
            )
        )

        print(
            "\nADMIN VOLUNTEERS PAGE: FOUND"
        )

    finally:
        driver.quit()

def test_goods_list():
    driver = create_driver()

    try:
        login(driver)

        print("\nGOODS LIST")

        driver.get(
            BASE_URL + "/goods-list/"
        )

        time.sleep(2)

        print(
            "GOODS LIST URL:",
            driver.current_url
        )

        assert (
            "/goods-list/"
            in driver.current_url
        )

        page_text = driver.find_element(
            By.TAG_NAME,
            "body"
        ).text

        print("\nGOODS LIST PAGE:")
        print(page_text)

        inputs = driver.find_elements(
            By.TAG_NAME,
            "input"
        )

        buttons = driver.find_elements(
            By.TAG_NAME,
            "button"
        )

        print(
            "\nINPUTS FOUND:",
            len(inputs)
        )

        for item in inputs:
            print(
                "INPUT:",
                item.get_attribute("name"),
                "|",
                item.get_attribute("id"),
                "|",
                item.get_attribute("placeholder")
            )

        print(
            "\nBUTTONS FOUND:",
            len(buttons)
        )

        for button in buttons:
            print(
                "BUTTON:",
                button.text
            )

        print(
            "\nGOODS LIST PAGE: FOUND"
        )

    finally:
        driver.quit()


def test_create_goods():
    driver = create_driver()

    try:
        login(driver)

        print("\nCREATE GOODS")

        driver.get(
            BASE_URL + "/create-goods/"
        )

        time.sleep(2)

        print(
            "CREATE GOODS URL:",
            driver.current_url
        )

        assert (
            "/create-goods/"
            in driver.current_url
        )

        page_text = driver.find_element(
            By.TAG_NAME,
            "body"
        ).text

        print("\nCREATE GOODS PAGE:")
        print(page_text)

        inputs = driver.find_elements(
            By.TAG_NAME,
            "input"
        )

        textareas = driver.find_elements(
            By.TAG_NAME,
            "textarea"
        )

        selects = driver.find_elements(
            By.TAG_NAME,
            "select"
        )

        buttons = driver.find_elements(
            By.TAG_NAME,
            "button"
        )

        print(
            "\nINPUTS FOUND:",
            len(inputs)
        )

        for item in inputs:
            print(
                "INPUT:",
                item.get_attribute("name"),
                "|",
                item.get_attribute("id"),
                "|",
                item.get_attribute("placeholder")
            )

        print(
            "\nTEXTAREAS FOUND:",
            len(textareas)
        )

        for item in textareas:
            print(
                "TEXTAREA:",
                item.get_attribute("name"),
                "|",
                item.get_attribute("id")
            )

        print(
            "\nSELECTS FOUND:",
            len(selects)
        )

        for item in selects:
            print(
                "SELECT:",
                item.get_attribute("name"),
                "|",
                item.get_attribute("id")
            )

        print(
            "\nBUTTONS FOUND:",
            len(buttons)
        )

        for button in buttons:
            print(
                "BUTTON:",
                button.text
            )

        print(
            "\nCREATE GOODS PAGE: FOUND"
        )

    finally:
        driver.quit()


def test_goods_details():
    driver = create_driver()

    try:
        login(driver)

        print("\nGOODS DETAILS")

        driver.get(
            BASE_URL + "/goods-details/"
        )

        time.sleep(2)

        print(
            "GOODS DETAILS URL:",
            driver.current_url
        )

        page_text = driver.find_element(
            By.TAG_NAME,
            "body"
        ).text

        print("\nGOODS DETAILS PAGE:")
        print(page_text)

        print(
            "\nGOODS DETAILS PAGE: FOUND"
        )

    finally:
        driver.quit()


def test_goods_interest_contact():
    driver = create_driver()

    try:
        login(driver)

        print("\nGOODS INTEREST / CONTACT")

        driver.get(
            BASE_URL + "/goods-list/"
        )

        time.sleep(2)

        print(
            "GOODS LIST URL:",
            driver.current_url
        )

        page_text = driver.find_element(
            By.TAG_NAME,
            "body"
        ).text

        print("\nGOODS PAGE:")
        print(page_text)

        buttons = driver.find_elements(
            By.TAG_NAME,
            "button"
        )

        print(
            "\nBUTTONS FOUND:",
            len(buttons)
        )

        for button in buttons:
            print(
                "BUTTON:",
                button.text
            )

        print(
            "\nGOODS INTEREST / CONTACT PAGE: FOUND"
        )

    finally:
        driver.quit()


def test_goods_report_and_disclaimer():
    driver = create_driver()

    try:
        login(driver)

        print("\nGOODS REPORT / DISCLAIMER")

        driver.get(
            BASE_URL + "/goods-list/"
        )

        time.sleep(2)

        page_text = driver.find_element(
            By.TAG_NAME,
            "body"
        ).text

        print("\nGOODS PAGE:")
        print(page_text)

        print(
            "\nREPORT / DISCLAIMER ELEMENTS"
        )

        buttons = driver.find_elements(
            By.TAG_NAME,
            "button"
        )

        links = driver.find_elements(
            By.TAG_NAME,
            "a"
        )

        print(
            "BUTTONS FOUND:",
            len(buttons)
        )

        for button in buttons:
            print(
                "BUTTON:",
                button.text
            )

        print(
            "LINKS FOUND:",
            len(links)
        )

        for link in links:
            print(
                "LINK:",
                link.text,
                "|",
                link.get_attribute("href")
            )

        print(
            "\nGOODS REPORT / DISCLAIMER PAGE: FOUND"
        )

    finally:
        driver.quit()



def test_health_questions():
    driver = create_driver()

    try:
        login(driver)

        print("\n================ HEALTH QUESTIONS ================")

        print("LOGIN URL:", driver.current_url)

        driver.get(
            BASE_URL + "/health-questions/"
        )

        time.sleep(2)

        print(
            "HEALTH QUESTIONS URL:",
            driver.current_url
        )

        assert (
            "/health-questions/"
            in driver.current_url
        )

        page_text = driver.find_element(
            By.TAG_NAME,
            "body"
        ).text

        print("\nHEALTH QUESTIONS PAGE:")
        print(page_text)

        inputs = driver.find_elements(
            By.TAG_NAME,
            "input"
        )

        textareas = driver.find_elements(
            By.TAG_NAME,
            "textarea"
        )

        buttons = driver.find_elements(
            By.TAG_NAME,
            "button"
        )

        print(
            "\nINPUTS FOUND:",
            len(inputs)
        )

        for item in inputs:
            print(
                "INPUT:",
                item.get_attribute("name"),
                "|",
                item.get_attribute("id"),
                "|",
                item.get_attribute("placeholder")
            )

        print(
            "\nTEXTAREAS FOUND:",
            len(textareas)
        )

        for item in textareas:
            print(
                "TEXTAREA:",
                item.get_attribute("name"),
                "|",
                item.get_attribute("id")
            )

        print(
            "\nBUTTONS FOUND:",
            len(buttons)
        )

        for button in buttons:
            print(
                "BUTTON:",
                button.text
            )

        assert len(page_text.strip()) > 0

        print(
            "\nHEALTH QUESTIONS PAGE: FOUND"
        )

    finally:
        driver.quit()




def test_health_question_details():
    driver = create_driver()

    try:
        login(driver)

        print(
            "\n================ HEALTH QUESTION DETAILS ================"
        )

        print(
            "LOGIN URL:",
            driver.current_url
        )

        driver.get(
            BASE_URL + "/health-question-details/"
        )

        time.sleep(2)

        print(
            "HEALTH QUESTION DETAILS URL:",
            driver.current_url
        )

        assert (
            "/health-question-details/"
            in driver.current_url
        )

        page_text = driver.find_element(
            By.TAG_NAME,
            "body"
        ).text

        print("\nHEALTH QUESTION DETAILS PAGE:")
        print(page_text)

        inputs = driver.find_elements(
            By.TAG_NAME,
            "input"
        )

        textareas = driver.find_elements(
            By.TAG_NAME,
            "textarea"
        )

        buttons = driver.find_elements(
            By.TAG_NAME,
            "button"
        )

        print(
            "\nINPUTS FOUND:",
            len(inputs)
        )

        for item in inputs:
            print(
                "INPUT:",
                item.get_attribute("name"),
                "|",
                item.get_attribute("id"),
                "|",
                item.get_attribute("placeholder")
            )

        print(
            "\nTEXTAREAS FOUND:",
            len(textareas)
        )

        for item in textareas:
            print(
                "TEXTAREA:",
                item.get_attribute("name"),
                "|",
                item.get_attribute("id")
            )

        print(
            "\nBUTTONS FOUND:",
            len(buttons)
        )

        for button in buttons:
            print(
                "BUTTON:",
                button.text
            )

        assert len(page_text.strip()) > 0

        print(
            "\nHEALTH QUESTION DETAILS PAGE: FOUND"
        )

    finally:
        driver.quit()

def test_health_verification_reputation():
    driver = create_driver()

    try:
        login(driver)

        print("\n================ HEALTH VERIFICATION / REPUTATION ================")

        print("LOGIN URL:", driver.current_url)

        driver.get(
            BASE_URL + "/health-professionals/"
        )

        time.sleep(2)

        print(
            "HEALTH PROFESSIONALS URL:",
            driver.current_url
        )

        assert "/health-professionals/" in driver.current_url

        page_text = driver.find_element(
            By.TAG_NAME,
            "body"
        ).text

        print("\nHEALTH PROFESSIONALS PAGE:")
        print(page_text)

        inputs = driver.find_elements(
            By.TAG_NAME,
            "input"
        )

        buttons = driver.find_elements(
            By.TAG_NAME,
            "button"
        )

        links = driver.find_elements(
            By.TAG_NAME,
            "a"
        )

        print("\nINPUTS FOUND:", len(inputs))

        for item in inputs:
            print(
                "INPUT:",
                item.get_attribute("name"),
                "|",
                item.get_attribute("id"),
                "|",
                item.get_attribute("placeholder")
            )

        print("\nBUTTONS FOUND:", len(buttons))

        for button in buttons:
            print(
                "BUTTON:",
                button.text
            )

        print("\nLINKS FOUND:", len(links))

        for link in links:
            print(
                "LINK:",
                link.text,
                "|",
                link.get_attribute("href")
            )

        assert len(page_text.strip()) > 0

        print("\nHEALTH VERIFICATION / REPUTATION PAGE: FOUND")

    finally:
        driver.quit()


def test_health_professionals_directory():
    driver = create_driver()

    try:
        login(driver)

        print("\n================ HEALTH PROFESSIONAL DIRECTORY ================")

        print("LOGIN URL:", driver.current_url)

        driver.get(
            BASE_URL + "/health-professionals/"
        )

        time.sleep(2)

        print(
            "HEALTH PROFESSIONALS URL:",
            driver.current_url
        )

        assert "/health-professionals/" in driver.current_url

        page_text = driver.find_element(
            By.TAG_NAME,
            "body"
        ).text

        print("\nHEALTH PROFESSIONAL DIRECTORY PAGE:")
        print(page_text)

        inputs = driver.find_elements(
            By.TAG_NAME,
            "input"
        )

        buttons = driver.find_elements(
            By.TAG_NAME,
            "button"
        )

        links = driver.find_elements(
            By.TAG_NAME,
            "a"
        )

        print("\nINPUTS FOUND:", len(inputs))

        for item in inputs:
            print(
                "INPUT:",
                item.get_attribute("name"),
                "|",
                item.get_attribute("id"),
                "|",
                item.get_attribute("placeholder")
            )

        print("\nBUTTONS FOUND:", len(buttons))

        for button in buttons:
            print(
                "BUTTON:",
                button.text
            )

        print("\nLINKS FOUND:", len(links))

        for link in links:
            print(
                "LINK:",
                link.text,
                "|",
                link.get_attribute("href")
            )

        assert len(page_text.strip()) > 0

        print(
            "\nHEALTH PROFESSIONAL DIRECTORY: FOUND"
        )

    finally:
        driver.quit()