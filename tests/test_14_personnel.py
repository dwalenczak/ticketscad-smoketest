"""
Test 14: Personnel module tests.

Tests the member/personnel module including record listing, viewing,
and related sub-modules (equipment, teams, clothing, vehicles, events).
"""
import time
import pytest

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC


class TestPersonnelModule:
    """Test the Personnel (member.php) module."""

    @pytest.fixture(autouse=True)
    def _setup(self, nav, error_log):
        nav.close_popups()
        error_log.mark_position()
        yield
        nav.close_popups()
        nav.to_default()

    @pytest.mark.personnel
    def test_personnel_page_loads(self, nav, error_log):
        """Personnel page should load without PHP errors."""
        error_log.mark_position()
        nav.click_tab("personnel")
        nav.wait_for_main_load(3)

        page_errors = nav.get_main_errors()
        php_errors = error_log.get_php_errors()
        all_errors = page_errors + php_errors
        assert not all_errors, \
            f"Personnel page errors:\n" + "\n".join(str(e)[:200] for e in all_errors)

    @pytest.mark.personnel
    def test_personnel_has_content(self, nav):
        """Personnel page should display member records or an empty state."""
        nav.click_tab("personnel")
        nav.wait_for_main_load(3)

        text = nav.get_visible_text()
        has_content = len(text.strip()) > 20
        assert has_content, "Personnel page appears empty"

    @pytest.mark.personnel
    def test_personnel_has_add_button(self, nav):
        """Personnel page should have an Add/New member button or link."""
        nav.click_tab("personnel")
        nav.wait_for_main_load(3)

        nav.to_main()
        try:
            source = nav.driver.page_source.lower()
            has_add = ("add" in source and ("member" in source or "personnel" in source)) or \
                      "new member" in source or "add new" in source or \
                      "frm_name" in source
            assert has_add, \
                "Personnel page missing Add/New member functionality"
        finally:
            nav.to_default()

    @pytest.mark.personnel
    def test_personnel_direct_url(self, nav, base_url, error_log):
        """member.php loaded directly should work (auth gated)."""
        error_log.mark_position()
        nav.to_main()
        try:
            nav.driver.execute_script(
                f"window.location.href = '{base_url}member.php';"
            )
        finally:
            nav.to_default()

        nav.wait_for_main_load(3)

        page_errors = nav.get_main_errors()
        php_errors = error_log.get_php_errors()
        all_errors = page_errors + php_errors
        assert not all_errors, \
            f"member.php direct load errors:\n" + "\n".join(str(e)[:200] for e in all_errors)


class TestPersonnelTables:
    """Test personnel-related config tables load without errors."""

    @pytest.fixture(autouse=True)
    def _setup(self, nav, error_log):
        nav.close_popups()
        error_log.mark_position()
        yield
        nav.close_popups()
        nav.to_default()

    # Tables under Config that relate to personnel
    PERSONNEL_TABLES = [
        ("member_types", "Member Types"),
        ("member_ranks", "Member Ranks"),
        ("member_status", "Member Status"),
    ]

    @pytest.mark.parametrize("table,label", PERSONNEL_TABLES,
                             ids=[t[0] for t in PERSONNEL_TABLES])
    @pytest.mark.personnel
    @pytest.mark.config
    def test_personnel_table_loads(self, nav, error_log, base_url, table, label):
        """Personnel config table '{table}' should load without errors."""
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


class TestEquipment:
    """Test equipment-related functionality."""

    @pytest.fixture(autouse=True)
    def _setup(self, nav, error_log):
        nav.close_popups()
        error_log.mark_position()
        yield
        nav.close_popups()
        nav.to_default()

    @pytest.mark.personnel
    @pytest.mark.config
    def test_equipment_types_table(self, nav, error_log, base_url):
        """Equipment types config table should load."""
        error_log.mark_position()

        nav.to_main()
        try:
            nav.driver.execute_script(
                f"window.location.href = '{base_url}tables.php?tablename=equipment_types';"
            )
        finally:
            nav.to_default()

        nav.wait_for_main_load(3)

        page_errors = nav.get_main_errors()
        php_errors = error_log.get_php_errors()
        all_errors = page_errors + php_errors
        assert not all_errors, \
            f"Equipment types table errors:\n" + "\n".join(str(e)[:200] for e in all_errors)


class TestVehicles:
    """Test vehicle-related functionality."""

    @pytest.fixture(autouse=True)
    def _setup(self, nav, error_log):
        nav.close_popups()
        error_log.mark_position()
        yield
        nav.close_popups()
        nav.to_default()

    @pytest.mark.personnel
    @pytest.mark.config
    def test_vehicles_table(self, nav, error_log, base_url):
        """Vehicles config table should load."""
        error_log.mark_position()

        nav.to_main()
        try:
            nav.driver.execute_script(
                f"window.location.href = '{base_url}tables.php?tablename=vehicles';"
            )
        finally:
            nav.to_default()

        nav.wait_for_main_load(3)

        page_errors = nav.get_main_errors()
        php_errors = error_log.get_php_errors()
        all_errors = page_errors + php_errors
        assert not all_errors, \
            f"Vehicles table errors:\n" + "\n".join(str(e)[:200] for e in all_errors)


class TestTeams:
    """Test teams functionality."""

    @pytest.fixture(autouse=True)
    def _setup(self, nav, error_log):
        nav.close_popups()
        error_log.mark_position()
        yield
        nav.close_popups()
        nav.to_default()

    @pytest.mark.personnel
    @pytest.mark.config
    def test_teams_table(self, nav, error_log, base_url):
        """Teams config table should load."""
        error_log.mark_position()

        nav.to_main()
        try:
            nav.driver.execute_script(
                f"window.location.href = '{base_url}tables.php?tablename=teams';"
            )
        finally:
            nav.to_default()

        nav.wait_for_main_load(3)

        page_errors = nav.get_main_errors()
        php_errors = error_log.get_php_errors()
        all_errors = page_errors + php_errors
        assert not all_errors, \
            f"Teams table errors:\n" + "\n".join(str(e)[:200] for e in all_errors)
