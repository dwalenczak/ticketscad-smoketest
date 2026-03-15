@echo off
REM ============================================================
REM TicketsCAD Smoke Test Runner
REM ============================================================
REM
REM Usage:
REM   run_tests.bat                  - Run full suite (headed Edge)
REM   run_tests.bat --headless       - Run full suite headless
REM   run_tests.bat smoke            - Quick smoke tests only
REM   run_tests.bat login            - Login tests only
REM   run_tests.bat navigation       - Navigation tab tests only
REM   run_tests.bat tickets          - Ticket CRUD tests
REM   run_tests.bat dispatch         - Dispatch/routes tests
REM   run_tests.bat mobile           - Mobile view tests
REM   run_tests.bat security         - Security tests (auth, CSRF, SQLi)
REM   run_tests.bat ajax             - AJAX endpoint tests
REM   run_tests.bat map              - Map/tile tests
REM   run_tests.bat config           - Config page tests
REM   run_tests.bat all              - All tests, don't stop on first failure
REM
REM Options (append to any command):
REM   --headless      Run without visible browser
REM   --browser=chrome  Use Chrome instead of Edge
REM   --base-url=URL  Override TicketsCAD URL
REM ============================================================

set MARKER=%1
set EXTRA_ARGS=%2 %3 %4 %5

if "%MARKER%"=="" (
    echo Running FULL test suite...
    python -m pytest %EXTRA_ARGS%
    goto :end
)

if "%MARKER%"=="all" (
    echo Running ALL tests, continuing on failure...
    python -m pytest --no-header %EXTRA_ARGS%
    goto :end
)

if "%MARKER%"=="smoke" (
    echo Running SMOKE tests...
    python -m pytest -m smoke --no-header %EXTRA_ARGS%
    goto :end
)

if "%MARKER%"=="--headless" (
    echo Running FULL suite headless...
    python -m pytest --headless %EXTRA_ARGS%
    goto :end
)

echo Running %MARKER% tests...
python -m pytest -m %MARKER% --no-header %EXTRA_ARGS%

:end
