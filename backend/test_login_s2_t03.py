import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configure test credentials (defaults can be overridden via environment variables)
LOGIN_IDENTIFIER = os.environ.get("TEST_LOGIN_IDENTIFIER", "01712345671")
LOGIN_PASSWORD = os.environ.get("TEST_LOGIN_PASSWORD", "c123456789")

options = webdriver.ChromeOptions()
# Set headless for CI / background runs if desired
if os.environ.get("HEADLESS", "false").lower() in ("1", "true", "yes"):
    options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
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
        EC.presence_of_element_located((By.ID, "loginButton"))
    )

    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", login_button)
    time.sleep(0.5)

    try:
        login_button.click()
    except Exception:
        driver.execute_script("arguments[0].click();", login_button)

    print("Login button clicked")

    # Wait for navigation to dashboard
    try:
        wait.until(
            lambda d: "/dashboard/" in d.current_url
        )
    except Exception:
        pass

    time.sleep(1)

    print("Current URL:")
    print(driver.current_url)
    print("")

    access_token = driver.execute_script("return localStorage.getItem('helpnet_token');")
    refresh_token = driver.execute_script("return localStorage.getItem('refreshToken');")

    print("Access token exists:")
    print(bool(access_token))

    print("Refresh token exists:")
    print(bool(refresh_token))
    print("")

    if "/dashboard/" in driver.current_url and access_token and refresh_token:
        print("S2-T03 LOGIN TEST PASSED")
    else:
        print("S2-T03 LOGIN TEST FAILED")

finally:
    driver.quit()
