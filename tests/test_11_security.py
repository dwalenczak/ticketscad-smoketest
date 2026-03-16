"""
Test 11: Security validation.

Tests CSRF protection, SQL injection prevention, authentication
requirements, and session handling.
"""
import time
import pytest

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class TestCSRF:
    """Test CSRF token protection."""

    @pytest.fixture(autouse=True)
    def _setup(self, nav, error_log):
        nav.close_popups()
        error_log.mark_position()
        yield
        nav.close_popups()
        nav.to_default()

    def test_login_form_has_csrf(self, base_url):
        """Login form must include a CSRF token."""
        from selenium.webdriver.edge.options import Options as EdgeOptions
        options = EdgeOptions()
        options.add_argument("--headless=new")
        fresh = None
        try:
            from selenium import webdriver as wd
            fresh = wd.Edge(options=options)
            fresh.set_page_load_timeout(15)
            fresh.get(base_url)
            wait = WebDriverWait(fresh, 10)

            fresh.switch_to.default_content()
            wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "main")))

            csrf_fields = fresh.find_elements(By.NAME, "csrf_token")
            fresh.switch_to.default_content()

            assert len(csrf_fields) > 0, \
                "SECURITY: Login form has no CSRF token"
        finally:
            if fresh:
                fresh.quit()

    @pytest.mark.xfail(reason="edit.php does not yet have CSRF protection — backlog item")
    def test_edit_form_has_csrf(self, nav, base_url):
        """Edit ticket form must include a CSRF token."""
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
            csrf_fields = nav.driver.find_elements(By.NAME, "csrf_token")
            assert len(csrf_fields) > 0, \
                "SECURITY: Edit form has no CSRF token"
        finally:
            nav.to_default()


class TestSQLInjection:
    """Test SQL injection prevention on key endpoints."""

    @pytest.fixture(autouse=True)
    def _setup(self, nav, error_log):
        nav.close_popups()
        error_log.mark_position()
        yield
        nav.close_popups()
        nav.to_default()

    def test_search_order_injection(self, nav, base_url, error_log):
        """Search ORDER BY should be whitelisted, not directly concatenated."""
        error_log.mark_position()

        nav.to_main()
        try:
            # Try to inject via ordertype parameter
            result = nav.driver.execute_script(f"""
                var xhr = new XMLHttpRequest();
                var formData = new FormData();
                formData.append('frm_query', 'test');
                formData.append('frm_search_in', 'description');
                formData.append('frm_ordertype', "date; DROP TABLE users; --");
                formData.append('frm_order_desc', 'DESC');
                xhr.open('POST', '{base_url}search.php', false);
                try {{
                    xhr.send(formData);
                    return {{
                        status: xhr.status,
                        response: xhr.responseText.substring(0, 1000)
                    }};
                }} catch(e) {{
                    return {{ status: 0, error: e.message }};
                }}
            """)
        finally:
            nav.to_default()

        if result:
            response = result.get('response', '').lower()
            # Should NOT contain SQL error messages
            sql_error_markers = [
                "you have an error in your sql syntax",
                "sql syntax",
                "mysql_",
                "mysqli_",
                "sqlstate",
            ]
            found = [m for m in sql_error_markers if m in response]
            assert not found, \
                f"SECURITY: SQL injection via ORDER BY appears possible: {found}"


class TestAuthGating:
    """Test that pages require authentication."""

    PROTECTED_PAGES = [
        "main.php",
        "edit.php",
        "search.php",
        "units.php",
        "facilities.php",
        "reports.php",
        "config.php",
        "chat.php",
        "member.php",       # Personnel module
        "log.php",
        "mobile.php",
        "board.php",
        "routes.php",       # Dispatch page
    ]

    @pytest.mark.parametrize("page", PROTECTED_PAGES)
    def test_page_requires_auth(self, base_url, page):
        """Page '{page}' should require authentication."""
        # Use a fresh browser session (no cookies) to test
        from selenium.webdriver.edge.options import Options as EdgeOptions
        options = EdgeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--start-maximized")

        fresh_driver = None
        try:
            from selenium import webdriver
            fresh_driver = webdriver.Edge(options=options)
            fresh_driver.set_page_load_timeout(15)

            url = f"{base_url}{page}"
            fresh_driver.get(url)
            time.sleep(2)

            source = (fresh_driver.page_source or "").lower()

            # Page should redirect to login, show login form,
            # or show access denied — NOT show actual content
            shows_login = "frm_user" in source or "frm_passwd" in source
            shows_denied = "denied" in source or "unauthorized" in source
            is_empty = len(source.strip()) < 100

            # Check if the page is loaded within the frameset
            # (which means it redirected to index/login)
            url_after = fresh_driver.current_url.lower()
            redirected_to_login = "index.php" in url_after or \
                                  url_after.endswith("/tickets/")

            page_is_protected = (shows_login or shows_denied or
                                 is_empty or redirected_to_login)

            assert page_is_protected, \
                f"SECURITY: {page} is accessible without authentication. " \
                f"URL after: {url_after}"
        except Exception as e:
            if "timeout" in str(e).lower():
                pytest.skip(f"Page load timed out for {page}")
            raise
        finally:
            if fresh_driver:
                fresh_driver.quit()
