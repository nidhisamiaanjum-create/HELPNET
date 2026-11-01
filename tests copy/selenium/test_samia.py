import time
import tempfile
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import os


BASE_URL = "http://127.0.0.1:8000"


def test_registration():
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 10)

    try:
        # Open registration page
        driver.get(f"{BASE_URL}/register/")

        # Wait for registration form
        form = wait.until(
            EC.visibility_of_element_located((By.ID, "registerForm"))
        )

        assert form.is_displayed(), "Registration form is not visible"

        # Generate unique account data
        unique_id = str(int(time.time()))

        phone = "018" + unique_id[-8:]
        email = f"selenium{unique_id}@example.com"

        # Fill Full Name
        driver.find_element(By.ID, "fullName").send_keys(
            "Selenium Test User"
        )

        # Fill Phone
        driver.find_element(By.ID, "phoneNumber").send_keys(
            phone
        )

        # Fill Password
        driver.find_element(By.ID, "password").send_keys(
            "Test@12345"
        )

        # Fill Email
        driver.find_element(By.ID, "email").send_keys(
            email
        )

        # Select Citizen role
        role = Select(
            driver.find_element(By.ID, "role")
        )
        role.select_by_value("Citizen")

        # Find registration button
        register_button = wait.until(
            EC.presence_of_element_located(
                (By.ID, "registerButton")
            )
        )

        # Scroll button into view
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});",
            register_button
        )

        # Make sure the button is visible
        register_button = wait.until(
            EC.visibility_of_element_located(
                   (By.ID, "registerButton")
               )
        )

        driver.execute_script(
               "arguments[0].scrollIntoView({block: 'center', inline: 'center'});",
               register_button
        )

        # Submit the real frontend form
        driver.execute_script(
          "arguments[0].click();",
           register_button
        )

        # Wait for registration result
        wait.until(
            lambda d: (
                "/login/" in d.current_url
                or "/dashboard/" in d.current_url
                or (
                    d.find_element(By.ID, "formAlert").is_displayed()
                    and d.find_element(By.ID, "formAlert").text.strip()
                )
            )
        )

        # Successful redirect
        if (
            "/login/" in driver.current_url
            or "/dashboard/" in driver.current_url
        ):
            return

        # Otherwise check visible alert
        alert = driver.find_element(
            By.ID, "formAlert"
        ).text.strip()

        success_words = [
            "success",
            "successful",
            "registered",
            "created",
            "সফল",
            "নিবন্ধিত",
        ]

        assert any(
            word.lower() in alert.lower()
            for word in success_words
        ), f"Registration did not succeed. Alert: {alert}"

    finally:
        driver.quit()

def test_login():
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 10)

    try:
        driver.get(f"{BASE_URL}/login/")

        # Confirm login form is visible
        login_form = wait.until(
            EC.visibility_of_element_located((By.ID, "loginForm"))
        )
        assert login_form.is_displayed(), "Login form is not visible"

        # Use the account created by ST 1
        # ST 1 creates a new account dynamically, so we need
        # a known existing test account for login testing.
        identifier = "01700000005"  # Known test account
        password = "user123456789"

        driver.find_element(By.ID, "identifier").send_keys(identifier)
        driver.find_element(By.ID, "password").send_keys(password)

        login_button = wait.until(
            EC.visibility_of_element_located((By.ID, "loginButton"))
        )

        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});",
            login_button
        )

        driver.execute_script(
            "arguments[0].click();",
            login_button
        )

        # Wait for successful login redirect or visible error
        wait.until(
            lambda d: (
                "/dashboard/" in d.current_url
                or "/admin-dashboard/" in d.current_url
                or (
                    d.find_element(By.ID, "formAlert").is_displayed()
                    and d.find_element(By.ID, "formAlert").text.strip()
                )
            )
        )

        # Successful login must redirect away from login page
        assert "/login/" not in driver.current_url, (
            f"Login failed. Current URL: {driver.current_url}"
        )

    finally:
        driver.quit()

def test_credential_validation_and_role_permissions():
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 10)

    try:
        # -----------------------------
        # Part 1: Invalid credentials
        # -----------------------------
        driver.get(f"{BASE_URL}/login/")

        wait.until(
            EC.visibility_of_element_located((By.ID, "loginForm"))
        )

        driver.find_element(By.ID, "identifier").send_keys(
            "01700000005"  # Known test account
        )
        driver.find_element(By.ID, "password").send_keys(
            "wrong123456789"  # Known wrong password for the test account
        )

        login_button = wait.until(
            EC.visibility_of_element_located((By.ID, "loginButton"))
        )

        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});",
            login_button
        )

        driver.execute_script(
            "arguments[0].click();",
            login_button
        )

        # Wait for error message
        wait.until(
            lambda d: (
                d.find_element(By.ID, "formAlert").is_displayed()
                and d.find_element(By.ID, "formAlert").text.strip()
            )
        )

        alert = driver.find_element(By.ID, "formAlert").text.strip()

        assert alert, "Invalid credentials did not produce an error message"
        assert "/login/" in driver.current_url, (
            "Invalid credentials were accepted"
        )

        # -----------------------------
        # Part 2: Role permission
        # -----------------------------
        #
        # Log in using the existing normal-user account.
        #
        driver.find_element(By.ID, "identifier").clear()
        driver.find_element(By.ID, "password").clear()

        driver.find_element(By.ID, "identifier").send_keys(
            "01700000005"  # Known test account
        )
        driver.find_element(By.ID, "password").send_keys(
            "user123456789"  # Known correct password for the test account
        )

        driver.execute_script(
            "arguments[0].click();",
            login_button
        )

        wait.until(
            lambda d: "/dashboard/" in d.current_url
            or "/admin-dashboard/" in d.current_url
        )

        # The test account should NOT be an admin.
        assert "/admin-dashboard/" not in driver.current_url, (
            "Normal user was redirected to admin dashboard"
        )

        # Try opening admin verification directly.
        driver.get(f"{BASE_URL}/admin-verification/")

        wait.until(
            lambda d: d.execute_script("return document.readyState")
            == "complete"
        )

        # A non-admin must not remain on the admin verification page.
        assert "/admin-verification/" not in driver.current_url, (
            "Normal user was able to access admin verification page"
        )

    finally:
        driver.quit()

def test_logout():
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 10)

    try:
        # Login first
        driver.get(f"{BASE_URL}/login/")

        wait.until(
            EC.visibility_of_element_located((By.ID, "loginForm"))
        )

        driver.find_element(By.ID, "identifier").send_keys(
            "01700000005"
        )
        driver.find_element(By.ID, "password").send_keys(
            "user123456789"
        )

        login_button = wait.until(
            EC.element_to_be_clickable((By.ID, "loginButton"))
        )

        driver.execute_script(
            "arguments[0].click();",
            login_button
        )

        # Wait until dashboard opens
        wait.until(
            lambda d: "/dashboard/" in d.current_url
        )

        # Confirm dashboard is actually visible
        wait.until(
            EC.visibility_of_element_located((By.ID, "logoutButton"))
        )

        # Click real logout button
        logout_button = driver.find_element(
            By.ID, "logoutButton"
        )

        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});",
            logout_button
        )

        driver.execute_script(
            "arguments[0].click();",
            logout_button
        )

        # After logout, user should leave the protected dashboard
        wait.until(
            lambda d: "/login/" in d.current_url
        )

        assert "/login/" in driver.current_url, (
            f"Logout failed. Current URL: {driver.current_url}"
        )

        # Verify token is removed from browser storage
        token = driver.execute_script(
            "return localStorage.getItem('helpnet_token');"
        )

        assert token is None, (
            "Authentication token still exists after logout"
        )

    finally:
        driver.quit()

def test_password_reset():
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 10)

    try:
        driver.get(f"{BASE_URL}/forgot-password/")

        # Confirm forgot-password form is visible
        wait.until(
            EC.visibility_of_element_located(
                (By.ID, "forgotPasswordForm")
            )
        )

        email_input = wait.until(
            EC.visibility_of_element_located(
                (By.ID, "email")
            )
        )

        email_input.send_keys(
            "user@gmail.com"  # Known test account email
        )

        reset_button = wait.until(
            EC.element_to_be_clickable(
                (By.ID, "forgotPasswordButton")
            )
        )

        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});",
            reset_button
        )

        driver.execute_script(
            "arguments[0].click();",
            reset_button
        )

        # Wait for the frontend response
        message = wait.until(
            EC.visibility_of_element_located(
                (By.ID, "forgotPasswordMessage")
            )
        )

        message_text = message.text.strip()

        assert message_text, (
            "Password reset did not produce a visible message"
        )

    finally:
        driver.quit()

def test_language_switch():
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 10)

    try:
        driver.get(f"{BASE_URL}/login/")

        # Wait for i18n to initialize
        login_title = wait.until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, '[data-i18n="loginTitle"]')
            )
        )

        lang_button = wait.until(
            EC.element_to_be_clickable((By.ID, "langToggle"))
        )

        # Start from Bangla
        driver.execute_script(
            "localStorage.setItem('helpnet_lang', 'bn');"
        )
        driver.refresh()

        login_title = wait.until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, '[data-i18n="loginTitle"]')
            )
        )

        wait.until(
            lambda d: login_title.text.strip() == "লগইন করুন"
        )

        assert login_title.text.strip() == "লগইন করুন", (
            "Bangla language was not applied"
        )

        # Switch to English
        lang_button = wait.until(
            EC.element_to_be_clickable((By.ID, "langToggle"))
        )

        driver.execute_script(
            "arguments[0].click();",
            lang_button
        )

        wait.until(
            lambda d: d.find_element(
                By.CSS_SELECTOR,
                '[data-i18n="loginTitle"]'
            ).text.strip() == "Log in"
        )

        login_title = driver.find_element(
            By.CSS_SELECTOR,
            '[data-i18n="loginTitle"]'
        )

        assert login_title.text.strip() == "Log in", (
            "English language was not applied"
        )

        # Switch back to Bangla
        lang_button = wait.until(
            EC.element_to_be_clickable((By.ID, "langToggle"))
        )

        driver.execute_script(
            "arguments[0].click();",
            lang_button
        )

        wait.until(
            lambda d: d.find_element(
                By.CSS_SELECTOR,
                '[data-i18n="loginTitle"]'
            ).text.strip() == "লগইন করুন"
        )

        assert driver.find_element(
            By.CSS_SELECTOR,
            '[data-i18n="loginTitle"]'
        ).text.strip() == "লগইন করুন"

    finally:
        driver.quit()

def test_login_st7():
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 10)

    try:
        driver.get(f"{BASE_URL}/login/")

        identifier = wait.until(
            EC.visibility_of_element_located((By.ID, "identifier"))
        )
        password = wait.until(
            EC.visibility_of_element_located((By.ID, "password"))
        )
        login_button = wait.until(
            EC.element_to_be_clickable((By.ID, "loginButton"))
        )

        identifier.send_keys("01700000005")
        password.send_keys("user123456789")

        driver.execute_script(
            "arguments[0].click();",
            login_button
        )

        wait.until(
            lambda d: "/dashboard/" in d.current_url
            or "/admin-dashboard/" in d.current_url
        )

        assert (
            "/dashboard/" in driver.current_url
            or "/admin-dashboard/" in driver.current_url
        ), "User did not reach authenticated area"

    finally:
        driver.quit()

def test_protected_access_st8():
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 10)

    try:
        # Make sure there is no existing login session
        driver.get(f"{BASE_URL}/login/")

        driver.execute_script("""
            localStorage.removeItem('helpnet_token');
            localStorage.removeItem('helpnet_user');
            localStorage.removeItem('refreshToken');
        """)

        # Try to access protected dashboard directly
        driver.get(f"{BASE_URL}/dashboard/")

        # Protected page should redirect to login
        wait.until(
            lambda d: "/login/" in d.current_url
        )

        assert "/login/" in driver.current_url, (
            "Unauthenticated user could access protected dashboard"
        )

    finally:
        driver.quit()

def test_logout_st9():
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 10)

    try:
        driver.get(f"{BASE_URL}/login/")

        identifier = wait.until(
            EC.visibility_of_element_located((By.ID, "identifier"))
        )
        password = wait.until(
            EC.visibility_of_element_located((By.ID, "password"))
        )
        login_button = wait.until(
            EC.element_to_be_clickable((By.ID, "loginButton"))
        )

        identifier.send_keys("01700000005")
        password.send_keys("user123456789")

        driver.execute_script(
            "arguments[0].click();",
            login_button
        )

        wait.until(
            lambda d: "/dashboard/" in d.current_url
            or "/admin-dashboard/" in d.current_url
        )

        logout_button = wait.until(
            EC.element_to_be_clickable((By.ID, "logoutButton"))
        )

        driver.execute_script(
            "arguments[0].click();",
            logout_button
        )

        # Verify logout redirect
        wait.until(
            lambda d: "/login/" in d.current_url
        )

        assert "/login/" in driver.current_url, (
            "User was not redirected to login after logout"
        )

        # Try protected page after logout
        driver.get(f"{BASE_URL}/dashboard/")

        wait.until(
            lambda d: "/login/" in d.current_url
        )

        assert "/login/" in driver.current_url, (
            "Protected dashboard remained accessible after logout"
        )

    finally:
        driver.quit()

def test_password_reset_st10():
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 10)

    try:
        # Open reset page without uid/token
        driver.get(f"{BASE_URL}/reset-password/")

        message = wait.until(
            EC.visibility_of_element_located(
                (By.ID, "resetPasswordMessage")
            )
        )

        reset_button = wait.until(
            EC.presence_of_element_located(
                (By.ID, "resetPasswordButton")
            )
        )

        # Verify invalid/incomplete reset-link message
        wait.until(
            lambda d: "অসম্পূর্ণ বা অবৈধ" in message.text
        )

        assert "অসম্পূর্ণ বা অবৈধ" in message.text, (
            "Invalid reset-link message was not shown"
        )

        # Button must be disabled when uid/token are missing
        assert reset_button.get_attribute("disabled") is not None, (
            "Reset button was not disabled for an invalid reset link"
        )

    finally:
        driver.quit()


def test_nid_submission():
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 15)

    try:
        # -------------------------------------------------
        # 1. Create a fresh Citizen account through frontend
        # -------------------------------------------------
        driver.get(f"{BASE_URL}/register/")

        timestamp = str(int(time.time()))
        phone = "018" + timestamp[-8:]
        email = f"nidtest{timestamp}@example.com"

        wait.until(
            EC.visibility_of_element_located((By.ID, "fullName"))
        ).send_keys("NID Test User")

        driver.find_element(
            By.ID, "phoneNumber"
        ).send_keys(phone)

        driver.find_element(
            By.ID, "password"
        ).send_keys("TestPassword123")

        driver.find_element(
            By.ID, "email"
        ).send_keys(email)

        Select(
            driver.find_element(By.ID, "role")
        ).select_by_value("Citizen")

        Select(
            driver.find_element(By.ID, "district")
        ).select_by_value("Dhaka")

        driver.find_element(
            By.ID, "upazila"
        ).send_keys("Dhanmondi")

        register_button = wait.until(
            EC.presence_of_element_located(
                (By.ID, "registerButton")
            )
        )

        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});",
            register_button
        )

        driver.execute_script(
            "arguments[0].click();",
            register_button
        )

        # Registration should succeed
        wait.until(
            lambda d: "/login/" in d.current_url
            or (
                d.find_element(By.ID, "formAlert").text.strip() != ""
            )
        )

        # -------------------------------------------------
        # 2. Login with the fresh account
        # -------------------------------------------------
        if "/login/" not in driver.current_url:
            driver.get(f"{BASE_URL}/login/")

        identifier = wait.until(
            EC.visibility_of_element_located(
                (By.ID, "identifier")
            )
        )

        password = driver.find_element(
            By.ID, "password"
        )

        identifier.send_keys(phone)
        password.send_keys("TestPassword123")

        login_button = wait.until(
            EC.presence_of_element_located(
                (By.ID, "loginButton")
            )
        )

        driver.execute_script(
            "arguments[0].click();",
            login_button
        )

        wait.until(
            lambda d: "/dashboard/" in d.current_url
        )

        # -------------------------------------------------
        # 3. Open NID verification
        # -------------------------------------------------
        driver.get(
            f"{BASE_URL}/nid-verification/"
        )

        status = wait.until(
            EC.visibility_of_element_located(
                (By.ID, "verificationStatus")
            )
        )

        # Fresh account should start unverified
        assert "যাচাই করা হয়নি" in status.text, (
            "Fresh account is not in unverified state"
        )

        # -------------------------------------------------
        # 4. Negative test: submit without selecting a file
        # -------------------------------------------------
        submit_button = wait.until(
            EC.presence_of_element_located(
                (By.ID, "submitVerification")
            )
        )

        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});",
            submit_button
        )

        driver.execute_script(
            "arguments[0].click();",
            submit_button
        )

        # The NID JavaScript displays:
        # "অনুগ্রহ করে একটি ফাইল নির্বাচন করুন।"
        # Find the visible page element containing that message.
        error = wait.until(
            lambda d: next(
                (
                    element
                    for element in d.find_elements(
                        By.XPATH,
                        "//*[contains(normalize-space(.), "
                        "'একটি ফাইল নির্বাচন করুন')]"
                    )
                    if element.is_displayed()
                ),
                False
            )
        )

        assert "একটি ফাইল নির্বাচন করুন" in error.text, (
            "ST 12 FAIL: Missing-file validation message not shown."
        )

        # -------------------------------------------------
        # 5. Create harmless temporary PDF
        # -------------------------------------------------
        pdf_path = None

        try:
            with tempfile.NamedTemporaryFile(
                suffix=".pdf",
                delete=False
            ) as temp_file:
                temp_file.write(
                    b"%PDF-1.4\n"
                    b"1 0 obj\n"
                    b"<< /Type /Catalog /Pages 2 0 R >>\n"
                    b"endobj\n"
                    b"2 0 obj\n"
                    b"<< /Type /Pages /Kids [] /Count 0 >>\n"
                    b"endobj\n"
                    b"trailer\n"
                    b"<< /Root 1 0 R >>\n"
                    b"%%EOF"
                )
                pdf_path = temp_file.name

            # -------------------------------------------------
            # 6. Select NID and upload PDF
            # -------------------------------------------------
            Select(
                driver.find_element(By.ID, "documentType")
            ).select_by_value("nid")

            driver.find_element(
                By.ID,
                "verificationDocument"
            ).send_keys(pdf_path)

            submit_button = wait.until(
                EC.presence_of_element_located(
                    (By.ID, "submitVerification")
                )
            )

            driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});",
                submit_button
            )

            driver.execute_script(
                "arguments[0].click();",
                submit_button
            )

            # -------------------------------------------------
            # 7. Verify pending status
            # -------------------------------------------------
            wait.until(
                lambda d: "অপেক্ষমাণ" in
                d.find_element(
                    By.ID,
                    "verificationStatus"
                ).text
            )

            assert "অপেক্ষমাণ" in driver.find_element(
                By.ID,
                "verificationStatus"
            ).text, (
                "ST 12 FAIL: NID verification did not become pending."
            )

            print(
                "ST 12 PASS: NID document submission "
                "and pending verification status confirmed."
            )

        finally:
            if pdf_path and os.path.exists(pdf_path):
                os.remove(pdf_path)

    finally:
        driver.quit()



def test_verified_badge_st13():
    driver = webdriver.Chrome()

    try:
        # Login as approved/verified user
        driver.get(BASE_URL + "/login/")

        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, "identifier"))
        ).send_keys("01700000005")

        driver.find_element(By.ID, "password").send_keys("user123456789")
        driver.find_element(By.ID, "loginButton").click()

        WebDriverWait(driver, 10).until(
            lambda d: "/dashboard/" in d.current_url
            or "/admin-dashboard/" in d.current_url
        )

        # Open profile
        driver.get(BASE_URL + "/profile/")

        # Wait for profile.js to render the verified badge
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script("""
                const badge = document.getElementById("verifiedBadge");
                return badge && !badge.hidden && badge.innerText.includes("✓");
            """)
        )

        verified_badge = driver.find_element(By.ID, "verifiedBadge")

        assert verified_badge.is_displayed(), (
            "ST 13 FAIL: Verified badge is not visible for approved user."
        )

        assert "✓" in verified_badge.text, (
            "ST 13 FAIL: Verified badge does not contain the verified mark."
        )

        print("ST 13 PASS: Approved user shows visible Verified badge.")

    finally:
        driver.quit()


def test_admin_verification_st14():
    driver = webdriver.Chrome()

    unique = str(int(time.time()))
    citizen_phone = "018" + unique[-8:]
    citizen_email = f"st14_{unique}@gmail.com"

    pdf_path = None

    try:
        # ---------------------------------------------------------
        # 1. Register a fresh Citizen account
        # ---------------------------------------------------------
        driver.get(BASE_URL + "/register/")

        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located(
                (By.ID, "registerForm")
            )
        )

        WebDriverWait(driver, 10).until(
            lambda d: d.find_element(
                By.CSS_SELECTOR,
                '#role option[value="Citizen"]'
            )
        )

        driver.find_element(
            By.ID,
            "fullName"
        ).send_keys("ST14 Verification User")

        driver.find_element(
            By.ID,
            "phoneNumber"
        ).send_keys(citizen_phone)

        driver.find_element(
            By.ID,
            "password"
        ).send_keys("Test123456789")

        driver.find_element(
            By.ID,
            "email"
        ).send_keys(citizen_email)

        Select(
            driver.find_element(By.ID, "role")
        ).select_by_value("Citizen")

        Select(
            driver.find_element(By.ID, "district")
        ).select_by_value("Dhaka")

        driver.find_element(
            By.ID,
            "upazila"
        ).send_keys("Dhanmondi")

        # Use JavaScript click to avoid page-layout click interception.
        register_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.ID, "registerButton")
            )
        )

        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});",
            register_button
        )

        driver.execute_script(
            "arguments[0].click();",
            register_button
        )

        # Wait for registration result.
        WebDriverWait(driver, 10).until(
            lambda d: (
                "/login/" in d.current_url
            )
            or (
                d.find_element(
                    By.ID,
                    "formAlert"
                ).is_displayed()
                and
                d.find_element(
                    By.ID,
                    "formAlert"
                ).text.strip()
            )
        )

        # ---------------------------------------------------------
        # 2. Login as the newly created Citizen
        # ---------------------------------------------------------
        driver.get(BASE_URL + "/login/")

        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located(
                (By.ID, "identifier")
            )
        ).send_keys(citizen_phone)

        driver.find_element(
            By.ID,
            "password"
        ).send_keys("Test123456789")

        login_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.ID, "loginButton")
            )
        )

        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});",
            login_button
        )

        driver.execute_script(
            "arguments[0].click();",
            login_button
        )

        WebDriverWait(driver, 10).until(
            lambda d: (
                "/dashboard/" in d.current_url
                or "/admin-dashboard/" in d.current_url
            )
        )

        # ---------------------------------------------------------
        # 3. Submit NID verification
        # ---------------------------------------------------------
        driver.get(
            BASE_URL + "/nid-verification/"
        )

        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located(
                (By.ID, "nidVerificationForm")
            )
        )

        # Create a harmless temporary PDF.
        with tempfile.NamedTemporaryFile(
            suffix=".pdf",
            delete=False
        ) as temp_file:
            temp_file.write(
                b"%PDF-1.4\n"
                b"1 0 obj\n"
                b"<< /Type /Catalog /Pages 2 0 R >>\n"
                b"endobj\n"
                b"2 0 obj\n"
                b"<< /Type /Pages /Kids [] /Count 0 >>\n"
                b"endobj\n"
                b"trailer\n"
                b"<< /Root 1 0 R >>\n"
                b"%%EOF"
            )
            pdf_path = temp_file.name

        Select(
            driver.find_element(By.ID, "documentType")
        ).select_by_value("nid")

        driver.find_element(
            By.ID,
            "verificationDocument"
        ).send_keys(pdf_path)

        submit_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.ID, "submitVerification")
            )
        )

        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});",
            submit_button
        )

        driver.execute_script(
            "arguments[0].click();",
            submit_button
        )

        # Wait for verification request to become pending.
        WebDriverWait(driver, 15).until(
            lambda d: (
                "অপেক্ষমাণ" in
                d.find_element(
                    By.ID,
                    "verificationStatus"
                ).text
            )
            or
            (
                d.find_element(
                    By.ID,
                    "verificationStatus"
                ).get_attribute("class")
                and
                "pending" in
                d.find_element(
                    By.ID,
                    "verificationStatus"
                ).get_attribute("class").lower()
            )
        )

        # ---------------------------------------------------------
        # 4. Login as Admin
        # ---------------------------------------------------------
        driver.get(
            BASE_URL + "/login/"
        )

        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located(
                (By.ID, "identifier")
            )
        ).send_keys("01700000001")

        driver.find_element(
            By.ID,
            "password"
        ).send_keys("admin123456789")

        admin_login_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.ID, "loginButton")
            )
        )

        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});",
            admin_login_button
        )

        driver.execute_script(
            "arguments[0].click();",
            admin_login_button
        )

        WebDriverWait(driver, 10).until(
            lambda d: "/admin-dashboard/" in d.current_url
        )

        # ---------------------------------------------------------
        # 5. Open Admin Verification
        # ---------------------------------------------------------
        driver.get(
            BASE_URL + "/admin-verification/"
        )

        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located(
                (By.ID, "verificationList")
            )
        )

        # Find the request belonging specifically to this test user.
        request_card = WebDriverWait(driver, 15).until(
            lambda d: next(
                (
                    card
                    for card in d.find_elements(
                        By.CSS_SELECTOR,
                        "#verificationList .card"
                    )
                    if citizen_phone in card.text
                ),
                False
            )
        )

        assert citizen_phone in request_card.text, (
            "ST 14 FAIL: Pending verification request not found."
        )

        # ---------------------------------------------------------
        # 6. Approve request
        # ---------------------------------------------------------
        approve_button = request_card.find_element(
            By.CSS_SELECTOR,
            ".approve-btn"
        )

        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});",
            approve_button
        )

        driver.execute_script(
            "arguments[0].click();",
            approve_button
        )

        # First alert: confirmation
        WebDriverWait(driver, 5).until(
            EC.alert_is_present()
        )

        confirmation_alert = driver.switch_to.alert

        assert "approve" in confirmation_alert.text.lower(), (
            "ST 14 FAIL: Approval confirmation message not shown."
        )

        confirmation_alert.accept()

        # Second alert: successful approval
        WebDriverWait(driver, 5).until(
            EC.alert_is_present()
        )

        success_alert = driver.switch_to.alert

        assert "approved successfully" in (
            success_alert.text.lower()
        ), (
            "ST 14 FAIL: Approval success message not shown."
        )

        success_alert.accept()

        # ---------------------------------------------------------
        # 7. Verify request disappeared after approval
        # ---------------------------------------------------------
        WebDriverWait(driver, 10).until(
            lambda d: all(
                citizen_phone not in card.text
                for card in d.find_elements(
                    By.CSS_SELECTOR,
                    "#verificationList .card"
                )
            )
        )

        print(
            "ST 14 PASS: Admin successfully approved "
            "the pending verification request."
        )

    finally:
        if pdf_path and os.path.exists(pdf_path):
            os.remove(pdf_path)

        driver.quit()
