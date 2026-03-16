"""
Test 10: AJAX endpoint validation.

Tests all major AJAX endpoints for proper responses and no PHP errors.
These endpoints are called by JavaScript in the browser and are
critical for interactive features.
"""
import time
import pytest

from selenium.webdriver.common.by import By


# AJAX endpoints and their expected request patterns
AJAX_ENDPOINTS = [
    ("ajax/routes_form.php", {"ticket_id": "5", "sortby": "distance", "dir": "ASC"}),
    ("ajax/mobile_main.php", {}),
    ("ajax/mobile_tktlist.php", {}),
    ("ajax/mobile_buttons.php", {}),
    ("ajax/facboard_incidents.php", {"sortby": "date", "dir": "DESC"}),
    ("ajax/get_replacetext.php", {}),
]


class TestAjaxEndpoints:
    """Test AJAX endpoints return valid responses."""

    @pytest.fixture(autouse=True)
    def _setup(self, nav, error_log):
        nav.close_popups()
        error_log.mark_position()
        yield
        nav.close_popups()
        nav.to_default()

    @pytest.mark.parametrize("endpoint,params", AJAX_ENDPOINTS)
    def test_ajax_no_fatal_errors(self, nav, base_url, error_log, endpoint, params):
        """AJAX endpoint '{endpoint}' should not produce fatal PHP errors."""
        error_log.mark_position()

        # Build URL with params
        param_str = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{base_url}{endpoint}"
        if param_str:
            url += f"?{param_str}"

        # Load via JavaScript in the main frame
        nav.to_main()
        try:
            result = nav.driver.execute_script(f"""
                var xhr = new XMLHttpRequest();
                xhr.open('GET', '{url}', false);
                try {{
                    xhr.send();
                    return {{
                        status: xhr.status,
                        response: xhr.responseText.substring(0, 2000),
                        error: null
                    }};
                }} catch(e) {{
                    return {{
                        status: 0,
                        response: '',
                        error: e.message
                    }};
                }}
            """)
        finally:
            nav.to_default()

        if result and result.get('error'):
            pytest.skip(f"XHR failed: {result['error']}")

        if result:
            status = result.get('status', 0)
            response = result.get('response', '')
            response_lower = response.lower()

            # Check for PHP fatal errors in response
            fatal_markers = [
                "fatal error", "parse error",
                "call to undefined function",
            ]
            found = [m for m in fatal_markers if m in response_lower]
            assert not found, \
                f"AJAX {endpoint} returned PHP errors: {found}\n" \
                f"Response preview: {response[:500]}"

            # Check HTTP status
            assert status == 200, \
                f"AJAX {endpoint} returned status {status}"

        # Also check server-side log
        php_errors = error_log.get_php_errors()
        # Filter to only errors related to this endpoint
        endpoint_errors = [
            e for e in php_errors
            if endpoint.replace("/", "\\\\") in e or endpoint.split("/")[-1] in e
        ]
        assert not endpoint_errors, \
            f"AJAX {endpoint} triggered server errors:\n" + \
            "\n".join(str(e)[:200] for e in endpoint_errors)


class TestTileProxy:
    """Test the map tile proxy endpoint."""

    @pytest.fixture(autouse=True)
    def _setup(self, nav, error_log):
        error_log.mark_position()
        yield
        nav.to_default()

    def test_tile_proxy_returns_image(self, nav, base_url):
        """Tile proxy should return a valid image for a standard tile request."""
        nav.to_main()
        try:
            result = nav.driver.execute_script(f"""
                var xhr = new XMLHttpRequest();
                xhr.open('GET', '{base_url}tile_proxy.php?z=10&x=268&y=374', false);
                try {{
                    xhr.send();
                    return {{
                        status: xhr.status,
                        contentType: xhr.getResponseHeader('Content-Type'),
                        size: xhr.responseText.length
                    }};
                }} catch(e) {{
                    return {{ status: 0, error: e.message }};
                }}
            """)
        finally:
            nav.to_default()

        if result and result.get('error'):
            pytest.skip(f"Tile proxy request failed: {result['error']}")

        if result:
            assert result.get('status') == 200, \
                f"Tile proxy returned status {result.get('status')}"
            content_type = result.get('contentType', '')
            assert 'image' in content_type, \
                f"Tile proxy returned wrong content type: {content_type}"
            assert result.get('size', 0) > 100, \
                "Tile proxy returned too-small response (likely empty/error)"
