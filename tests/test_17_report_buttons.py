"""
Test 17: Report button highlighting.

Verifies that clicking a report button highlights it and that clicking
a different button clears the previous highlight. Regression test for
the irep_but (Incident Report) sticky highlight bug.
"""
import time
import pytest

from selenium.webdriver.common.by import By


# All report button IDs and their display labels
REPORT_BUTTONS = [
    ("ulog_but", "Unit Log"),
    ("comms_but", "Comms report"),
    ("flog_but", "Facility Log"),
    ("dlog_but", "Dispatch Log"),
    ("slog_but", "Station Log"),
    ("ilog_but", "Incident Summary"),
    ("irep_but", "Incident Report"),
    ("alog_but", "After-action Report"),
    ("mlog_but", "Incident mgmt Report"),
    ("billreport_but", "Organisation Billing Report"),
    ("region_but", "Region Report"),
]


class TestReportButtonHighlight:
    """Test that report buttons highlight correctly and exclusively."""

    @pytest.fixture(autouse=True)
    def _setup(self, nav, error_log):
        nav.close_popups()
        error_log.mark_position()
        yield
        nav.close_popups()
        nav.to_default()

    @pytest.mark.reports
    def test_reports_page_has_all_buttons(self, nav):
        """Reports page should have all expected report buttons."""
        nav.click_tab("reps")
        nav.wait_for_main_load(2)

        nav.to_main()
        try:
            missing = []
            for btn_id, label in REPORT_BUTTONS:
                els = nav.driver.find_elements(By.ID, btn_id)
                if not els:
                    missing.append(f"{btn_id} ({label})")
            assert not missing, \
                f"Reports page missing buttons: {missing}"
        finally:
            nav.to_default()

    @pytest.mark.reports
    def test_clicking_button_highlights_it(self, nav):
        """Clicking a report button should give it the signal_b class."""
        nav.click_tab("reps")
        nav.wait_for_main_load(2)

        nav.to_main()
        try:
            btn = nav.driver.find_element(By.ID, "ulog_but")
            btn.click()
            time.sleep(0.5)

            css_class = btn.get_attribute("class") or ""
            assert "signal_b" in css_class, \
                f"Clicked button should have signal_b class, got: '{css_class}'"
        finally:
            nav.to_default()

    @pytest.mark.reports
    @pytest.mark.parametrize("btn_id,label", REPORT_BUTTONS,
                             ids=[b[0] for b in REPORT_BUTTONS])
    def test_button_clears_on_other_click(self, nav, btn_id, label):
        """Clicking '{label}' then another button should clear '{label}' highlight.

        Regression test: irep_but (Incident Report) was missing from
        the unLit() function and stayed highlighted after selecting
        a different report type.
        """
        nav.click_tab("reps")
        nav.wait_for_main_load(2)

        nav.to_main()
        try:
            # Step 1: Click the target button
            target = nav.driver.find_elements(By.ID, btn_id)
            if not target or not target[0].is_displayed():
                pytest.skip(f"Button {btn_id} not visible")

            target[0].click()
            time.sleep(0.3)

            # Verify it's highlighted
            css_after_click = target[0].get_attribute("class") or ""
            assert "signal_b" in css_after_click, \
                f"Button {btn_id} not highlighted after click: '{css_after_click}'"

            # Step 2: Click a different button
            # Pick the first button that isn't the target
            other_id = "ulog_but" if btn_id != "ulog_but" else "comms_but"
            other = nav.driver.find_element(By.ID, other_id)
            other.click()
            time.sleep(0.3)

            # Step 3: Verify the original button is no longer highlighted
            css_after_other = target[0].get_attribute("class") or ""
            assert "signal_b" not in css_after_other, \
                f"REGRESSION: {btn_id} ({label}) stays highlighted " \
                f"after clicking {other_id}. Class: '{css_after_other}'"

            # Also verify the other button IS highlighted
            other_class = other.get_attribute("class") or ""
            assert "signal_b" in other_class, \
                f"The newly clicked button {other_id} should be highlighted"

        finally:
            nav.to_default()

    @pytest.mark.reports
    def test_only_one_button_highlighted_at_a_time(self, nav):
        """After clicking through all buttons, only the last should be highlighted."""
        nav.click_tab("reps")
        nav.wait_for_main_load(2)

        nav.to_main()
        try:
            # Click through all visible buttons
            visible_buttons = []
            for btn_id, label in REPORT_BUTTONS:
                els = nav.driver.find_elements(By.ID, btn_id)
                if els and els[0].is_displayed():
                    visible_buttons.append((btn_id, els[0]))

            if len(visible_buttons) < 2:
                pytest.skip("Need at least 2 visible buttons")

            # Click the last visible button
            last_id, last_el = visible_buttons[-1]
            last_el.click()
            time.sleep(0.3)

            # Check all buttons: only last should be highlighted
            highlighted = []
            for btn_id, btn_el in visible_buttons:
                css = btn_el.get_attribute("class") or ""
                if "signal_b" in css:
                    highlighted.append(btn_id)

            assert highlighted == [last_id], \
                f"Expected only {last_id} highlighted, but found: {highlighted}"

        finally:
            nav.to_default()
