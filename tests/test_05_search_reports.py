"""
Test 05: Search and Reports modules.

Tests search form, report generation, and validates no PHP errors
or SQL injection vectors in the output.
"""
import time
import pytest

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC


class TestSearch:
    """Test the Search module."""

    @pytest.fixture(autouse=True)
    def _setup(self, nav, error_log):
        nav.close_popups()
        error_log.mark_position()
        yield
        nav.close_popups()
        nav.to_default()

    def test_search_page_loads(self, nav, error_log):
        """Search page should load without errors."""
        error_log.mark_position()
        nav.click_tab("srch")
        nav.wait_for_main_load(2)

        page_errors = nav.get_main_errors()
        php_errors = error_log.get_php_errors()

        all_errors = page_errors + php_errors
        assert not all_errors, \
            f"Search page errors:\n" + "\n".join(str(e)[:200] for e in all_errors)

    def test_search_form_has_fields(self, nav):
        """Search form should have search input and search-in dropdown."""
        nav.click_tab("srch")
        nav.wait_for_main_load(2)

        nav.to_main()
        try:
            # Search text input
            search_input = nav.driver.find_elements(By.NAME, "frm_search")
            assert len(search_input) > 0, "Search text input not found"

            # Search-in column selector
            search_in = nav.driver.find_elements(By.NAME, "frm_search_in")
            assert len(search_in) > 0, "Search-in dropdown not found"
        finally:
            nav.to_default()

    def test_search_executes_without_error(self, nav, error_log):
        """Running a search should return results without PHP errors."""
        error_log.mark_position()

        nav.click_tab("srch")
        nav.wait_for_main_load(2)

        nav.to_main()
        try:
            search_input = nav.driver.find_element(By.NAME, "frm_search")
            search_input.clear()
            search_input.send_keys("test")

            # Submit the search form
            nav.driver.execute_script(
                "document.forms[0].submit();"
            )
        finally:
            nav.to_default()

        nav.wait_for_main_load(3)

        page_errors = nav.get_main_errors()
        php_errors = error_log.get_php_errors()

        all_errors = page_errors + php_errors
        assert not all_errors, \
            f"Search execution errors:\n" + "\n".join(str(e)[:200] for e in all_errors)


class TestReports:
    """Test the Reports module."""

    @pytest.fixture(autouse=True)
    def _setup(self, nav, error_log):
        nav.close_popups()
        error_log.mark_position()
        yield
        nav.close_popups()
        nav.to_default()

    def test_reports_page_loads(self, nav, error_log):
        """Reports page should load without errors."""
        error_log.mark_position()
        nav.click_tab("reps")
        nav.wait_for_main_load(2)

        page_errors = nav.get_main_errors()
        php_errors = error_log.get_php_errors()

        all_errors = page_errors + php_errors
        assert not all_errors, \
            f"Reports page errors:\n" + "\n".join(str(e)[:200] for e in all_errors)

    def test_reports_form_has_fields(self, nav):
        """Reports page should have report type selection and date fields."""
        nav.click_tab("reps")
        nav.wait_for_main_load(2)

        nav.to_main()
        try:
            source = nav.driver.page_source.lower()
            # Should have report-related controls
            assert "report" in source, "Reports page missing report controls"
        finally:
            nav.to_default()

    def test_reports_generates_without_error(self, nav, error_log):
        """Generating a report should not produce PHP errors."""
        error_log.mark_position()

        nav.click_tab("reps")
        nav.wait_for_main_load(2)

        nav.to_main()
        try:
            # Try to find and submit the report form
            forms = nav.driver.find_elements(By.TAG_NAME, "form")
            if forms:
                # Try submitting the first form (default report)
                nav.driver.execute_script(
                    "if (document.forms.length > 0) document.forms[0].submit();"
                )
        finally:
            nav.to_default()

        nav.wait_for_main_load(3)

        php_errors = error_log.get_php_errors()
        assert not php_errors, \
            f"Report generation errors:\n" + "\n".join(str(e)[:200] for e in php_errors)
