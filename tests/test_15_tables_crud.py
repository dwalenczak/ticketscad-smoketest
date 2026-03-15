"""
Test 15: Tables CRUD — verify all config tables load and render.

Uses the tables.php endpoint with different tablename parameters to
ensure each configuration table can be listed without PHP errors.
This catches missing columns, bad queries, and broken table definitions.
"""
import time
import pytest

from selenium.webdriver.common.by import By


class TestTablesLoad:
    """Verify every config table loads without errors via tables.php."""

    @pytest.fixture(autouse=True)
    def _setup(self, nav, error_log):
        nav.close_popups()
        error_log.mark_position()
        yield
        nav.close_popups()
        nav.to_default()

    # All known tables managed via tables.php
    # (tablename parameter -> human label)
    CONFIG_TABLES = [
        "in_types",          # Call Natures / Incident Types
        "severity",          # Severity levels
        "status",            # Status codes
        "disposition",       # Disposition codes
        "organizations",     # Organizations
        "regions",           # Regions
        "facilities",        # Facilities
        "unit_types",        # Unit Types
        "responder",         # Responders/Units
        "member_types",      # Member Types
        "member_ranks",      # Member Ranks
        "member_status",     # Member Status
        "equipment_types",   # Equipment Types
        "vehicles",          # Vehicles
        "teams",             # Teams
        "clothing",          # Clothing Types
        "insurance",         # Insurance Types
        "action_codes",      # Action Codes
        "log_codes",         # Log Codes
    ]

    @pytest.mark.parametrize("table", CONFIG_TABLES)
    @pytest.mark.config
    def test_table_loads(self, nav, error_log, base_url, table):
        """Config table '{table}' should load without PHP errors."""
        error_log.mark_position()

        nav.to_main()
        try:
            nav.driver.execute_script(
                f"window.location.href = '{base_url}tables.php?tablename={table}';"
            )
        finally:
            nav.to_default()

        nav.wait_for_main_load(3)

        page_errors = nav.get_main_errors()
        php_errors = error_log.get_php_errors()
        all_errors = page_errors + php_errors
        assert not all_errors, \
            f"Table '{table}' errors:\n" + "\n".join(str(e)[:200] for e in all_errors)

    @pytest.mark.config
    def test_tables_default_page(self, nav, error_log, base_url):
        """tables.php with no parameters should load a default view."""
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
            f"Default tables page errors:\n" + "\n".join(str(e)[:200] for e in all_errors)
