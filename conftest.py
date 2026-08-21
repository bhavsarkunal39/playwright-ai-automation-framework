import os
import sys
from datetime import datetime
# Add the parent directory of project to sys.path
project_root = os.getcwd()
sys.path.append(project_root)
from urllib import request
import pytest
import logging
import atexit
import signal
import threading
import weakref
import subprocess
import platform
import Keywords.projectVariables as globalVar
from playwright.sync_api import Playwright, Page, Browser
from Profiles.encryptDecrypt import Security
from typing import Generator
from Keywords.reporting.ExtentReporting import ExtentReporting, ReportConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    force=True
)
log = logging.getLogger(__name__)

# Create a handler to prevent 'I/O operation on closed file' errors
class SafeHandler(logging.StreamHandler):
    def emit(self, record):
        try:
            # Check if stream is still open before writing
            if hasattr(self.stream, 'closed') and self.stream.closed:
                return  # Don't attempt to write to closed stream
            # Additional check for stream writability
            if hasattr(self.stream, 'write'):
                super().emit(record)
        except (ValueError, OSError, AttributeError):
            # Silently handle 'I/O operation on closed file' errors
            # and other stream-related errors
            pass

# Remove all existing handlers and add only the safe handler
log.handlers.clear()
log.addHandler(SafeHandler())

# Global cleanup flag to prevent duplicate executions
_cleanup_performed = False
_cleanup_lock = threading.Lock()

def encrypt_profile_on_exit():
    """Cleanup function to encrypt profile on exit"""
    global _cleanup_performed 
    with _cleanup_lock:
        if _cleanup_performed:
            return  # Prevent multiple executions
        _cleanup_performed = True
    
    def safe_log(message):
        """Safe logging function that falls back to print"""
        try:
            # Check if any handlers are available and working
            if log.handlers:
                log.info(message)
            else:
                print(message)
        except (ValueError, OSError, AttributeError):
            print(message)
    
    if globalVar.exit_handler:
        print("Profile Encryption cleanup already performed by pytest_sessionfinish().")
    else:
        print("encrypt_profile_on_exit(): Performing profile encryption cleanup.")
        try:
            profile = globalVar.profile
            profilePath = os.path.join(globalVar.profilePath, f"{profile}.json")
            if os.path.exists(profilePath):
                print(f"Encrypting profile {profile} from cleanup handler...")     
                Security.encrypt_json_file(profilePath)
                print(f"Encrypted the Profile {profile} via cleanup handler")
                globalVar.exit_handler = True
        except Exception as e:
            # Use print for errors in cleanup handlers
            print(f"Error encrypting profile in cleanup handler: {str(e)}")

def handle_exit_signal(sig, frame):
    """Handle exit signals for cleanup"""
    log.warning(f"Signal {sig} received. Running profile encryption cleanup.")
    if globalVar.exit_handler:
        log.info("Profile Encryption cleanup already performed by pytest_sessionfinish().")
    else:
        delete_pycache_dirs()
        encrypt_profile_on_exit()
        sys.exit(0)
        globalVar.exit_handler = True
        log.info(f"Signal {sig} received: Profile encryption cleanup completed.")

def monitor_main_thread():
    """Monitor main thread for debug termination scenarios"""
    main_thread = threading.main_thread()
    main_thread.join()  # Wait for main thread to end
    encrypt_profile_on_exit()

# Register cleanup handlers for all termination scenarios
def register_cleanup_handlers():
    """Register multiple cleanup handlers"""
    # Normal exit
    atexit.register(encrypt_profile_on_exit)  
    # Signal handlers
    try:
        signal.signal(signal.SIGINT, handle_exit_signal)   # Ctrl+C
        signal.signal(signal.SIGTERM, handle_exit_signal)  # kill
        if platform.system() == "Windows":
            signal.signal(signal.SIGBREAK, handle_exit_signal)  # Ctrl+Break
    except (OSError, ValueError) as e:
        log.warning(f"Could not register signal handler: {e}")  
    # Debug termination monitor
    monitor_thread = threading.Thread(target=monitor_main_thread, daemon=True)
    monitor_thread.start()

# Register all cleanup handlers
register_cleanup_handlers()

def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--params",
        action="store",
        default=f"{globalVar.generate_report_enabled},{globalVar.generate_log_file},{globalVar.headless},{globalVar.record_video},{globalVar.product},{globalVar.browser},{globalVar.profile}",
        help="Comma-separated parameters: generate_report_enabled,generate_log_file,headless,record_video,product,browser,profile"
    )
    # New option for marker order
    parser.addoption(
        "--suite-markers",
        action="store",
        default="",
        help="Comma-separated list of markers in the order to execute"
    )

def pytest_configure(config: pytest.Config) -> None:
    params = config.getoption("--params").split(",")
    if len(params) == 7:
        globalVar.generate_report_enabled = params[0].upper()
        globalVar.generate_log_file = params[1].upper()
        globalVar.headless = params[2].upper()
        globalVar.record_video = params[3].upper()
        globalVar.product = params[4].upper()
        globalVar.browser = params[5].upper()
        globalVar.profile = params[6].upper()
    else:
        raise ValueError("Expected 7 parameters: generate_report_enabled,generate_log_file,headless,record_video,product,browser,profile")


@pytest.fixture(scope='session')
def browser(playwright: Playwright):
    log.info('Session start')
    browserValue = globalVar.browser
    if browserValue is None:
        browserValue = "chrome"
    browserValue = browserValue.upper()
    headlesValue = globalVar.headless
    if headlesValue == "N":
        headlesValue = False
        log.info(f'Headless mode: {headlesValue}')
    elif headlesValue == "Y":
        headlesValue = True
        log.info(f'Running session in Headless mode: {headlesValue}')
    else:
        log.error(f"Invalid headless value: {headlesValue}. Defaulting to False.")
        headlesValue = False
    try:
        match browserValue:
            case "CHROME":
                browser = playwright.chromium.launch(
                    headless=headlesValue, 
                    slow_mo=globalVar.slow_motion,
                )
                log.info('Chromium browser launched.')
            case "FIREFOX":
                browser = playwright.firefox.launch(
                    headless=headlesValue, 
                    slow_mo=globalVar.slow_motion,
                )
                log.info('Firefox browser launched.') 
            case _:
                log.error(f"Unsupported browser type: {browserValue}")
                raise ValueError(f"Unsupported browser type: {browserValue}")
        yield browser
    except Exception as e:
        log.error(f"Error during browser setup: {e}")
        raise
    finally:
        browser.close()
        log.info('Session end')

@pytest.fixture(scope='session')
def page(browser: Browser):
    log.info('Page setup')
    if globalVar.record_video == "Y":
        record_video_dir = os.path.join(globalVar.project_root, "Test_Videos")
        context = browser.new_context(record_video_dir=record_video_dir,ignore_https_errors=True,viewport=None)
    else:
        context = browser.new_context(ignore_https_errors=True, viewport=None)
    context.set_default_navigation_timeout(globalVar.default_navigation_timeout)
    context.set_default_timeout(globalVar.default_timeout)
    page = context.new_page()
    try:
        yield page
    except Exception as e:
        log.error(f"Error during page setup: {e}")
        raise
    finally:
        context.close()
        log.info('Page closed')

@pytest.fixture(scope='session')
def report() -> Generator[ExtentReporting, None, None]:
    """Session-scoped fixture for ExtentReporting initialization."""
    config = ReportConfig(
        #test_suite_name=getattr(globalVar, 'test_suite_name', 'TestSuite'),
        generate_report_enabled=getattr(globalVar, 'generate_report_enabled', 'Y'),
        report_path=getattr(globalVar, 'report_path', None),
        generate_log_file=getattr(globalVar, 'generate_log_file', 'Y')
    )
    reporter = ExtentReporting(config)
    yield reporter
    reporter.generate_report()
    log.info('Extent report generated')
        
@pytest.fixture(scope='function', autouse=True)
def test_setup(report: ExtentReporting) -> Generator[None, None, None]:
    reporter = report
    yield
    # End the test using the reporter instance
    try:
        reporter.end_test()
        log.info('Test case ended')
    except Exception as e:
        log.error(f"Error ending test: {e}")

@pytest.hookimpl(tryfirst=True)
def pytest_sessionstart(session):
    profile = globalVar.profile
    profilePath = os.path.join(globalVar.profilePath, f"{profile}.json")
    print(f"Path of the Profile: {profilePath}")
    print(f"Decrypting the Profile {profile}")
    try:
        Security.decrypt_json_file(profilePath) 
        log.info(f"Decrypted the Profile {profile}")  
    except Exception as e:
        log.error(f"Failed to decrypt profile {profilePath}: {str(e)}")
        raise

@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    global _cleanup_performed
    
    # Mark cleanup as performed to prevent duplicate execution by other handlers
    with _cleanup_lock:
        if _cleanup_performed:
            return
        _cleanup_performed = True

    profile = globalVar.profile
    profilePath = os.path.join(globalVar.profilePath, f"{profile}.json")
    print(f"Path of the Profile: {profilePath}")
    print(f"Encrypting the Profile {profile}")
    try:
        if globalVar.exit_handler:
            log.info("Profile Encryption cleanup already performed by exit handler.")
        else:
            log.info("pytest_sessionfinish(): Performing profile encryption cleanup.")
            Security.encrypt_json_file(profilePath)
            log.info(f"pytest_sessionfinish(): Encrypted the Profile {profile}")
            delete_pycache_dirs()
            globalVar.exit_handler = True
    except Exception as e:
        log.error(f"pytest_sessionfinish(): Failed to encrypt profile {profilePath}: {str(e)}")
        raise
    

def delete_pycache_dirs():
    log.info("Cleaning up __pycache__ directories")  
    try:
        if platform.system() == "Windows":
            command = 'Get-ChildItem -Path . -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force'
            subprocess.run(["powershell", "-Command", command], check=True, capture_output=True)
        else:
            command = 'find . -type d -name "__pycache__" -exec rm -rf {} +'
            subprocess.run(command, shell=True, check=True, capture_output=True)
        log.info("Successfully deleted all __pycache__ directories")
    except subprocess.CalledProcessError as e:
        log.error(f"Failed to delete __pycache__ directories: {e.stderr.decode()}")
    except Exception as e:
        log.error(f"Unexpected error during __pycache__ cleanup: {str(e)}")

def pytest_collection_modifyitems(session, config, items):
    # Get the marker order from CLI
    suite_markers_str = config.getoption("--suite-markers")
    if not suite_markers_str:
        return  # no ordering requested
    suite_markers = suite_markers_str.split(",")
    # Define sort key: position in suite_markers list
    def sort_key(item):
        for idx, mark in enumerate(suite_markers):
            if mark in [m.name for m in item.iter_markers()]:
                return idx
        return len(suite_markers)  # tests not in list go last
    items.sort(key=sort_key)