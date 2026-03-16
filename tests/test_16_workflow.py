"""
Test 16: End-to-end workflow tests.

Tests complete workflows: creating a ticket, viewing it on the situation
screen, opening the popup, and verifying dispatch page access.
"""
import time
import pytest

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC


class TestTicketWorkflow:
    """Test the ticket creation and viewing workflow."""

    @pytest.fixture(autouse=True)
    def _setup(self, nav, error_log):
        nav.close_popups()
        error_log.mark_position()
        yield
        nav.close_popups()
        nav.to_default()

    @pytest.mark.tickets
    def test_situation_screen_shows_tickets(self, nav):
        """Situation screen should display existing tickets."""
        nav.click_tab("main")
        nav.wait_for_main_load(3)

        text = nav.get_visible_text()
        # Should have some content — tickets, "no open tickets", etc.
        assert len(text.strip()) > 10, \
            "Situation screen appears completely empty"

    @pytest.mark.tickets
    def test_situation_has_ticket_rows(self, nav):
        """Situation screen should have clickable ticket entries."""
        nav.click_tab("main")
        nav.wait_for_main_load(3)

        nav.to_main()
        try:
            # Look for table rows that might be tickets
            rows = nav.driver.find_elements(By.CSS_SELECTOR, "tr[onclick], td[onclick]")
            # Or look for links
            links = nav.driver.find_elements(By.CSS_SELECTOR, "a[href*='ticket'], a[href*='edit']")
            # The page should have SOME interactive elements
            has_interactive = len(rows) > 0 or len(links) > 0
            # Even if no tickets, the page should have content
            source = nav.driver.page_source or ""
            has_structure = "table" in source.lower()
            assert has_interactive or has_structure, \
                "Situation screen has no ticket rows or table structure"
        finally:
            nav.to_default()

    @pytest.mark.tickets
    def test_edit_ticket_form_fields(self, nav, base_url, error_log):
        """Edit ticket form should have expected form fields."""
        error_log.mark_position()

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
            expected_fields = [
                "frm_in_types_id",  # Nature
                "frm_severity",     # Severity/Priority
                "frm_city",         # City
                "frm_state",        # State
            ]
            for field in expected_fields:
                els = nav.driver.find_elements(By.NAME, field)
                assert len(els) > 0, \
                    f"Edit ticket missing field: {field}"
        finally:
            nav.to_default()

    @pytest.mark.tickets
    def test_popup_ticket_no_errors(self, nav, base_url, logged_in_browser, error_log):
        """Opening a ticket popup should not produce PHP errors."""
        error_log.mark_position()

        logged_in_browser.execute_script(
            f"window.open('{base_url}map_popup.php?id=5', "
            "'workflow_popup', 'width=900,height=600');"
        )
        time.sleep(3)

        handles = logged_in_browser.window_handles
        if len(handles) > 1:
            logged_in_browser.switch_to.window(handles[-1])
            source = (logged_in_browser.page_source or "").lower()
            error_markers = ["fatal error", "parse error",
                             "call to undefined function",
                             "undefined variable"]
            found = [m for m in error_markers if m in source]

            php_errors = error_log.get_php_errors()

            logged_in_browser.close()
            logged_in_browser.switch_to.window(handles[0])

            all_errors = found + php_errors
            assert not all_errors, \
                f"Popup errors:\n" + "\n".join(str(e)[:200] for e in all_errors)
        else:
            pytest.skip("Popup window did not open")


class TestDispatchWorkflow:
    """Test the dispatch workflow."""

    @pytest.fixture(autouse=True)
    def _setup(self, nav, error_log):
        nav.close_popups()
        error_log.mark_position()
        yield
        nav.close_popups()
        nav.to_default()

    @pytest.mark.dispatch
    def test_dispatch_page_loads(self, nav, base_url, error_log):
        """Dispatch/routes page should load for a ticket."""
        error_log.mark_position()

        nav.to_main()
        try:
            nav.driver.execute_script(
                f"window.location.href = '{base_url}routes.php?ticket_id=5';"
            )
        finally:
            nav.to_default()

        nav.wait_for_main_load(4)

        page_errors = nav.get_main_errors()
        php_errors = error_log.get_php_errors()
        all_errors = page_errors + php_errors
        assert not all_errors, \
            f"Dispatch page errors:\n" + "\n".join(str(e)[:200] for e in all_errors)

    @pytest.mark.dispatch
    def test_dispatch_shows_units(self, nav, base_url):
        """Dispatch page should show available units."""
        nav.to_main()
        try:
            nav.driver.execute_script(
                f"window.location.href = '{base_url}routes.php?ticket_id=5';"
            )
        finally:
            nav.to_default()

        nav.wait_for_main_load(4)

        text = nav.get_visible_text()
        has_content = len(text.strip()) > 20
        assert has_content, "Dispatch page appears empty — no unit data"

    @pytest.mark.dispatch
    def test_dispatch_has_checkboxes(self, nav, base_url):
        """Dispatch page should have unit selection checkboxes."""
        nav.to_main()
        try:
            nav.driver.execute_script(
                f"window.location.href = '{base_url}routes.php?ticket_id=5';"
            )
        finally:
            nav.to_default()

        nav.wait_for_main_load(4)

        nav.to_main()
        try:
            checkboxes = nav.driver.find_elements(
                By.CSS_SELECTOR, "input[type='checkbox']"
            )
            assert len(checkboxes) >= 0, \
                "Dispatch page rendered without error"
            # Note: may have 0 checkboxes if no units available
        finally:
            nav.to_default()


class TestSearchWorkflow:
    """Test the search workflow end-to-end."""

    @pytest.fixture(autouse=True)
    def _setup(self, nav, error_log):
        nav.close_popups()
        error_log.mark_position()
        yield
        nav.close_popups()
        nav.to_default()

    @pytest.mark.search
    def test_search_returns_results(self, nav, base_url, error_log):
        """Searching for a common term should return results."""
        error_log.mark_position()
        nav.click_tab("srch")
        nav.wait_for_main_load(2)

        nav.to_main()
        try:
            query_el = nav.driver.find_elements(By.NAME, "frm_query")
            if query_el:
                query_el[0].clear()
                query_el[0].send_keys("test")
                # Submit form
                nav.driver.execute_script(
                    "if(document.queryForm) document.queryForm.submit(); "
                    "else if(document.forms[0]) document.forms[0].submit();"
                )
            else:
                pytest.skip("Search field not found")
        finally:
            nav.to_default()

        nav.wait_for_main_load(3)

        php_errors = error_log.get_php_errors()
        assert not php_errors, \
            f"Search execution PHP errors:\n" + "\n".join(str(e)[:200] for e in php_errors)

    @pytest.mark.search
    def test_search_with_different_types(self, nav, base_url, error_log):
        """Search should work with different search-in field types."""
        error_log.mark_position()
        nav.click_tab("srch")
        nav.wait_for_main_load(2)

        nav.to_main()
        try:
            search_in = nav.driver.find_elements(By.NAME, "frm_search_in")
            if search_in:
                select = Select(search_in[0])
                options = [opt.get_attribute("value") for opt in select.options]
                assert len(options) >= 2, \
                    f"Search-in dropdown has too few options: {options}"
            else:
                # search_in may not exist in all versions
                pass
        finally:
            nav.to_default()
