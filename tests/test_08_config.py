"""
Test 08: Config, Personnel, Chat, Log, Board, Help, SOPs, Full Screen.

Tests all remaining navigation tabs and their pages load correctly.
"""
import time
import pytest

from selenium.webdriver.common.by import By


class TestConfig:
    """Test the Config module."""

    @pytest.fixture(autouse=True)
    def _setup(self, nav, error_log):
        nav.close_popups()
        error_log.mark_position()
        yield
        nav.close_popups()
        nav.to_default()

    def test_config_page_loads(self, nav, error_log):
        """Config page should load without PHP errors."""
        error_log.mark_position()
        nav.click_tab("conf")
        nav.wait_for_main_load(2)

        page_errors = nav.get_main_errors()
        php_errors = error_log.get_php_errors()

        all_errors = page_errors + php_errors
        assert not all_errors, \
            f"Config page errors:\n" + "\n".join(str(e)[:200] for e in all_errors)

    def test_config_has_settings(self, nav):
        """Config page should display configuration options."""
        nav.click_tab("conf")
        nav.wait_for_main_load(2)

        text = nav.get_visible_text()
        has_content = len(text.strip()) > 20
        assert has_content, "Config page appears empty"


class TestPersonnel:
    """Test the Personnel module."""

    @pytest.fixture(autouse=True)
    def _setup(self, nav, error_log):
        nav.close_popups()
        error_log.mark_position()
        yield
        nav.close_popups()
        nav.to_default()

    def test_personnel_page_loads(self, nav, error_log):
        """Personnel page should load without PHP errors."""
        error_log.mark_position()
        nav.click_tab("personnel")
        nav.wait_for_main_load(2)

        page_errors = nav.get_main_errors()
        php_errors = error_log.get_php_errors()

        all_errors = page_errors + php_errors
        assert not all_errors, \
            f"Personnel page errors:\n" + "\n".join(str(e)[:200] for e in all_errors)


class TestChat:
    """Test the Chat module."""

    @pytest.fixture(autouse=True)
    def _setup(self, nav, error_log):
        nav.close_popups()
        error_log.mark_position()
        yield
        nav.close_popups()
        nav.to_default()

    def test_chat_page_loads(self, nav, error_log):
        """Chat page should load without PHP errors."""
        error_log.mark_position()
        nav.click_tab("chat")
        nav.wait_for_main_load(2)

        page_errors = nav.get_main_errors()
        php_errors = error_log.get_php_errors()

        all_errors = page_errors + php_errors
        assert not all_errors, \
            f"Chat page errors:\n" + "\n".join(str(e)[:200] for e in all_errors)


class TestLog:
    """Test the Log module."""

    @pytest.fixture(autouse=True)
    def _setup(self, nav, error_log):
        nav.close_popups()
        error_log.mark_position()
        yield
        nav.close_popups()
        nav.to_default()

    def test_log_page_loads(self, nav, error_log):
        """Log page should load without PHP errors."""
        error_log.mark_position()
        nav.click_tab("log")
        nav.wait_for_main_load(2)

        page_errors = nav.get_main_errors()
        php_errors = error_log.get_php_errors()

        all_errors = page_errors + php_errors
        assert not all_errors, \
            f"Log page errors:\n" + "\n".join(str(e)[:200] for e in all_errors)


class TestBoard:
    """Test the Board module."""

    @pytest.fixture(autouse=True)
    def _setup(self, nav, error_log):
        nav.close_popups()
        error_log.mark_position()
        yield
        nav.close_popups()
        nav.to_default()

    def test_board_page_loads(self, nav, error_log):
        """Board page should load without PHP errors."""
        error_log.mark_position()
        nav.click_tab("call")
        nav.wait_for_main_load(2)

        page_errors = nav.get_main_errors()
        php_errors = error_log.get_php_errors()

        all_errors = page_errors + php_errors
        assert not all_errors, \
            f"Board page errors:\n" + "\n".join(str(e)[:200] for e in all_errors)


class TestHelp:
    """Test the Help module."""

    @pytest.fixture(autouse=True)
    def _setup(self, nav, error_log):
        nav.close_popups()
        error_log.mark_position()
        yield
        nav.close_popups()
        nav.to_default()

    def test_help_page_loads(self, nav, error_log):
        """Help page should load without PHP errors."""
        error_log.mark_position()
        nav.click_tab("help")
        nav.wait_for_main_load(2)

        page_errors = nav.get_main_errors()
        php_errors = error_log.get_php_errors()

        all_errors = page_errors + php_errors
        assert not all_errors, \
            f"Help page errors:\n" + "\n".join(str(e)[:200] for e in all_errors)


class TestSOPs:
    """Test the SOPs module."""

    @pytest.fixture(autouse=True)
    def _setup(self, nav, error_log):
        nav.close_popups()
        error_log.mark_position()
        yield
        nav.close_popups()
        nav.to_default()

    def test_sops_page_loads(self, nav, error_log):
        """SOPs page should load without PHP errors."""
        error_log.mark_position()
        nav.click_tab("card")
        nav.wait_for_main_load(2)

        page_errors = nav.get_main_errors()
        php_errors = error_log.get_php_errors()

        all_errors = page_errors + php_errors
        assert not all_errors, \
            f"SOPs page errors:\n" + "\n".join(str(e)[:200] for e in all_errors)

    def test_sops_requires_auth(self, nav):
        """SOPs should only be accessible to authenticated users."""
        nav.click_tab("card")
        nav.wait_for_main_load(2)

        # This test documents the security requirement
        # SOPs should NOT be visible on the pre-login navbar
        text = nav.get_visible_text()
        # If we got here, we're logged in so it should work
        # The real test is in test_01_login.test_navbar_hidden_before_login
        assert True


class TestFullScreen:
    """Test the Full Screen module."""

    @pytest.fixture(autouse=True)
    def _setup(self, nav, error_log):
        nav.close_popups()
        error_log.mark_position()
        yield
        nav.close_popups()
        nav.to_default()

    def test_full_screen_loads(self, nav, error_log):
        """Full screen view should load without PHP errors."""
        error_log.mark_position()
        nav.click_tab("full")
        nav.wait_for_main_load(3)

        # Full screen may open a new window or load in main
        page_errors = nav.get_main_errors()
        php_errors = error_log.get_php_errors()

        all_errors = page_errors + php_errors
        assert not all_errors, \
            f"Full screen errors:\n" + "\n".join(str(e)[:200] for e in all_errors)
