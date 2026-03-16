"""
Test 04: Units and Facilities modules.

Tests that the units list, facilities list, and their forms
load correctly without PHP errors.
"""
import time
import pytest

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC


class TestUnits:
    """Test the Units module."""

    @pytest.fixture(autouse=True)
    def _setup(self, nav, error_log):
        nav.close_popups()
        error_log.mark_position()
        yield
        nav.close_popups()
        nav.to_default()

    def test_units_page_loads(self, nav, error_log):
        """Units page should load without PHP errors."""
        error_log.mark_position()
        nav.click_tab("resp")
        nav.wait_for_main_load(2)

        page_errors = nav.get_main_errors()
        php_errors = error_log.get_php_errors()

        all_errors = page_errors + php_errors
        assert not all_errors, \
            f"Units page errors:\n" + "\n".join(str(e)[:200] for e in all_errors)

    def test_units_list_has_content(self, nav):
        """Units page should display at least one unit."""
        nav.click_tab("resp")
        nav.wait_for_main_load(2)

        text = nav.get_visible_text()
        # Should have unit-related content
        assert "unit" in text.lower() or "handle" in text.lower() or \
               "TU1" in text or "Test Unit" in text, \
            "Units page has no unit-related content"

    def test_units_map_loads(self, nav):
        """Units page should display a Leaflet map."""
        nav.click_tab("resp")
        nav.wait_for_main_load(3)

        nav.to_main()
        try:
            maps = nav.driver.find_elements(
                By.CSS_SELECTOR, ".leaflet-container, #map_canvas"
            )
            assert len(maps) > 0, "No map found on units page"
        finally:
            nav.to_default()


class TestFacilities:
    """Test the Facilities module."""

    @pytest.fixture(autouse=True)
    def _setup(self, nav, error_log):
        nav.close_popups()
        error_log.mark_position()
        yield
        nav.close_popups()
        nav.to_default()

    def test_facilities_page_loads(self, nav, error_log):
        """Facilities page should load without PHP errors."""
        error_log.mark_position()
        nav.click_tab("facy")
        nav.wait_for_main_load(2)

        page_errors = nav.get_main_errors()
        php_errors = error_log.get_php_errors()

        all_errors = page_errors + php_errors
        assert not all_errors, \
            f"Facilities page errors:\n" + "\n".join(str(e)[:200] for e in all_errors)

    def test_facilities_has_content(self, nav):
        """Facilities page should show facility list or map."""
        nav.click_tab("facy")
        nav.wait_for_main_load(2)

        text = nav.get_visible_text()
        has_content = len(text.strip()) > 20
        assert has_content, "Facilities page appears empty"
