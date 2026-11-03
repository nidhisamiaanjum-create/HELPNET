import re
from pathlib import Path

import pytest
from selenium.common.exceptions import UnexpectedAlertPresentException


EVIDENCE_DIR = (
    Path(__file__).resolve().parents[2]
    / "project_documentation"
    / "selenium_evidence"
)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)


@pytest.fixture(autouse=True)
def capture_browser_screenshot(request):
    if "browser" not in request.fixturenames:
        yield
        return

    browser = request.getfixturevalue("browser")
    yield

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    report = getattr(request.node, "rep_call", None)
    result = "failed" if report and report.failed else "passed"
    test_name = re.sub(r"[^A-Za-z0-9._-]+", "-", request.node.nodeid).strip("-")
    screenshot_path = EVIDENCE_DIR / f"{test_name[:160]}-{result}.png"
    try:
        browser.save_screenshot(str(screenshot_path))
    except UnexpectedAlertPresentException:
        browser.switch_to.alert.accept()
        browser.save_screenshot(str(screenshot_path))
