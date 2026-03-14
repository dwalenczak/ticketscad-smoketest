# TicketsCAD Selenium Smoke Test (Windows)

This repository contains a single Python script (`smoketest.py`) that runs an interactive Selenium smoke test against a TicketsCAD instance.

The script:
- Detects locally installed browsers (Edge, Chrome, Firefox, Opera).
- Attempts to find matching local WebDriver binaries (`msedgedriver.exe`, `chromedriver.exe`, `geckodriver.exe`, `operadriver.exe`) in common Windows paths.
- Prompts for your TicketsCAD URL and admin credentials.
- Runs a bad-login test (expected failure), then a real login test.
- If login succeeds, runs a dynamic top-tab smoke test.

---

## 1) Prerequisites

- **Windows 10/11**
- **Python 3.10+** (3.11 or 3.12 recommended)
- At least one supported browser installed:
  - Microsoft Edge
  - Google Chrome
  - Mozilla Firefox
  - Opera
- Access to your TicketsCAD environment URL and admin credentials for smoke testing.

---

## 2) Download / open the project

If you already have the files, open a terminal in the project folder.

If using Git:

```powershell
git clone <your-repo-url>
cd ticketscad-smoketest
```

You should see `smoketest.py` in this directory.

---

## 3) Install Python dependencies with pip (native install)

This script depends on Selenium (all other imported modules are part of Python’s standard library).

From PowerShell or Command Prompt:

```powershell
python -m pip install --upgrade pip
python -m pip install selenium
```

Optional verification:

```powershell
python -m pip show selenium
python -m pip list
```

---

## 4) Browser driver setup (important)

### How the script handles drivers
The script first looks for local driver executables in:
- Current folder
- `C:\WebDriver`
- `C:\WebDriver\bin`
- `C:\Selenium`
- `C:\SeleniumDrivers`
- Any location already available via `PATH`

If no local driver is found for **Edge, Chrome, or Firefox**, Selenium may still run through **Selenium Manager** (automatic driver resolution).

> **Opera is the exception:** this script requires a local `operadriver.exe` (or `chromedriver.exe`) for Opera.

### Manual driver download links
If you want to manually install drivers (or if automatic resolution fails), use the official sources:

- **ChromeDriver (Google Chrome):** https://googlechromelabs.github.io/chrome-for-testing/
- **Edge WebDriver (Microsoft Edge):** https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/
- **GeckoDriver (Mozilla Firefox):** https://github.com/mozilla/geckodriver/releases
- **OperaDriver (Opera):** https://github.com/operasoftware/operachromiumdriver/releases

After downloading, place the driver executable in one of the folders above (or add its folder to `PATH`).

---

## 5) Run the smoke test

From the repository root:

```powershell
python smoketest.py
```

You will be prompted to:
1. Select detected browser number.
2. Enter TicketsCAD URL.
3. Enter admin username.
4. Enter admin password (hidden input).

What happens next:
- The script runs a bad-login attempt (`baduser` / `badpass`) and expects failure.
- Then it runs your real login attempt.
- If login succeeds, it runs a dynamic top-tab test and prints a summary.
- On specific failures, it writes screenshots/HTML dumps to the current folder.

At the end, press Enter to close Selenium.

---

## 6) Watch server-side logs while running

While this script runs, monitor your **TicketsCAD server-side error/access logs** in parallel. This is strongly recommended because:
- Front-end failures in Selenium often map to server-side stack traces or SQL/runtime errors.
- A UI action may appear to “hang” but the server log usually provides the direct root cause.
- Correlating script timestamps with server logs speeds up troubleshooting significantly.

If possible, keep the app log tailing in a second terminal during test execution.

---

## 7) Typical output artifacts

Depending on failures, you may see files such as:
- `ticketscad_login_form_not_found.png`
- `ticketscad_login_form_not_found.html`
- `ticketscad_login_failed.png`
- `ticketscad_login_uncertain.png`
- `tab_fail_<tab_id>.png`

These files are useful for validating what Selenium observed at failure time.

---

## 8) Troubleshooting

### `ModuleNotFoundError: No module named 'selenium'`
Selenium is not installed in the Python interpreter you are using.

Fix:

```powershell
python -m pip install selenium
```

### Browser is detected, but WebDriver fails to start
- Ensure browser version and driver version are compatible.
- Update browser to latest stable version.
- Install matching driver manually and put it in `PATH` or in one of the known driver folders.

### `No supported browsers detected.`
Install one of Edge/Chrome/Firefox/Opera, then re-run.

### URL issues
If you enter a URL without `http://` or `https://`, the script prepends `http://` automatically.

---

## 9) Quick start (copy/paste)

```powershell
# From project directory
python -m pip install --upgrade pip
python -m pip install selenium
python smoketest.py
```
