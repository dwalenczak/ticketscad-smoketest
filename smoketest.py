from __future__ import annotations

import os
import re
import shutil
import time
import getpass
from pathlib import Path
from datetime import datetime

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService

from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService

from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService


# Enable ANSI colors on modern Windows terminals
if os.name == "nt":
    os.system("")


class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    CYAN = "\033[36m"
    MAGENTA = "\033[35m"
    WHITE = "\033[37m"


def ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log(msg: str, level: str = "INFO") -> None:
    color = {
        "INFO": C.CYAN,
        "OK": C.GREEN,
        "WARN": C.YELLOW,
        "ERR": C.RED,
        "DBG": C.MAGENTA,
    }.get(level, C.WHITE)
    print(f"{color}[{ts()}] [{level:<4}] {msg}{C.RESET}")

def do_login(driver, url: str, username: str, password: str) -> bool:
    log(f"Opening {url}", "INFO")
    driver.get(url)

    wait = WebDriverWait(driver, 15)

    try:
        # Top-level is a frameset, so switch into the main frame first
        log("Waiting for main frame...", "INFO")
        driver.switch_to.default_content()
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "main")))

        log("Waiting for frm_user...", "INFO")
        username_el = wait.until(EC.presence_of_element_located((By.NAME, "frm_user")))

        log("Waiting for frm_passwd...", "INFO")
        password_el = wait.until(EC.presence_of_element_located((By.NAME, "frm_passwd")))

    except Exception:
        log("Could not find login fields inside frame 'main'.", "ERR")
        log(f"Current URL: {driver.current_url}", "DBG")
        log(f"Page title: {driver.title}", "DBG")

        driver.switch_to.default_content()
        screenshot = Path.cwd() / "ticketscad_login_form_not_found.png"
        html_dump = Path.cwd() / "ticketscad_login_form_not_found.html"

        driver.save_screenshot(str(screenshot))
        html_dump.write_text(driver.page_source, encoding="utf-8", errors="ignore")

        log(f"Saved screenshot: {screenshot}", "WARN")
        log(f"Saved HTML dump: {html_dump}", "WARN")
        return False

    log("Entering username...", "DBG")
    username_el.clear()
    username_el.send_keys(username)

    log("Entering password...", "DBG")
    password_el.clear()
    password_el.send_keys(password)

    log("Submitting login form...", "INFO")
    driver.execute_script("document.login_form.submit();")

    log("Waiting for login result...", "INFO")

    for _ in range(15):
        time.sleep(1)

        # Check inside main frame
        driver.switch_to.default_content()
        try:
            driver.switch_to.frame("main")
        except Exception:
            log("Could not switch back to frame 'main' after submit.", "ERR")
            return False

        # Failure marker
        warn_nodes = driver.find_elements(By.CSS_SELECTOR, "font.warn")
        for warn in warn_nodes:
            try:
                if warn.is_displayed() and "login failed" in warn.text.lower():
                    log("Login failed. TicketsCAD returned the warning message.", "ERR")
                    driver.switch_to.default_content()
                    screenshot = Path.cwd() / "ticketscad_login_failed.png"
                    driver.save_screenshot(str(screenshot))
                    log(f"Saved screenshot: {screenshot}", "WARN")
                    return False
            except Exception:
                pass

        # Success heuristic: login fields are gone from main frame
        still_has_user = driver.find_elements(By.NAME, "frm_user")
        still_has_pass = driver.find_elements(By.NAME, "frm_passwd")

        if not still_has_user and not still_has_pass:
            driver.switch_to.default_content()
            log("Login appears successful.", "OK")
            log(f"Current URL: {driver.current_url}", "DBG")
            return True

    driver.switch_to.default_content()
    log("Could not confirm success or failure within timeout.", "ERR")
    screenshot = Path.cwd() / "ticketscad_login_uncertain.png"
    driver.save_screenshot(str(screenshot))
    log(f"Saved screenshot: {screenshot}", "WARN")
    return False

def test_top_tabs_dynamic(driver, include_hidden: bool = False) -> dict[str, dict]:
    wait = WebDriverWait(driver, 10)

    error_markers = [
        "fatal error",
        "parse error",
        "warning:",
        "uncaught",
        "traceback",
        "stack trace",
        "500 internal server error",
        "404 not found",
        "not found on this server",
        "sql syntax",
        "login failed",
    ]

    original_handle = driver.current_window_handle
    results = {}

    def reset_to_original():
        # Close any spawned windows and return to the original one
        try:
            handles = driver.window_handles[:]
            for h in handles:
                if h != original_handle:
                    try:
                        driver.switch_to.window(h)
                        driver.close()
                    except Exception:
                        pass
        except Exception:
            pass

        driver.switch_to.window(original_handle)
        driver.switch_to.default_content()

    def extract_target_from_onclick(onclick: str) -> str:
        # Pull all single-quoted tokens safely, then choose the one that looks like a path
        # Examples:
        #   go_there('main.php', this.id);
        #   do_emd_card('./emd_cards/demo.pdf')
        #   light_butt('links'); parent.main.$('links').style.display='inline';
        tokens = re.findall(r"'([^']*)'", onclick or "")
        for token in tokens:
            t = token.lower()
            if t.endswith(".php") or t.endswith(".pdf") or "/" in t:
                return token
        return ""

    def main_frame_src() -> str:
        driver.switch_to.default_content()
        return (driver.find_element(By.NAME, "main").get_attribute("src") or "").strip()

    def main_frame_source() -> str:
        driver.switch_to.default_content()
        driver.switch_to.frame("main")
        try:
            return (driver.page_source or "")
        finally:
            driver.switch_to.default_content()

    def main_frame_control_count() -> int:
        driver.switch_to.default_content()
        driver.switch_to.frame("main")
        try:
            els = driver.find_elements(
                By.CSS_SELECTOR,
                "a[href], button, input:not([type='hidden']), select, textarea, span[onclick]"
            )
            return len(els)
        finally:
            driver.switch_to.default_content()

    def links_panel_state() -> tuple[bool, int]:
        driver.switch_to.default_content()
        driver.switch_to.frame("main")
        try:
            panels = driver.find_elements(By.ID, "links")
            if not panels:
                return False, 0
            panel = panels[0]
            # Presence + content count, no is_displayed() call
            controls = panel.find_elements(By.CSS_SELECTOR, "a[href], button, input, select, textarea, span[onclick]")
            text_len = len((panel.text or "").strip())
            return True, max(len(controls), 1 if text_len > 0 else 0)
        finally:
            driver.switch_to.default_content()

    log("Waiting for Tickets frameset...", "INFO")
    driver.switch_to.default_content()
    wait.until(EC.presence_of_element_located((By.ID, "the_frames")))

    log("Reading tab strip from upper frame...", "INFO")
    wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "upper")))
    raw_tabs = driver.find_elements(By.CSS_SELECTOR, "td[colspan='99'] span[id][onclick]")

    tabs = []
    seen_ids = set()

    for el in raw_tabs:
        try:
            tab_id = (el.get_attribute("id") or "").strip()
            text = (el.text or "").strip() or f"[{tab_id}]"
            onclick = (el.get_attribute("onclick") or "").strip()
            style = (el.get_attribute("style") or "").lower()

            if not tab_id or tab_id in seen_ids:
                continue
            seen_ids.add(tab_id)

            hidden = "display: none" in style
            if hidden and not include_hidden:
                continue

            tabs.append({
                "id": tab_id,
                "text": text,
                "onclick": onclick,
                "hidden": hidden,
                "target": extract_target_from_onclick(onclick),
            })
        except Exception:
            pass

    driver.switch_to.default_content()

    log(f"Detected {len(tabs)} tab(s).", "OK")
    for tab in tabs:
        log(
            f"Tab found: id={tab['id']}, text={tab['text']}, target={tab['target'] or '[none]'}, onclick={tab['onclick']}",
            "DBG"
        )

    for tab in tabs:
        tab_id = tab["id"]
        tab_text = tab["text"]
        onclick = tab["onclick"]
        target = tab["target"]

        results[tab_id] = {
            "text": tab_text,
            "onclick": onclick,
            "target": target,
            "status": "NOT_RUN",
            "detail": "",
        }

        log(f"Testing tab: {tab_text} [{tab_id}]", "INFO")

        try:
            reset_to_original()

            before_handles = set(driver.window_handles)
            before_src = main_frame_src()
            before_source = main_frame_source()

            # Click the tab from upper frame
            wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, "upper")))
            tab_el = driver.find_element(By.ID, tab_id)

            try:
                tab_el.click()
            except Exception:
                driver.execute_script("arguments[0].click();", tab_el)

            driver.switch_to.default_content()

            # First check whether a new window/tab opened
            new_window_opened = False
            try:
                WebDriverWait(driver, 3).until(EC.new_window_is_opened(list(before_handles)))
                new_window_opened = True
            except TimeoutException:
                new_window_opened = False

            if new_window_opened:
                after_handles = set(driver.window_handles)
                new_handles = [h for h in after_handles if h not in before_handles]

                if new_handles:
                    new_handle = new_handles[0]
                    driver.switch_to.window(new_handle)

                    # Keep this lightweight to avoid weird JS serialization issues
                    new_url = ""
                    new_title = ""
                    new_source = ""

                    try:
                        new_url = driver.current_url or ""
                    except Exception:
                        pass

                    try:
                        new_title = driver.title or ""
                    except Exception:
                        pass

                    try:
                        new_source = driver.page_source or ""
                    except Exception:
                        pass

                    low_blob = f"{new_url}\n{new_title}\n{new_source}".lower()
                    obvious_error = next((m for m in error_markers if m in low_blob), None)

                    if obvious_error:
                        results[tab_id]["status"] = "FAIL"
                        results[tab_id]["detail"] = f"new window error text: {obvious_error}"
                        log(f"{tab_text} failed in new window: {obvious_error}", "ERR")
                    else:
                        results[tab_id]["status"] = "PASS"
                        results[tab_id]["detail"] = f"opened new window url={new_url or '[unknown]'} title={new_title or '[blank]'}"
                        log(f"{tab_text} opened new window: {new_url or '[unknown]'}", "OK")

                    reset_to_original()
                    continue

            # No new window: inspect main frame result
            time.sleep(1.5)
            after_src = main_frame_src()
            after_source = main_frame_source()
            control_count = main_frame_control_count()

            low_source = after_source.lower()
            obvious_error = next((m for m in error_markers if m in low_source), None)

            # Special case: Links just shows an inline panel in main
            if "parent.main.$('links').style.display='inline'" in onclick:
                panel_exists, panel_controls = links_panel_state()
                if panel_exists and panel_controls > 0:
                    results[tab_id]["status"] = "PASS"
                    results[tab_id]["detail"] = f"links panel present with {panel_controls} control/content item(s)"
                    log(f"{tab_text} revealed links panel successfully.", "OK")
                elif panel_exists:
                    results[tab_id]["status"] = "WARN"
                    results[tab_id]["detail"] = "links panel exists but appears empty"
                    log(f"{tab_text} revealed a links panel, but it appears empty.", "WARN")
                else:
                    results[tab_id]["status"] = "FAIL"
                    results[tab_id]["detail"] = "links panel not found in main frame"
                    log(f"{tab_text} did not reveal the links panel.", "ERR")
                continue

            if obvious_error:
                results[tab_id]["status"] = "FAIL"
                results[tab_id]["detail"] = f"error text: {obvious_error}"
                log(f"{tab_text} failed: {obvious_error}", "ERR")

                screenshot = Path.cwd() / f"tab_fail_{tab_id}.png"
                driver.save_screenshot(str(screenshot))
                log(f"Saved screenshot: {screenshot}", "WARN")
                continue

            if target:
                target_l = target.lower()
                if target_l in after_src.lower() or target_l in low_source:
                    results[tab_id]["status"] = "PASS"
                    results[tab_id]["detail"] = f"target detected: {target}"
                    log(f"{tab_text} loaded expected target: {target}", "OK")
                    continue

            if after_src != before_src:
                if control_count > 0:
                    results[tab_id]["status"] = "PASS"
                    results[tab_id]["detail"] = f"main frame changed to {after_src} with {control_count} control(s)"
                    log(f"{tab_text} changed main frame and loaded usable content.", "OK")
                else:
                    results[tab_id]["status"] = "WARN"
                    results[tab_id]["detail"] = f"main frame changed to {after_src}, but no controls found"
                    log(f"{tab_text} changed main frame, but page looks sparse.", "WARN")
                continue

            if after_source != before_source:
                if control_count > 0:
                    results[tab_id]["status"] = "PASS"
                    results[tab_id]["detail"] = f"main content changed with {control_count} control(s)"
                    log(f"{tab_text} changed content and loaded usable controls.", "OK")
                else:
                    results[tab_id]["status"] = "WARN"
                    results[tab_id]["detail"] = "main content changed, but no controls found"
                    log(f"{tab_text} changed content, but page looks sparse.", "WARN")
                continue

            if control_count > 0:
                results[tab_id]["status"] = "WARN"
                results[tab_id]["detail"] = f"{control_count} control(s) found, but no clear nav/content change"
                log(f"{tab_text} has controls, but no clear page transition was detected.", "WARN")
            else:
                results[tab_id]["status"] = "FAIL"
                results[tab_id]["detail"] = "no clear nav/content change and no controls found"
                log(f"{tab_text} did not produce a usable page.", "ERR")

                screenshot = Path.cwd() / f"tab_fail_{tab_id}.png"
                driver.save_screenshot(str(screenshot))
                log(f"Saved screenshot: {screenshot}", "WARN")

        except Exception as e:
            results[tab_id]["status"] = "FAIL"
            results[tab_id]["detail"] = str(e)
            log(f"{tab_text} blew up: {e}", "ERR")

            try:
                reset_to_original()
                screenshot = Path.cwd() / f"tab_fail_{tab_id}.png"
                driver.save_screenshot(str(screenshot))
                log(f"Saved screenshot: {screenshot}", "WARN")
            except Exception:
                pass

    reset_to_original()

    print()
    print(f"{C.BOLD}Dynamic Tab Test Summary{C.RESET}")
    print(f"{C.DIM}{'-' * 110}{C.RESET}")
    for tab_id, info in results.items():
        print(
            f"{info['text']:<14} [{tab_id:<10}] {info['status']:<5}  "
            f"target={info['target'] or '[none]'}  {info['detail']}"
        )

    return results    

# --------------------------------------------------------------------------
# MAIN CODE BODY
# --------------------------------------------------------------------------
    
print(f"{C.CYAN}{C.BOLD}")
print("╔══════════════════════════════════════════════════════════════╗")
print("║                TicketsCAD Selenium Smoke Test                ║")
print("╚══════════════════════════════════════════════════════════════╝")
print(f"{C.RESET}")

# --------------------------------------------------------------------------
# Detect installed browsers and local webdrivers
# --------------------------------------------------------------------------

pf = Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
pfx86 = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"))
local = Path(os.environ.get("LOCALAPPDATA", r"C:\Users\Default\AppData\Local"))

common_driver_dirs = [
    Path.cwd(),
    Path(r"C:\WebDriver"),
    Path(r"C:\WebDriver\bin"),
    Path(r"C:\Selenium"),
    Path(r"C:\SeleniumDrivers"),
]

def first_existing(paths: list[Path]) -> Path | None:
    for p in paths:
        if p.exists():
            return p
    return None

def find_driver(exe_name: str) -> Path | None:
    hit = shutil.which(exe_name)
    if hit:
        return Path(hit)
    for d in common_driver_dirs:
        p = d / exe_name
        if p.exists():
            return p
    return None

browsers = []

edge_binary = first_existing([
    pf / "Microsoft" / "Edge" / "Application" / "msedge.exe",
    pfx86 / "Microsoft" / "Edge" / "Application" / "msedge.exe",
])
if edge_binary:
    browsers.append({
        "name": "Edge",
        "key": "edge",
        "binary": edge_binary,
        "driver": find_driver("msedgedriver.exe"),
    })

chrome_binary = first_existing([
    pf / "Google" / "Chrome" / "Application" / "chrome.exe",
    pfx86 / "Google" / "Chrome" / "Application" / "chrome.exe",
    local / "Google" / "Chrome" / "Application" / "chrome.exe",
])
if chrome_binary:
    browsers.append({
        "name": "Chrome",
        "key": "chrome",
        "binary": chrome_binary,
        "driver": find_driver("chromedriver.exe"),
    })

firefox_binary = first_existing([
    pf / "Mozilla Firefox" / "firefox.exe",
    pfx86 / "Mozilla Firefox" / "firefox.exe",
])
if firefox_binary:
    browsers.append({
        "name": "Firefox",
        "key": "firefox",
        "binary": firefox_binary,
        "driver": find_driver("geckodriver.exe"),
    })

opera_binary = first_existing([
    local / "Programs" / "Opera" / "opera.exe",
    pf / "Opera" / "opera.exe",
    pfx86 / "Opera" / "opera.exe",
])
if opera_binary:
    opera_driver = find_driver("operadriver.exe") or find_driver("chromedriver.exe")
    browsers.append({
        "name": "Opera",
        "key": "opera",
        "binary": opera_binary,
        "driver": opera_driver,
    })

if not browsers:
    log("No supported browsers detected.", "ERR")
    raise SystemExit(1)

# --------------------------------------------------------------------------
# Browser Picker, TicketsCAD URL, and Admin Creds
# --------------------------------------------------------------------------

print(f"{C.BOLD}Detected browsers / drivers{C.RESET}")
print(f"{C.DIM}{'-' * 70}{C.RESET}")
for i, b in enumerate(browsers, start=1):
    driver_text = str(b["driver"]) if b["driver"] else "None found locally"
    print(f"{i}. {b['name']}")
    print(f"   Browser : {b['binary']}")
    print(f"   Driver  : {driver_text}")
    print()

choice = input(f"{C.BOLD}Select browser number:{C.RESET} ").strip()
if not choice.isdigit() or int(choice) < 1 or int(choice) > len(browsers):
    log("Invalid browser selection.", "ERR")
    raise SystemExit(1)

browser = browsers[int(choice) - 1]

url = input(f"{C.BOLD}TicketsCAD URL:{C.RESET} ").strip()
if not url.lower().startswith(("http://", "https://")):
    url = "http://" + url
    log(f"No scheme provided. Using: {url}", "WARN")

username = input(f"{C.BOLD}Admin username:{C.RESET} ").strip()
password = getpass.getpass(f"{C.BOLD}Admin password:{C.RESET} ")

# --------------------------------------------------------------------------
# Launch browser
# --------------------------------------------------------------------------

log(f"Selected browser: {browser['name']}", "INFO")
log(f"Browser binary: {browser['binary']}", "DBG")
if browser["driver"]:
    log(f"Using local driver: {browser['driver']}", "DBG")
else:
    log("No local driver found. Letting Selenium Manager try.", "DBG")

driver = None

try:
    if browser["key"] == "edge":
        options = EdgeOptions()
        options.use_chromium = True
        options.binary_location = str(browser["binary"])
        options.add_argument("--start-maximized")
        if browser["driver"]:
            driver = webdriver.Edge(
                service=EdgeService(executable_path=str(browser["driver"])),
                options=options
            )
        else:
            driver = webdriver.Edge(options=options)

    elif browser["key"] == "chrome":
        options = ChromeOptions()
        options.binary_location = str(browser["binary"])
        options.add_argument("--start-maximized")
        if browser["driver"]:
            driver = webdriver.Chrome(
                service=ChromeService(executable_path=str(browser["driver"])),
                options=options
            )
        else:
            driver = webdriver.Chrome(options=options)

    elif browser["key"] == "firefox":
        options = FirefoxOptions()
        options.binary_location = str(browser["binary"])
        if browser["driver"]:
            driver = webdriver.Firefox(
                service=FirefoxService(executable_path=str(browser["driver"])),
                options=options
            )
        else:
            driver = webdriver.Firefox(options=options)
        driver.maximize_window()

    elif browser["key"] == "opera":
        if not browser["driver"]:
            log("Opera detected, but no operadriver/chromedriver found locally.", "ERR")
            raise SystemExit(1)

        options = ChromeOptions()
        options.binary_location = str(browser["binary"])
        options.add_argument("--start-maximized")
        driver = webdriver.Chrome(
            service=ChromeService(executable_path=str(browser["driver"])),
            options=options
        )

    else:
        log("Unsupported browser selection.", "ERR")
        raise SystemExit(1)

    driver.set_page_load_timeout(60)

    # Bad login test
    login_ok = do_login(driver, url, "baduser", "badpass")

    if login_ok:
        log("Unexpected result: bad login succeeded.", "ERR")
    else:
        log("Expected result: bad login failed correctly.", "OK")

    # Good login test
    login_ok = do_login(driver, url, username, password)

    if login_ok:
        log("Stopping here as requested.", "INFO")
    else:
        log("Stopping after failed login test.", "INFO")

    # Top-tabs test
    if login_ok:
        log("Running dynamic top-tab smoke test...", "INFO")
        tab_results = test_top_tabs_dynamic(driver)

        hard_fails = [k for k, v in tab_results.items() if v["status"] == "FAIL"]
        if hard_fails:
            log(f"Tabs with hard failures: {', '.join(hard_fails)}", "ERR")
        else:
            log("No hard tab failures detected.", "OK")
    else:
        log("Skipping tab test because login failed.", "ERR")

except TimeoutException:
    log("Page load timed out.", "ERR")

except Exception as e:
    log(f"Fatal error: {e}", "ERR")

finally:
    if driver is not None:
        input(f"{C.BOLD}Press Enter to close Selenium...{C.RESET}")
        driver.quit()
