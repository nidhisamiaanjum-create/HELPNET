from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

LOGIN_IDENTIFIER = "01712345671"
LOGIN_PASSWORD = "c123456789"

options = webdriver.ChromeOptions()
options.set_capability("goog:loggingPrefs", {"browser": "ALL"})

driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 15)

try:
    driver.get("http://127.0.0.1:8000/login/")
    print("Login page opened")

    identifier = wait.until(
        EC.presence_of_element_located((By.ID, "identifier"))
    )

    password = wait.until(
        EC.presence_of_element_located((By.ID, "password"))
    )

    identifier.send_keys(LOGIN_IDENTIFIER)
    password.send_keys(LOGIN_PASSWORD)

    print("Login information entered")

    login_button = wait.until(
        EC.element_to_be_clickable((By.ID, "loginButton"))
    )

    login_button.click()

    print("Login button clicked")

    # Wait longer for API response / redirect
    try:
        wait.until(
            lambda d: "/dashboard/" in d.current_url
        )
    except Exception:
        pass

    time.sleep(1)

    print("")
    print("Current URL:")
    print(driver.current_url)

    alert = driver.find_element(By.ID, "formAlert")

    print("")
    print("Alert text:")
    print(repr(alert.text))

    print("")
    print("===================================")
    print("BROWSER CONSOLE")
    print("===================================")

    logs = driver.get_log("browser")

    if not logs:
        print("No browser console errors found.")
    else:
        for log in logs:
            print(log["level"], ":", log["message"])

    print("")
    print("===================================")

    if "/dashboard/" in driver.current_url:
        print("LOGIN TEST PASSED")
    else:
        print("LOGIN TEST FAILED")

    print("===================================")

    # Keep browser open briefly so response can finish
    time.sleep(2)

finally:
    driver.quit()