import os
import json
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8000"

# Credentials from environment or defaults
LOGIN_IDENTIFIER = os.environ.get("TEST_LOGIN_IDENTIFIER", "01712345671")
LOGIN_PASSWORD = os.environ.get("TEST_LOGIN_PASSWORD", "c123456789")

def send_request(url, method="POST", headers=None, data=None):
    if headers is None:
        headers = {}
    if data is not None:
        payload = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
    else:
        payload = None

    req = urllib.request.Request(url, data=payload, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            status_code = response.getcode()
            body = response.read().decode("utf-8")
            try:
                parsed = json.loads(body)
            except Exception:
                parsed = body
            return status_code, parsed
    except urllib.error.HTTPError as e:
        status_code = e.code
        body = e.read().decode("utf-8")
        try:
            parsed = json.loads(body)
        except Exception:
            parsed = body
        return status_code, parsed
    except Exception as e:
        return 0, str(e)

def run_tests():
    print("=" * 60)
    print("S2-T08 — Test Logout / Token Invalidation")
    print("=" * 60)

    # Step 1: Login to get tokens
    print("\n[Step] Performing login to acquire access and refresh tokens...")
    status_code, resp = send_request(
        f"{BASE_URL}/api/auth/login/",
        method="POST",
        data={"identifier": LOGIN_IDENTIFIER, "password": LOGIN_PASSWORD}
    )

    if status_code != 200 or not resp.get("success"):
        print(f"FAILED to login: HTTP {status_code} - {resp}")
        return False

    access_token = resp["data"]["access"]
    refresh_token = resp["data"]["refresh"]
    print("Login successful! Access and refresh tokens acquired.")

    # -------------------------------------------------------------
    # TEST 1: Logout with valid refresh token
    # -------------------------------------------------------------
    print("\n--- TEST 1 — Logout with valid refresh token ---")
    status_code_1, resp_1 = send_request(
        f"{BASE_URL}/api/auth/logout/",
        method="POST",
        headers={"Authorization": f"Bearer {access_token}"},
        data={"refresh": refresh_token}
    )
    print(f"Status Code: {status_code_1}")
    print(f"Response Body: {json.dumps(resp_1, indent=2)}")

    test_1_pass = (
        status_code_1 == 200
        and resp_1.get("success") is True
        and resp_1.get("data") is None
        and resp_1.get("message") == "Logout successful."
    )
    if test_1_pass:
        print("TEST 1 — Logout with valid refresh token: PASSED")
    else:
        print("TEST 1 — Logout with valid refresh token: FAILED")

    # -------------------------------------------------------------
    # TEST 2: Test the SAME refresh token again
    # -------------------------------------------------------------
    print("\n--- TEST 2 — Reuse blacklisted refresh token ---")
    status_code_2, resp_2 = send_request(
        f"{BASE_URL}/api/auth/logout/",
        method="POST",
        headers={"Authorization": f"Bearer {access_token}"},
        data={"refresh": refresh_token}
    )
    print(f"Status Code: {status_code_2}")
    print(f"Response Body: {json.dumps(resp_2, indent=2)}")

    test_2_pass = (
        status_code_2 == 400
        and resp_2.get("success") is False
        and resp_2.get("data") is None
        and resp_2.get("message") == "Invalid or expired refresh token."
    )
    if test_2_pass:
        print("TEST 2 — Reuse blacklisted refresh token: PASSED")
    else:
        print("TEST 2 — Reuse blacklisted refresh token: FAILED")

    # -------------------------------------------------------------
    # TEST 3: Test logout without a refresh token
    # -------------------------------------------------------------
    print("\n--- TEST 3 — Logout without refresh token ---")
    status_code_3, resp_3 = send_request(
        f"{BASE_URL}/api/auth/logout/",
        method="POST",
        headers={"Authorization": f"Bearer {access_token}"},
        data={}
    )
    print(f"Status Code: {status_code_3}")
    print(f"Response Body: {json.dumps(resp_3, indent=2)}")

    test_3_pass = (
        status_code_3 == 400
        and resp_3.get("success") is False
        and resp_3.get("data") is None
        and resp_3.get("message") == "Refresh token is required."
    )
    if test_3_pass:
        print("TEST 3 — Logout without refresh token: PASSED")
    else:
        print("TEST 3 — Logout without refresh token: FAILED")

    # -------------------------------------------------------------
    # TEST 4: Check the protected endpoint (without auth header)
    # -------------------------------------------------------------
    print("\n--- TEST 4 — Unauthenticated logout request ---")
    status_code_4, resp_4 = send_request(
        f"{BASE_URL}/api/auth/logout/",
        method="POST",
        headers={},
        data={"refresh": refresh_token}
    )
    print(f"Status Code: {status_code_4}")
    print(f"Response Body: {json.dumps(resp_4, indent=2)}")

    test_4_pass = (
        status_code_4 == 401
    )
    if test_4_pass:
        print("TEST 4 — Unauthenticated logout request: PASSED")
    else:
        print("TEST 4 — Unauthenticated logout request: FAILED")

    # -------------------------------------------------------------
    # Summary
    # -------------------------------------------------------------
    print("\n" + "=" * 60)
    print("S2-T08 — Logout Testing Summary")
    print("=" * 60)
    print(f"TEST 1 — Valid refresh token logout: {'PASS' if test_1_pass else 'FAIL'}")
    print(f"TEST 2 — Reuse blacklisted token: {'PASS' if test_2_pass else 'FAIL'}")
    print(f"TEST 3 — Missing refresh token: {'PASS' if test_3_pass else 'FAIL'}")
    print(f"TEST 4 — Unauthenticated request: {'PASS' if test_4_pass else 'FAIL'}")
    
    all_passed = test_1_pass and test_2_pass and test_3_pass and test_4_pass
    print(f"\nOverall: {'S2-T08 PASS' if all_passed else 'S2-T08 FAIL'}")
    print("=" * 60)
    return all_passed

if __name__ == "__main__":
    run_tests()
