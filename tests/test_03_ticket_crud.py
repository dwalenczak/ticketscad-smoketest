"""
Test 03: Ticket CRUD operations.

Tests creating, viewing, editing, and closing tickets.
Validates form fields, required field indicators, and error handling.
"""
import time
import pytest

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC


class TestTicketCreate:
    """Test ticket creation via the New tab."""

    @pytest.fixture(autouse=True)
    def _setup(self, nav, error_log):
        nav.close_popups()
        error_log.mark_position()
        yield
        nav.close_popups()
        nav.to_default()

    def test_new_ticket_form_loads(self, nav):
        """New ticket form should load with all expected sections."""
        nav.click_tab("add")
        nav.wait_for_main_load(2)

        nav.to_main()
        try:
            source = nav.driver.page_source.lower()

            # Key form sections that should be present
            assert "incident basics" in source or "nature" in source, \
                "Incident Basics section not found"
            assert "location" in source or "address" in source, \
                "Location fields not found"

            # Check for the edit form itself
            forms = nav.driver.find_elements(By.TAG_NAME, "form")
            form_names = [f.get_attribute("name") or "" for f in forms]

            assert any("ticket" in n.lower() or "edit" in n.lower() or n == ""
                       for n in form_names), \
                f"No ticket form found. Forms: {form_names}"
        finally:
            nav.to_default()

    def test_new_ticket_form_fields(self, nav):
        """New ticket form should have the key input fields."""
        nav.click_tab("add")
        nav.wait_for_main_load(2)

        nav.to_main()
        try:
            # Look for key fields by name
            expected_fields = [
                "frm_in_types_id", # Nature/Incident Type dropdown
                "frm_severity",    # Priority/Severity dropdown
                "frm_city",        # City
                "frm_state",       # State
            ]

            for field_name in expected_fields:
                elements = nav.driver.find_elements(By.NAME, field_name)
                assert len(elements) > 0, \
                    f"Expected form field '{field_name}' not found"
        finally:
            nav.to_default()

    def test_new_ticket_has_submit_button(self, nav):
        """New ticket form should have a Submit button."""
        nav.click_tab("add")
        nav.wait_for_main_load(2)

        nav.to_main()
        try:
            # Look for submit-type elements
            buttons = nav.driver.find_elements(
                By.CSS_SELECTOR,
                "input[type='submit'], button[type='submit'], "
                "img[onclick*='submit'], span[onclick*='submit'], "
                "a[onclick*='submit'], td[onclick*='submit']"
            )
            # Also look for text "Submit"
            all_clickables = nav.driver.find_elements(
                By.XPATH,
                "//*[contains(text(), 'Submit')]"
            )
            assert len(buttons) > 0 or len(all_clickables) > 0, \
                "No Submit button found on new ticket form"
        finally:
            nav.to_default()

    def test_new_ticket_nature_dropdown_populated(self, nav):
        """Nature dropdown should have at least one option beyond default."""
        nav.click_tab("add")
        nav.wait_for_main_load(2)

        nav.to_main()
        try:
            nature_el = nav.driver.find_elements(By.NAME, "frm_in_types_id")
            if nature_el:
                select = Select(nature_el[0])
                options = select.options
                # Should have more than just a blank/default option
                assert len(options) >= 2, \
                    f"Nature dropdown has only {len(options)} option(s) — " \
                    f"need at least one call nature configured"
        finally:
            nav.to_default()

    def test_new_ticket_no_php_errors(self, nav, error_log):
        """Loading the new ticket form should produce no PHP errors."""
        error_log.mark_position()

        nav.click_tab("add")
        nav.wait_for_main_load(2)

        page_errors = nav.get_main_errors()
        php_errors = error_log.get_php_errors()

        all_errors = page_errors + php_errors
        assert not all_errors, \
            f"PHP errors on new ticket form:\n" + "\n".join(str(e)[:200] for e in all_errors)

    def test_new_ticket_map_loads(self, nav):
        """New ticket form should display a Leaflet map."""
        nav.click_tab("add")
        nav.wait_for_main_load(3)

        nav.to_main()
        try:
            # Look for Leaflet map container
            map_containers = nav.driver.find_elements(
                By.CSS_SELECTOR, ".leaflet-container, #map_canvas, #map"
            )
            assert len(map_containers) > 0, \
                "No Leaflet map container found on new ticket form"

            # Check that map tiles loaded
            tiles = nav.driver.find_elements(
                By.CSS_SELECTOR, ".leaflet-tile-loaded"
            )
            # Allow a moment for tiles to load
            if not tiles:
                time.sleep(2)
                tiles = nav.driver.find_elements(
                    By.CSS_SELECTOR, ".leaflet-tile-loaded"
                )

            assert len(tiles) > 0, \
                "Map tiles did not load on new ticket form"
        finally:
            nav.to_default()


class TestTicketEdit:
    """Test editing existing tickets."""

    @pytest.fixture(autouse=True)
    def _setup(self, nav, error_log):
        nav.close_popups()
        error_log.mark_position()
        yield
        nav.close_popups()
        nav.to_default()

    def test_edit_ticket_loads(self, nav, base_url):
        """Editing an existing ticket should load without errors."""
        # Navigate directly to edit.php for ticket 5 (our test ticket)
        nav.to_main()
        try:
            nav.driver.execute_script(
                f"window.location.href = '{base_url}edit.php?ticket_id=5';"
            )
        finally:
            nav.to_default()

        nav.wait_for_main_load(3)

        page_errors = nav.get_main_errors()
        assert not page_errors, \
            f"Errors loading edit ticket:\n" + "\n".join(str(e)[:200] for e in page_errors)

    def test_edit_ticket_has_toolbar(self, nav, base_url):
        """Edit ticket should show the action toolbar (Popup, +Action, etc)."""
        nav.to_main()
        try:
            nav.driver.execute_script(
                f"window.location.href = '{base_url}edit.php?ticket_id=5';"
            )
        finally:
            nav.to_default()

        nav.wait_for_main_load(3)

        nav.to_main()
        try:
            source = nav.driver.page_source
            # Look for toolbar items
            toolbar_items = ["Popup", "Action", "Patient", "Notify",
                             "Print", "E-mail", "Dispatch"]
            found = [item for item in toolbar_items if item in source]
            assert len(found) >= 3, \
                f"Edit toolbar incomplete. Found: {found}"
        finally:
            nav.to_default()


class TestTicketPopup:
    """Test the ticket popup window."""

    @pytest.fixture(autouse=True)
    def _setup(self, nav, error_log):
        nav.close_popups()
        error_log.mark_position()
        yield
        nav.close_popups()
        nav.to_default()

    def test_popup_ticket_loads(self, nav, base_url, logged_in_browser):
        """Popup window for a ticket should load without errors."""
        # Open popup via direct URL
        logged_in_browser.execute_script(
            f"window.open('{base_url}map_popup.php?id=5', "
            "'popup_test', 'width=900,height=600');"
        )
        time.sleep(3)

        # Switch to popup
        handles = logged_in_browser.window_handles
        if len(handles) > 1:
            logged_in_browser.switch_to.window(handles[-1])

            source = (logged_in_browser.page_source or "").lower()
            error_markers = ["fatal error", "parse error",
                             "call to undefined function"]
            found_errors = [m for m in error_markers if m in source]

            logged_in_browser.close()
            logged_in_browser.switch_to.window(handles[0])

            assert not found_errors, \
                f"Popup had errors: {found_errors}"
        else:
            pytest.skip("Popup window did not open")

    def test_popup_map_has_tiles(self, nav, base_url, logged_in_browser):
        """Popup map should load tiles without needing F5 refresh."""
        logged_in_browser.execute_script(
            f"window.open('{base_url}map_popup.php?id=5', "
            "'map_test', 'width=900,height=600');"
        )
        time.sleep(4)  # Allow time for multi-pass tile fix

        handles = logged_in_browser.window_handles
        if len(handles) > 1:
            logged_in_browser.switch_to.window(handles[-1])

            tiles = logged_in_browser.find_elements(
                By.CSS_SELECTOR, ".leaflet-tile-loaded"
            )

            tile_count = len(tiles)
            logged_in_browser.close()
            logged_in_browser.switch_to.window(handles[0])

            assert tile_count > 0, \
                f"Map popup loaded 0 tiles — tiles not rendering on first load"
        else:
            pytest.skip("Popup window did not open")
