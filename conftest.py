"""
Shared pytest fixtures for TicketsCAD smoke tests.

Provides browser setup, login, frame navigation, error log monitoring,
and browser console capture for the entire test suite.
"""
from __future__ import annotations

import os
import re
import time
import json
import subprocess
from pathlib import Path
from datetime import datetime

import pytest

from selenium import webdriver
from selenium.common.exceptions import (
    TimeoutException,
    StaleElementReferenceException,
    NoSuchElementException,
    NoSuchFrameException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService


# ---------------------------------------------------------------------------
# pytest CLI options
# ---------------------------------------------------------------------------
def pytest_addoption(parser):
    parser.addoption("--base-url", default="http://localhost/tickets/",
                     help="TicketsCAD base URL")
    parser.addoption("--admin-user", default="admin",
                     help="Admin username")
    parser.addoption("--admin-pass", default="testing",
                     help="Admin password")
    parser.addoption("--guest-user", default="guest",
                     help="Guest username")
    parser.addoption("--guest-pass", default="guest",
                     help="Guest password")
    parser.addoption("--browser", default="edge",
                     choices=["edge", "chrome", "firefox"],
                     help="Browser to use")
    parser.addoption("--headed", action="store_true", default=True,
                     help="Run with visible browser (default)")
    parser.addoption("--headless", action="store_true", default=False,
                     help="Run in headless mode")
    parser.addoption("--error-log",
                     default=r"C:\xampp\8.2.4\apache\logs\error.log",
                     help="Path to PHP/Apache error log")
    parser.addoption("--screenshot-dir", default="screenshots",
                     help="Directory for failure screenshots")


# ---------------------------------------------------------------------------
# Error log watcher
# ---------------------------------------------------------------------------
class ErrorLogWatcher:
    """Monitors the Apache/PHP error log for new entries during tests."""

    def __init__(self, log_path: str):
        self.log_path = Path(log_path)
        self.start_pos = 0
        self.baseline_errors = []

    def mark_position(self):
        """Record current end of file as baseline."""
        if self.log_path.exists():
            self.start_pos = self.log_path.stat().st_size
        else:
            self.start_pos = 0

    def get_new_entries(self) -> list[str]:
        """Return log entries written since mark_position()."""
        if not self.log_path.exists():
            return []
        try:
            with open(self.log_path, "r", encoding="utf-8", errors="replace") as f:
                f.seek(self.start_pos)
                content = f.read()
            if not content.strip():
                return []
            return [line.strip() for line in content.splitlines() if line.strip()]
        except Exception:
            return []

    def get_php_errors(self) -> list[str]:
        """Return only PHP error/warning/notice entries (not deprecation notices)."""
        entries = self.get_new_entries()
        php_errors = []
        for entry in entries:
            low = entry.lower()
            # Skip deprecation notices — they're expected in legacy code
            if "php deprecated:" in low:
                continue
            if any(marker in low for marker in [
                "php fatal error",
                "php parse error",
                "php warning",
                "php notice",
                "undefined variable",
                "undefined array key",
                "undefined index",
                "call to undefined function",
            ]):
                php_errors.append(entry)
        return php_errors


# ---------------------------------------------------------------------------
# Browser console capture
# ---------------------------------------------------------------------------
class ConsoleCapture:
    """Captures browser console errors via Chrome DevTools Protocol."""

    def __init__(self, driver):
        self.driver = driver
        self.supports_logs = hasattr(driver, 'get_log')

    def get_errors(self) -> list[str]:
        """Return JS console errors from the browser."""
        if not self.supports_logs:
            return []
        try:
            logs = self.driver.get_log('browser')
            errors = []
            for entry in logs:
                if entry.get('level') in ('SEVERE', 'ERROR'):
                    msg = entry.get('message', '')
                    # Skip common non-actionable errors
                    if 'favicon.ico' in msg:
                        continue
                    errors.append(msg)
            return errors
        except Exception:
            return []


# ---------------------------------------------------------------------------
# Frame navigation helpers
# ---------------------------------------------------------------------------
class FrameNav:
    """Helper for navigating TicketsCAD's frameset structure."""

    def __init__(self, driver, wait):
        self.driver = driver
        self.wait = wait

    def to_default(self):
        """Switch to default content (top level)."""
        self.driver.switch_to.default_content()

    def to_main(self):
        """Switch into the 'main' frame."""
        self.driver.switch_to.default_content()
        self.wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "main")))

    def to_upper(self):
        """Switch into the 'upper' frame (top nav bar)."""
        self.driver.switch_to.default_content()
        self.wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "upper")))

    def main_frame_src(self) -> str:
        """Get the current src URL of the main frame."""
        self.driver.switch_to.default_content()
        try:
            el = self.driver.find_element(By.NAME, "main")
            return (el.get_attribute("src") or "").strip()
        except Exception:
            return ""

    def main_page_source(self) -> str:
        """Get the page source from the main frame."""
        self.to_main()
        try:
            return self.driver.page_source or ""
        finally:
            self.driver.switch_to.default_content()

    def click_tab(self, tab_id: str):
        """Click a navigation tab in the upper frame."""
        self.to_upper()
        try:
            el = self.driver.find_element(By.ID, tab_id)
            try:
                el.click()
            except Exception:
                self.driver.execute_script("arguments[0].click();", el)
        finally:
            self.driver.switch_to.default_content()

    def wait_for_main_load(self, timeout: float = 3.0):
        """Wait for main frame to finish loading after a tab click."""
        time.sleep(timeout)

    def get_main_errors(self) -> list[str]:
        """Check main frame page source for PHP error markers."""
        source = self.main_page_source().lower()
        error_markers = [
            "fatal error", "parse error", "warning:", "uncaught exception",
            "stack trace", "500 internal server error", "undefined variable",
            "undefined array key", "undefined index",
            "call to undefined function",
        ]
        found = []
        for marker in error_markers:
            if marker in source:
                # Extract the actual error text around the marker
                idx = source.find(marker)
                snippet = source[max(0, idx - 20):idx + 200]
                # Clean HTML
                snippet = re.sub(r'<[^>]+>', ' ', snippet).strip()
                found.append(snippet[:300])
        return found

    def get_visible_text(self) -> str:
        """Get visible text content from main frame."""
        self.to_main()
        try:
            body = self.driver.find_element(By.TAG_NAME, "body")
            return body.text or ""
        except Exception:
            return ""
        finally:
            self.driver.switch_to.default_content()

    def find_forms(self) -> list[dict]:
        """Find all forms in the main frame with their names and actions."""
        self.to_main()
        try:
            forms = self.driver.find_elements(By.TAG_NAME, "form")
            result = []
            for f in forms:
                result.append({
                    "name": f.get_attribute("name") or "",
                    "action": f.get_attribute("action") or "",
                    "method": f.get_attribute("method") or "get",
                    "id": f.get_attribute("id") or "",
                })
            return result
        except Exception:
            return []
        finally:
            self.driver.switch_to.default_content()

    def close_popups(self):
        """Close any popup windows that opened, return to main window."""
        main_handle = self.driver.window_handles[0]
        for handle in self.driver.window_handles[1:]:
            try:
                self.driver.switch_to.window(handle)
                self.driver.close()
            except Exception:
                pass
        self.driver.switch_to.window(main_handle)
        self.driver.switch_to.default_content()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def base_url(request):
    url = request.config.getoption("--base-url")
    if not url.endswith("/"):
        url += "/"
    return url


@pytest.fixture(scope="session")
def admin_creds(request):
    return {
        "user": request.config.getoption("--admin-user"),
        "pass": request.config.getoption("--admin-pass"),
    }


@pytest.fixture(scope="session")
def guest_creds(request):
    return {
        "user": request.config.getoption("--guest-user"),
        "pass": request.config.getoption("--guest-pass"),
    }


@pytest.fixture(scope="session")
def screenshot_dir(request):
    d = Path(request.config.getoption("--screenshot-dir"))
    d.mkdir(parents=True, exist_ok=True)
    return d


@pytest.fixture(scope="session")
def error_log(request):
    watcher = ErrorLogWatcher(request.config.getoption("--error-log"))
    return watcher


@pytest.fixture(scope="session")
def browser(request):
    """Create and return a Selenium WebDriver for the session."""
    browser_name = request.config.getoption("--browser")
    headless = request.config.getoption("--headless")

    driver = None

    if browser_name == "edge":
        options = EdgeOptions()
        options.add_argument("--start-maximized")
        if headless:
            options.add_argument("--headless=new")
        # Enable browser logging
        options.set_capability("ms:loggingPrefs", {"browser": "ALL"})
        driver = webdriver.Edge(options=options)

    elif browser_name == "chrome":
        options = ChromeOptions()
        options.add_argument("--start-maximized")
        if headless:
            options.add_argument("--headless=new")
        options.set_capability("goog:loggingPrefs", {"browser": "ALL"})
        driver = webdriver.Chrome(options=options)

    elif browser_name == "firefox":
        options = FirefoxOptions()
        if headless:
            options.add_argument("--headless")
        driver = webdriver.Firefox(options=options)
        driver.maximize_window()

    driver.set_page_load_timeout(30)
    driver.implicitly_wait(2)

    yield driver

    driver.quit()


@pytest.fixture(scope="session")
def logged_in_browser(browser, base_url, admin_creds):
    """Return a browser that is logged into TicketsCAD as admin."""
    driver = browser
    wait = WebDriverWait(driver, 15)

    driver.get(base_url)

    # Switch into main frame for login
    driver.switch_to.default_content()
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "main")))

    username_el = wait.until(EC.presence_of_element_located((By.NAME, "frm_user")))
    password_el = wait.until(EC.presence_of_element_located((By.NAME, "frm_passwd")))

    username_el.clear()
    username_el.send_keys(admin_creds["user"])
    password_el.clear()
    password_el.send_keys(admin_creds["pass"])

    driver.execute_script("document.login_form.submit();")

    # Wait for login to complete — login fields disappear on success
    login_ok = False
    for _ in range(20):
        time.sleep(1)
        driver.switch_to.default_content()

        current_url = driver.current_url or ""

        # If we got redirected to install.php, go back to index and retry
        if "install.php" in current_url:
            driver.get(base_url)
            time.sleep(3)
            driver.switch_to.default_content()
            # Check if we're now logged in (session preserved)
            frames = driver.find_elements(By.ID, "the_frames")
            if frames:
                try:
                    driver.switch_to.frame("main")
                    still_has_user = driver.find_elements(By.NAME, "frm_user")
                    if not still_has_user:
                        driver.switch_to.default_content()
                        login_ok = True
                        break
                    driver.switch_to.default_content()
                except Exception:
                    driver.switch_to.default_content()
            continue

        # Check if we already have the frameset loaded post-login
        frames = driver.find_elements(By.ID, "the_frames")
        if frames:
            try:
                driver.switch_to.frame("main")
                still_has_user = driver.find_elements(By.NAME, "frm_user")
                still_has_pass = driver.find_elements(By.NAME, "frm_passwd")
                if not still_has_user and not still_has_pass:
                    driver.switch_to.default_content()
                    login_ok = True
                    break
                driver.switch_to.default_content()
            except (NoSuchFrameException, Exception):
                driver.switch_to.default_content()
                continue
        else:
            # Might be a flat page (no frameset), check page source
            source = (driver.page_source or "").lower()
            if "situation" in source or "module:" in source:
                login_ok = True
                break

    if not login_ok:
        # Take debug screenshot
        debug_path = Path.cwd() / "screenshots" / "login_debug.png"
        debug_path.parent.mkdir(parents=True, exist_ok=True)
        driver.save_screenshot(str(debug_path))
        pytest.fail(
            f"Login did not complete within timeout. "
            f"Current URL: {driver.current_url}. "
            f"Debug screenshot saved to {debug_path}"
        )

    # Verify we have the frameset
    driver.switch_to.default_content()
    wait.until(EC.presence_of_element_located((By.ID, "the_frames")))

    return driver


@pytest.fixture(scope="session")
def nav(logged_in_browser):
    """Provide a FrameNav helper bound to the logged-in browser."""
    wait = WebDriverWait(logged_in_browser, 10)
    return FrameNav(logged_in_browser, wait)


@pytest.fixture(scope="session")
def console(logged_in_browser):
    """Provide a ConsoleCapture helper."""
    return ConsoleCapture(logged_in_browser)


@pytest.fixture(autouse=True)
def capture_errors_on_failure(request, error_log, screenshot_dir, browser):
    """After each test, capture PHP errors and screenshot on failure."""
    error_log.mark_position()
    yield
    # After test
    if hasattr(request.node, 'rep_call') and request.node.rep_call.failed:
        # Save screenshot
        test_name = request.node.name.replace("[", "_").replace("]", "")
        screenshot_path = screenshot_dir / f"FAIL_{test_name}.png"
        try:
            browser.save_screenshot(str(screenshot_path))
        except Exception:
            pass

    # Always check for PHP errors after each test
    php_errors = error_log.get_php_errors()
    if php_errors:
        # Attach as test warning (not failure — we track separately)
        for err in php_errors[:5]:
            print(f"\n  PHP ERROR: {err[:200]}")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Store test result on the item for use in fixtures."""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)
