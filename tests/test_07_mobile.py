"""
Test 07: Mobile view module.

Tests the mobile interface, map loading, and AJAX endpoints
used by the mobile view.
"""
import time
import pytest

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class TestMobile:
    """Test the Mobile module."""

    @pytest.fixture(autouse=True)
    def _setup(self, nav, error_log):
        nav.close_popups()
        error_log.mark_position()
        yield
        nav.close_popups()
        nav.to_default()

    def test_mobile_page_loads(self, nav, error_log):
        """Mobile page should load without PHP errors."""
        error_log.mark_position()
        nav.click_tab("term")
        nav.wait_for_main_load(3)

        page_errors = nav.get_main_errors()
        php_errors = error_log.get_php_errors()

        all_errors = page_errors + php_errors
        assert not all_errors, \
            f"Mobile page errors:\n" + "\n".join(str(e)[:200] for e in all_errors)

    def test_mobile_has_incident_list(self, nav):
        """Mobile view should display an incident list or empty state."""
        nav.click_tab("term")
        nav.wait_for_main_load(3)

        text = nav.get_visible_text()
        has_content = len(text.strip()) > 10
        assert has_content, "Mobile page appears empty"

    def test_mobile_map_popup_tiles(self, nav, base_url, logged_in_browser, error_log):
        """Map popup from mobile should load tiles on first open."""
        error_log.mark_position()

        # Open map popup directly
        logged_in_browser.execute_script(
            f"window.open('{base_url}map_popup.php?id=5', "
            "'mobile_map_test', 'width=800,height=600');"
        )
        time.sleep(5)  # Allow all three invalidateSize passes

        handles = logged_in_browser.window_handles
        if len(handles) > 1:
            logged_in_browser.switch_to.window(handles[-1])

            # Count loaded tiles
            tiles = logged_in_browser.find_elements(
                By.CSS_SELECTOR, ".leaflet-tile-loaded"
            )

            # Also check for high-res tiles (zoom level appropriate)
            tile_count = len(tiles)

            # Check for PHP errors in popup
            source = (logged_in_browser.page_source or "").lower()
            has_php_error = "fatal error" in source or "parse error" in source

            logged_in_browser.close()
            logged_in_browser.switch_to.window(handles[0])
            logged_in_browser.switch_to.default_content()

            assert not has_php_error, "Map popup has PHP errors"
            assert tile_count >= 4, \
                f"Map popup only loaded {tile_count} tiles — " \
                f"expected at least 4 for a usable map"
        else:
            pytest.skip("Map popup did not open")
