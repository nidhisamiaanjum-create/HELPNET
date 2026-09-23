from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


LOGIN_IDENTIFIER = "01712345671"


options = webdriver.ChromeOptions()
options.set_capability(
    "goog:loggingPrefs",
    {"browser": "ALL"}
)

driver = webdriver.Chrome(options=options)

wait = WebDriverWait(driver, 10)


try:

    # ============================================================
    # TEST 1: WRONG PASSWORD
    # ============================================================

    print("")
    print("===================================")
    print("TEST 1: WRONG PASSWORD")
    print("===================================")

    driver.get(
        "http://127.0.0.1:8000/login/"
    )

    identifier = wait.until(
        EC.presence_of_element_located(
            (By.ID, "identifier")
        )
    )

    password = wait.until(
        EC.presence_of_element_located(
            (By.ID, "password")
        )
    )

    identifier.send_keys(
        LOGIN_IDENTIFIER
    )

    # Intentionally wrong password
    password.send_keys(
        "WrongPassword123!"
    )

    login_button = wait.until(
        EC.element_to_be_clickable(
            (By.ID, "loginButton")
        )
    )

    login_button.click()


    # Wait until formAlert contains a message
    wait.until(
        lambda d:
        d.find_element(
            By.ID,
            "formAlert"
        ).text.strip() != ""
    )


    print("Current URL:")
    print(driver.current_url)


    alert = driver.find_element(
        By.ID,
        "formAlert"
    )


    print("Error message:")
    print(repr(alert.text))


    if (
        "/login/" in driver.current_url
        and
        alert.text.strip()
        and
        "Invalid email/phone number or password."
        in alert.text
    ):

        print(
            "WRONG PASSWORD TEST PASSED"
        )

    else:

        print(
            "WRONG PASSWORD TEST FAILED"
        )


    # ============================================================
    # TEST 2: EMPTY FIELDS
    # ============================================================

    print("")
    print("===================================")
    print("TEST 2: EMPTY FIELDS")
    print("===================================")

    driver.get(
        "http://127.0.0.1:8000/login/"
    )


    identifier = wait.until(
        EC.presence_of_element_located(
            (By.ID, "identifier")
        )
    )

    password = wait.until(
        EC.presence_of_element_located(
            (By.ID, "password")
        )
    )


    # Leave both fields empty

    login_button = wait.until(
        EC.element_to_be_clickable(
            (By.ID, "loginButton")
        )
    )

    login_button.click()


    # Wait for validation message
    wait.until(
        lambda d:
        d.find_element(
            By.ID,
            "identifierError"
        ).text.strip()
        or
        d.find_element(
            By.ID,
            "passwordError"
        ).text.strip()
    )


    print("Current URL:")
    print(driver.current_url)


    identifier_error = driver.find_element(
        By.ID,
        "identifierError"
    )

    password_error = driver.find_element(
        By.ID,
        "passwordError"
    )


    print("Identifier error:")
    print(repr(identifier_error.text))


    print("Password error:")
    print(repr(password_error.text))


    if (
        "/login/" in driver.current_url
        and
        (
            identifier_error.text.strip()
            or
            password_error.text.strip()
        )
    ):

        print(
            "EMPTY FIELDS TEST PASSED"
        )

    else:

        print(
            "EMPTY FIELDS TEST FAILED"
        )


    # ============================================================
    # FINAL RESULT
    # ============================================================

    print("")
    print("===================================")
    print("S2-T02 LOGIN ERROR TESTS COMPLETE")
    print("===================================")


finally:

    driver.quit()