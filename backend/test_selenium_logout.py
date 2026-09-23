import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

LOGIN_IDENTIFIER = os.environ.get("TEST_LOGIN_IDENTIFIER", "01712345671")
LOGIN_PASSWORD = os.environ.get("TEST_LOGIN_PASSWORD", "c123456789")

options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1280,800")

driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 15)

try:
    print("Opening login page...")
    driver.get("http://127.0.0.1:8000/login/")

    identifier = wait.until(EC.presence_of_element_located((By.ID, "identifier")))
    password = wait.until(EC.presence_of_element_located((By.ID, "password")))

    identifier.send_keys(LOGIN_IDENTIFIER)
    password.send_keys(LOGIN_PASSWORD)

    login_button = wait.until(EC.presence_of_element_located((By.ID, "loginButton")))
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", login_button)
    time.sleep(0.5)
    driver.execute_script("arguments[0].click();", login_button)

    wait.until(lambda d: "/dashboard/" in d.current_url)
    time.sleep(1)

    print(f"Logged in successfully. URL: {driver.current_url}")
    access_token = driver.execute_script("return localStorage.getItem('helpnet_token');")
    refresh_token = driver.execute_script("return localStorage.getItem('refreshToken');")
    print(f"Tokens in localStorage: Access={'YES' if access_token else 'NO'}, Refresh={'YES' if refresh_token else 'NO'}")

    screenshot_dash = "backend/screenshot_dashboard.png"
    driver.save_screenshot(screenshot_dash)
    print(f"Saved dashboard screenshot to {screenshot_dash}")

    # Now click logout
    logout_button = wait.until(EC.presence_of_element_located((By.ID, "logoutButton")))
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", logout_button)
    time.sleep(0.5)
    driver.execute_script("arguments[0].click();", logout_button)

    wait.until(lambda d: "/login/" in d.current_url)
    time.sleep(1)

    post_access = driver.execute_script("return localStorage.getItem('helpnet_token');")
    post_refresh = driver.execute_script("return localStorage.getItem('refreshToken');")
    print(f"Post-logout URL: {driver.current_url}")
    print(f"Post-logout Tokens: Access={'YES' if post_access else 'CLEARED'}, Refresh={'YES' if post_refresh else 'CLEARED'}")

    screenshot_login = "backend/screenshot_post_logout.png"
    driver.save_screenshot(screenshot_login)
    print(f"Saved post-logout screenshot to {screenshot_login}")

    if "/login/" in driver.current_url and not post_access and not post_refresh:
        print("UI LOGOUT FLOW PASSED")
    else:
        print("UI LOGOUT FLOW FAILED")

finally:
    driver.quit()
