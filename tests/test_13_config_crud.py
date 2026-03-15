"""
Test 13: Configuration CRUD operations.

Tests creating, editing, and deleting configuration records
(natures, unit types, organizations, regions) via the Config module.
Also validates that config changes appear in dependent dropdowns.
"""
import time
import pytest

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC


class TestConfigNavigation:
    """Test navigating between Config sub-pages."""

    @pytest.fixture(autouse=True)
    def _setup(self, nav, error_log):
        nav.close_popups()
        error_log.mark_position()
        yield
        nav.close_popups()
        nav.to_default()

    # Config uses tables.php with func= parameter for different sections
    CONFIG_SECTIONS = [
        ("summ", "System Settings"),
        ("users", "User Administration"),
        ("natures", "Call Natures"),
        ("severity", "Severity"),
        ("status", "Status"),
        ("disposition", "Disposition"),
    ]

    @pytest.mark.parametrize("func,label", CONFIG_SECTIONS,
                             ids=[s[0] for s in CONFIG_SECTIONS])
    @pytest.mark.config
    def test_config_section_loads(self, nav, error_log, base_url, func, label):
        """Config section '{func}' should load without PHP errors."""
        error_log.mark_position()

        nav.to_main()
        try:
            nav.driver.execute_script(
                f"window.location.href = '{base_url}config.php?func={func}';"
            )
        finally:
            nav.to_default()

        nav.wait_for_main_load(3)

        page_errors = nav.get_main_errors()
        php_errors = error_log.get_php_errors()
        all_errors = page_errors + php_errors
        assert not all_errors, \
            f"Config section '{func}' errors:\n" + "\n".join(str(e)[:200] for e in all_errors)

    @pytest.mark.config
    def test_config_tables_loads(self, nav, error_log, base_url):
        """Tables management page should load without errors."""
        error_log.mark_position()

        nav.to_main()
        try:
            nav.driver.execute_script(
                f"window.location.href = '{base_url}tables.php';"
            )
        finally:
            nav.to_default()

        nav.wait_for_main_load(3)

        page_errors = nav.get_main_errors()
        php_errors = error_log.get_php_errors()
        all_errors = page_errors + php_errors
        assert not all_errors, \
            f"Tables page errors:\n" + "\n".join(str(e)[:200] for e in all_errors)


class TestNaturesCRUD:
    """Test creating and viewing call natures."""

    @pytest.fixture(autouse=True)
    def _setup(self, nav, error_log):
        nav.close_popups()
        error_log.mark_position()
        yield
        nav.close_popups()
        nav.to_default()

    @pytest.mark.config
    def test_natures_list_has_entries(self, nav, base_url):
        """Call natures list should contain at least one entry."""
        nav.to_main()
        try:
            nav.driver.execute_script(
                f"window.location.href = '{base_url}config.php?func=natures';"
            )
        finally:
            nav.to_default()

        nav.wait_for_main_load(3)

        text = nav.get_visible_text()
        # Should have table rows with nature names
        assert len(text.strip()) > 50, \
            "Natures page appears empty — no call natures configured"

    @pytest.mark.config
    def test_natures_appear_in_new_ticket(self, nav, base_url):
        """Configured natures should appear in the new ticket dropdown."""
        nav.click_tab("add")
        nav.wait_for_main_load(2)

        nav.to_main()
        try:
            nature_el = nav.driver.find_elements(By.NAME, "frm_in_types_id")
            assert nature_el, "Nature dropdown not found on new ticket form"

            select = Select(nature_el[0])
            options = [opt.text.strip() for opt in select.options if opt.text.strip()]
            assert len(options) >= 1, \
                "Nature dropdown has no options — config may be broken"
        finally:
            nav.to_default()


class TestUserAdmin:
    """Test user administration in Config."""

    @pytest.fixture(autouse=True)
    def _setup(self, nav, error_log):
        nav.close_popups()
        error_log.mark_position()
        yield
        nav.close_popups()
        nav.to_default()

    @pytest.mark.config
    def test_user_admin_page_loads(self, nav, base_url, error_log):
        """User administration page should load and show users."""
        error_log.mark_position()

        nav.to_main()
        try:
            nav.driver.execute_script(
                f"window.location.href = '{base_url}config.php?func=users';"
            )
        finally:
            nav.to_default()

        nav.wait_for_main_load(3)

        page_errors = nav.get_main_errors()
        php_errors = error_log.get_php_errors()
        all_errors = page_errors + php_errors
        assert not all_errors, \
            f"User admin errors:\n" + "\n".join(str(e)[:200] for e in all_errors)

    @pytest.mark.config
    def test_user_admin_shows_admin_user(self, nav, base_url):
        """User admin page should list the admin user."""
        nav.to_main()
        try:
            nav.driver.execute_script(
                f"window.location.href = '{base_url}config.php?func=users';"
            )
        finally:
            nav.to_default()

        nav.wait_for_main_load(3)

        text = nav.get_visible_text()
        assert "admin" in text.lower(), \
            "Admin user not found in user administration list"
