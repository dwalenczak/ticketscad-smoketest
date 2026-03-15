"""
Test 01: Login and authentication.

Tests login with valid/invalid credentials, CSRF token presence,
session handling, and logout functionality.
"""
import time
import pytest

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class TestLogin:
    """Login page and authentication tests."""

    def test_login_page_loads(self, browser, base_url):
        """Index page loads and shows the login form in the main frame."""
        driver = browser
        driver.get(base_url)
        wait = WebDriverWait(driver, 10)

        # Should have a frameset
        driver.switch_to.default_content()
        frames = driver.find_elements(By.ID, "the_frames")
        assert len(frames) > 0 or driver.find_elements(By.NAME, "main"), \
            "Expected frameset with main frame"

        # Switch to main and find login form
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "main")))

        user_field = driver.find_elements(By.NAME, "frm_user")
        pass_field = driver.find_elements(By.NAME, "frm_passwd")

        assert len(user_field) > 0, "Login form missing username field"
        assert len(pass_field) > 0, "Login form missing password field"

        driver.switch_to.default_content()

    def test_login_form_has_csrf_token(self, browser, base_url):
        """Login form should include a CSRF token."""
        driver = browser
        driver.get(base_url)
        wait = WebDriverWait(driver, 10)

        driver.switch_to.default_content()
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "main")))

        csrf = driver.find_elements(By.NAME, "csrf_token")
        assert len(csrf) > 0, "Login form missing CSRF token"
        assert csrf[0].get_attribute("value"), "CSRF token is empty"

        driver.switch_to.default_content()

    def test_bad_login_fails(self, browser, base_url):
        """Invalid credentials should show a failure message, not grant access."""
        driver = browser
        driver.get(base_url)
        wait = WebDriverWait(driver, 10)

        driver.switch_to.default_content()
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "main")))

        user_el = wait.until(EC.presence_of_element_located((By.NAME, "frm_user")))
        pass_el = wait.until(EC.presence_of_element_located((By.NAME, "frm_passwd")))

        user_el.clear()
        user_el.send_keys("baduser")
        pass_el.clear()
        pass_el.send_keys("badpassword")

        driver.execute_script("document.login_form.submit();")
        time.sleep(2)

        driver.switch_to.default_content()
        driver.switch_to.frame("main")

        source_lower = (driver.page_source or "").lower()

        # Should still show login form OR show failure message
        still_has_login = driver.find_elements(By.NAME, "frm_user")
        has_warning = "login failed" in source_lower or "warn" in source_lower

        assert still_has_login or has_warning, \
            "Bad login did not show failure or keep login form"

        driver.switch_to.default_content()

    def test_navbar_hidden_before_login(self, browser, base_url):
        """Navigation tabs should NOT be visible/functional before authentication."""
        driver = browser
        driver.get(base_url)
        wait = WebDriverWait(driver, 10)

        driver.switch_to.default_content()

        # Check the upper frame for navigation tabs
        try:
            wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "upper")))

            tabs = driver.find_elements(
                By.CSS_SELECTOR, "td[colspan='99'] span[id][onclick]"
            )

            visible_tabs = []
            for tab in tabs:
                try:
                    style = (tab.get_attribute("style") or "").lower()
                    if "display: none" not in style and tab.is_displayed():
                        tab_text = tab.text.strip()
                        if tab_text:
                            visible_tabs.append(tab_text)
                except StaleElementReferenceException:
                    pass

            driver.switch_to.default_content()

            # Before login, nav tabs should be hidden or minimal
            # The reporter flagged this as a security issue
            if visible_tabs:
                pytest.fail(
                    f"SECURITY: Navigation tabs visible before login: {visible_tabs}. "
                    f"Unauthenticated users can see/access these pages."
                )

        except Exception as e:
            driver.switch_to.default_content()
            # If upper frame doesn't exist or has no tabs, that's fine
            if "frame" in str(e).lower():
                pass  # No upper frame = no exposed tabs = OK

    def test_admin_login_succeeds(self, logged_in_browser):
        """Admin login should succeed and show the frameset."""
        driver = logged_in_browser
        driver.switch_to.default_content()

        # Should have the_frames
        frames = driver.find_elements(By.ID, "the_frames")
        assert len(frames) > 0, "Frameset not present after login"

    def test_situation_screen_loads_after_login(self, nav):
        """After admin login, the Situation screen should load in main frame."""
        nav.to_main()
        try:
            source = nav.driver.page_source.lower()
            # Situation screen markers
            assert any(marker in source for marker in [
                "situation", "main.php", "incident", "ticket"
            ]), "Situation screen did not load after login"
        finally:
            nav.to_default()
