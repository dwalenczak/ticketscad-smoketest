"""
Test 02: Top navigation tabs.

Tests that every navigation tab loads its target page without
PHP errors, server errors, or blank pages.
"""
import re
import time
import pytest

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# All known top nav tabs with their expected targets
# Tab IDs match the SPAN IDs in top.php
# Format: (span_id, display_text, target_php_file_or_None)
NAV_TABS = [
    ("main", "Situation", "main.php"),
    ("add", "New", "add.php"),
    ("resp", "Units", "units.php"),
    ("facy", "Fac's", "facilities.php"),
    ("srch", "Search", "search.php"),
    ("reps", "Reports", "reports.php"),
    ("conf", "Config", "config.php"),
    ("help", "Help", "help.php"),
    ("full", "Full scr", None),       # opens via do_full_scr() JS
    ("personnel", "Personnel", "member.php"),
    ("links", "Links", None),         # inline panel toggle
    ("term", "Mobile", "mobile.php"),
]

# Tabs that require non-guest AND specific settings enabled:
# "card" (SOP's) - requires $card_addr set
# "chat" - requires chat_time != 0
# "log" - requires non-guest
# "call" (Board) - requires call_board == 1
# "msg" (Msgs) - requires use_messaging enabled
# "reqs" (Requests) - requires non-guest
# "ics" (ICS-FORMS) - requires ics_top == 1


class TestNavigation:
    """Test all top navigation tabs load without errors."""

    @pytest.fixture(autouse=True)
    def _setup(self, nav, error_log):
        """Reset to situation screen before each tab test."""
        nav.close_popups()
        nav.to_default()
        error_log.mark_position()
        yield
        nav.close_popups()
        nav.to_default()

    @pytest.mark.parametrize("tab_id,tab_name,expected_target", NAV_TABS)
    def test_tab_loads(self, nav, error_log, tab_id, tab_name, expected_target):
        """Tab '{tab_name}' loads without PHP errors."""
        # First go to Situation to have a clean baseline
        nav.click_tab("main")
        nav.wait_for_main_load(1.5)

        before_src = nav.main_frame_src()

        # Click the target tab
        nav.click_tab(tab_id)
        nav.wait_for_main_load(2.0)

        # Handle Links tab (inline panel, not a page load)
        if expected_target is None:
            return  # Links just toggles a panel

        # Check for PHP errors in the loaded page
        errors = nav.get_main_errors()
        php_log_errors = error_log.get_php_errors()

        # Build a detailed error message if needed
        all_errors = []
        if errors:
            all_errors.extend([f"PAGE: {e[:200]}" for e in errors])
        if php_log_errors:
            all_errors.extend([f"LOG: {e[:200]}" for e in php_log_errors])

        assert not all_errors, \
            f"Tab '{tab_name}' produced errors:\n" + "\n".join(all_errors)

        # Verify the page actually loaded something
        after_src = nav.main_frame_src()
        visible_text = nav.get_visible_text()

        # The page should have either changed the frame src or have content
        page_changed = after_src != before_src
        has_content = len(visible_text.strip()) > 10

        assert page_changed or has_content, \
            f"Tab '{tab_name}' did not load any visible content"

    def test_all_tabs_present(self, nav):
        """Verify all expected navigation tabs exist in the upper frame."""
        nav.to_upper()
        try:
            tabs = nav.driver.find_elements(
                By.CSS_SELECTOR, "td[colspan='99'] span[id][onclick]"
            )
            tab_ids = set()
            for tab in tabs:
                tid = (tab.get_attribute("id") or "").strip()
                if tid:
                    tab_ids.add(tid)

            expected_ids = {t[0] for t in NAV_TABS}
            missing = expected_ids - tab_ids
            if missing:
                pytest.fail(f"Missing navigation tabs: {missing}")
        finally:
            nav.to_default()
