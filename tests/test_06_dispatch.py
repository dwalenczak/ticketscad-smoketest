"""
Test 06: Dispatch/Routes module.

Tests dispatch page loading, unit checkbox functionality,
and the dispatch workflow from situation screen.
"""
import time
import pytest

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class TestDispatch:
    """Test the dispatch/routes functionality."""

    @pytest.fixture(autouse=True)
    def _setup(self, nav, error_log):
        nav.close_popups()
        error_log.mark_position()
        yield
        nav.close_popups()
        nav.to_default()

    def test_routes_page_loads(self, nav, base_url, error_log):
        """Routes/dispatch page should load without errors."""
        error_log.mark_position()

        nav.to_main()
        try:
            # Load routes directly for ticket 5
            nav.driver.execute_script(
                f"window.location.href = '{base_url}routes.php?ticket_id=5';"
            )
        finally:
            nav.to_default()

        nav.wait_for_main_load(3)

        page_errors = nav.get_main_errors()
        php_errors = error_log.get_php_errors()

        all_errors = page_errors + php_errors
        assert not all_errors, \
            f"Routes page errors:\n" + "\n".join(str(e)[:200] for e in all_errors)

    def test_routes_shows_units(self, nav, base_url):
        """Routes page should list available units for dispatch."""
        nav.to_main()
        try:
            nav.driver.execute_script(
                f"window.location.href = '{base_url}routes.php?ticket_id=5';"
            )
        finally:
            nav.to_default()

        nav.wait_for_main_load(3)

        text = nav.get_visible_text()
        # Should show unit-related content
        assert "unit" in text.lower() or "handle" in text.lower() or \
               "TU1" in text or "Test Unit" in text or "available" in text.lower(), \
            "Routes page doesn't show any units"

    def test_routes_checkboxes_clickable(self, nav, base_url, logged_in_browser):
        """Unit checkboxes on dispatch page should be clickable for available units."""
        nav.to_main()
        try:
            nav.driver.execute_script(
                f"window.location.href = '{base_url}routes.php?ticket_id=5';"
            )
        finally:
            nav.to_default()

        nav.wait_for_main_load(3)

        nav.to_main()
        try:
            checkboxes = nav.driver.find_elements(
                By.CSS_SELECTOR, "input[type='checkbox']"
            )

            if not checkboxes:
                pytest.skip("No checkboxes found on dispatch page")

            # Find checkboxes that are NOT disabled
            clickable = [
                cb for cb in checkboxes
                if not cb.get_attribute("disabled")
            ]

            # At least some checkboxes should be clickable for available units
            assert len(clickable) > 0, \
                f"All {len(checkboxes)} checkbox(es) are disabled — " \
                f"no units can be dispatched"
        finally:
            nav.to_default()

    def test_routes_map_loads(self, nav, base_url):
        """Routes page should display a map showing the route."""
        nav.to_main()
        try:
            nav.driver.execute_script(
                f"window.location.href = '{base_url}routes.php?ticket_id=5';"
            )
        finally:
            nav.to_default()

        nav.wait_for_main_load(3)

        nav.to_main()
        try:
            maps = nav.driver.find_elements(
                By.CSS_SELECTOR, ".leaflet-container, #map_canvas"
            )
            assert len(maps) > 0, "No map found on routes page"
        finally:
            nav.to_default()

    def test_dispatch_show_messages(self, nav, base_url, error_log):
        """'Show Messages' on dispatch should not produce undefined array key errors."""
        error_log.mark_position()

        nav.to_main()
        try:
            nav.driver.execute_script(
                f"window.location.href = '{base_url}routes.php?ticket_id=5';"
            )
        finally:
            nav.to_default()

        nav.wait_for_main_load(3)

        # Try to click "Show Messages" or similar button
        nav.to_main()
        try:
            msg_links = nav.driver.find_elements(
                By.XPATH,
                "//*[contains(text(), 'Show') and contains(text(), 'Message')]"
            )
            if msg_links:
                msg_links[0].click()
                time.sleep(2)
        finally:
            nav.to_default()

        # Check for the specific error reported: "Undefined array key 0"
        php_errors = error_log.get_php_errors()
        array_key_errors = [e for e in php_errors if "undefined array key" in e.lower()]
        assert not array_key_errors, \
            f"'Show Messages' triggered undefined array key error:\n" + \
            "\n".join(str(e)[:200] for e in array_key_errors)
