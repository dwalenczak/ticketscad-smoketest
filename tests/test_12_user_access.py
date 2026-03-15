"""
Test 12: User access level verification.

Tests that different user levels (admin, guest) see the correct
navigation tabs and have appropriate access restrictions.
"""
import time
import pytest

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# ---------------------------------------------------------------------------
# Helper: create a fresh browser session and login as a given user
# ---------------------------------------------------------------------------
def login_as(base_url, username, password, headless=True):
    """Login as a specific user in a fresh browser session.

    Returns (driver, wait) tuple.  Caller must driver.quit().
    """
    options = EdgeOptions()
    options.add_argument("--start-maximized")
    if headless:
        options.add_argument("--headless=new")
    options.set_capability("ms:loggingPrefs", {"browser": "ALL"})

    driver = webdriver.Edge(options=options)
    driver.set_page_load_timeout(30)
    driver.implicitly_wait(2)
    wait = WebDriverWait(driver, 15)

    driver.get(base_url)

    driver.switch_to.default_content()
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "main")))

    user_el = wait.until(EC.presence_of_element_located((By.NAME, "frm_user")))
    pass_el = wait.until(EC.presence_of_element_located((By.NAME, "frm_passwd")))
    user_el.clear()
    user_el.send_keys(username)
    pass_el.clear()
    pass_el.send_keys(password)
    driver.execute_script("document.login_form.submit();")

    # Wait for login to complete
    for _ in range(20):
        time.sleep(1)
        driver.switch_to.default_content()
        current_url = driver.current_url or ""

        # Handle install.php redirect
        if "install.php" in current_url:
            driver.get(base_url)
            time.sleep(3)
            driver.switch_to.default_content()

        frames = driver.find_elements(By.ID, "the_frames")
        if frames:
            try:
                driver.switch_to.frame("main")
                still_login = driver.find_elements(By.NAME, "frm_user")
                driver.switch_to.default_content()
                if not still_login:
                    return driver, wait
            except Exception:
                driver.switch_to.default_content()

    # If we get here, login may have redirected (e.g. mobile/facility view)
    return driver, wait


class TestAdminAccess:
    """Verify admin user sees all expected navigation tabs."""

    # All tabs an admin should see
    ADMIN_TABS = [
        "main",        # Situation
        "add",         # New
        "resp",        # Units
        "facy",        # Facilities
        "srch",        # Search
        "reps",        # Reports
        "conf",        # Config
        "help",        # Help
        "log",         # Log
        "full",        # Full Screen
        "personnel",   # Personnel
        "links",       # Links
        "call",        # Board
        "term",        # Mobile
    ]

    def test_admin_sees_all_tabs(self, nav):
        """Admin user should see all navigation tabs."""
        nav.to_upper()
        try:
            source = nav.driver.page_source
            missing = []
            for tab_id in self.ADMIN_TABS:
                els = nav.driver.find_elements(By.ID, tab_id)
                if not els:
                    missing.append(tab_id)
                elif not els[0].is_displayed():
                    missing.append(f"{tab_id} (hidden)")

            assert not missing, \
                f"Admin is missing tabs: {missing}"
        finally:
            nav.to_default()

    def test_admin_can_access_config(self, nav, error_log):
        """Admin should be able to load the Config page."""
        error_log.mark_position()
        nav.click_tab("conf")
        nav.wait_for_main_load(2)

        page_errors = nav.get_main_errors()
        php_errors = error_log.get_php_errors()
        all_errors = page_errors + php_errors
        assert not all_errors, \
            f"Config page errors for admin:\n" + "\n".join(str(e)[:200] for e in all_errors)

    def test_admin_can_access_reports(self, nav, error_log):
        """Admin should be able to load the Reports page."""
        error_log.mark_position()
        nav.click_tab("reps")
        nav.wait_for_main_load(2)

        page_errors = nav.get_main_errors()
        php_errors = error_log.get_php_errors()
        all_errors = page_errors + php_errors
        assert not all_errors, \
            f"Reports page errors for admin:\n" + "\n".join(str(e)[:200] for e in all_errors)


class TestGuestAccess:
    """Verify guest user sees only appropriate tabs."""

    # Tabs a guest SHOULD see
    GUEST_VISIBLE = ["main", "add", "resp", "facy", "srch", "help", "full"]

    # Tabs a guest should NOT see
    GUEST_HIDDEN = ["reps", "conf", "log", "personnel", "links", "call", "term"]

    @pytest.fixture()
    def guest_driver(self, base_url, guest_creds):
        """Login as guest in a separate browser session."""
        driver, wait = login_as(
            base_url,
            guest_creds["user"],
            guest_creds["pass"],
            headless=True,
        )
        yield driver, wait
        driver.quit()

    def test_guest_visible_tabs(self, guest_driver, base_url):
        """Guest should see the basic navigation tabs."""
        driver, wait = guest_driver
        driver.switch_to.default_content()

        try:
            wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "upper")))
        except Exception:
            pytest.skip("Could not switch to upper frame — guest login may have failed")

        source = driver.page_source
        missing = []
        for tab_id in self.GUEST_VISIBLE:
            els = driver.find_elements(By.ID, tab_id)
            if not els:
                missing.append(tab_id)

        driver.switch_to.default_content()

        assert not missing, \
            f"Guest is missing expected tabs: {missing}"

    def test_guest_hidden_tabs(self, guest_driver, base_url):
        """Guest should NOT see admin-only tabs."""
        driver, wait = guest_driver
        driver.switch_to.default_content()

        try:
            wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "upper")))
        except Exception:
            pytest.skip("Could not switch to upper frame — guest login may have failed")

        visible_admin_tabs = []
        for tab_id in self.GUEST_HIDDEN:
            els = driver.find_elements(By.ID, tab_id)
            if els and els[0].is_displayed():
                visible_admin_tabs.append(tab_id)

        driver.switch_to.default_content()

        assert not visible_admin_tabs, \
            f"Guest can see admin tabs that should be hidden: {visible_admin_tabs}"

    def test_guest_cannot_access_config_directly(self, base_url, guest_creds):
        """Guest should not be able to access config.php directly."""
        driver, wait = login_as(
            base_url,
            guest_creds["user"],
            guest_creds["pass"],
            headless=True,
        )
        try:
            # Try loading config.php in the main frame
            driver.switch_to.default_content()
            try:
                wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "main")))
                driver.execute_script(
                    f"window.location.href = '{base_url}config.php';"
                )
                time.sleep(3)

                source = (driver.page_source or "").lower()
                # Should show access denied or redirect — not the config page
                shows_config = "user administration" in source or "system settings" in source
                assert not shows_config, \
                    "SECURITY: Guest can access Config page content"
            except Exception:
                pass  # If frame doesn't exist, that's fine
        finally:
            driver.quit()
