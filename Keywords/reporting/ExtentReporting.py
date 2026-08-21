import base64
from datetime import datetime
import json
from sqlalchemy import create_engine ,text
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging
import html
import os
from jinja2 import Environment, FileSystemLoader
from dataclasses import dataclass, field
from typing import TypeVar, Generic
import Keywords.projectVariables as globalVar
import sys
project_root = os.getcwd()
sys.path.append(project_root)
import pytest
import oracledb
T = TypeVar('T')

@dataclass
class TestStep:
    step_number: int
    status: str
    message: str
    timestamp: str
    screenshot_data: Optional[str] = None
    is_full_page: bool = False

@dataclass
class TestCase:
    name: str
    description: str
    marker: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[str] = None
    results: Dict[str, int] = field(default_factory=lambda: {"PASS": 0, "FAIL": 0, "SKIP": 0, "INFO": 0, "WARNING": 0})
    steps: List[TestStep] = field(default_factory=list)

@dataclass
class ReportConfig:
    report_path: Optional[str] = None
    auto_screenshot: str = 'N'  # 'Y' or 'N' instead of True/False
    test_suite_name: str = "TestExecutionReport"
    generate_report_enabled: str = globalVar.generate_report_enabled  # 'Y' or 'N'
    template_path: Optional[str] = "Keywords/reporting/templates"
    logs_dir_name: str = "Logs"
    reports_dir_name: str = "ExtentReports"
    generate_log_file: str = globalVar.generate_log_file  # 'Y' or 'N'

class ScreenshotManager:
    @staticmethod
    def capture_screenshot(page: T, full_page: bool = False, save_path: str = None, masked_fld: List[str] = None, table_selectors: dict = None) -> Optional[str]:
        """Capture a screenshot from the given page and save it to the Screenshots folder."""
        mask_locators= []
        blur_flag = "Y"
        if not page:
            logging.error("Page object cannot be None")
            return None
        try:
            page.wait_for_load_state("networkidle")
            if globalVar.mask_bydefault_enabled.upper() == 'Y':
                ScreenshotManager.mask_bydefault(page)
            field_locators = ScreenshotManager.mask_explicitly(page, masked_fld, table_selectors)
            #Adding code for PROJECT product.
            if ExtentReporting.mask_type.lower() == "blur":
                key_locator = ScreenshotManager.mask_explicitly(page, locators=ExtentReporting.locator_to_mask)
                mask_locators.extend(field_locators)
                mask_locators.extend(key_locator)
            elif ExtentReporting.mask_type.lower() == "mask":
                mask_locators.extend(field_locators)
                mask_locators.extend(ExtentReporting.locator_to_mask)
                ScreenshotManager.mask_keyworddriven(page, mask_locators)
                blur_flag ="N"
            elif ExtentReporting.mask_type.lower() == "both":
                #blur code
                key_locator = ScreenshotManager.mask_explicitly(page, locators=ExtentReporting.locator_to_mask)
                mask_locators.extend(field_locators)
                mask_locators.extend(key_locator)
                #mask code
                ScreenshotManager.mask_keyworddriven(page, field_locators)
                ScreenshotManager.mask_keyworddriven(page, ExtentReporting.locator_to_mask)
            else:
                logging.warning(f"Invalid mask type '{ExtentReporting.mask_type}'")    
            if blur_flag == "Y":
                screenshot_bytes = page.screenshot(
                    full_page=full_page,
                    type="png",
                    animations="disabled",
                    mask= mask_locators,
                    mask_color = "grey"  
                )
            else:
                screenshot_bytes = page.screenshot(
                    full_page=full_page,
                    type="png",
                    animations="disabled"
                )
            ScreenshotManager.restore_og_value(page)
            if save_path:
                with open(save_path, 'wb') as f:
                    f.write(screenshot_bytes)
            return base64.b64encode(screenshot_bytes).decode('utf-8')
        except Exception as e:
            logging.exception(f"Failed to capture screenshot: {e}")
            # Try one more time with minimal options
            try:
                logging.info("Attempting screenshot with minimal options...")
                screenshot_bytes = page.screenshot(
                    full_page=False,
                    type="png",
                    timeout=15000  # 15 seconds timeout for retry
                )
                if save_path:
                    with open(save_path, 'wb') as f:
                        f.write(screenshot_bytes)
                logging.info("Screenshot captured successfully with minimal options")
                return base64.b64encode(screenshot_bytes).decode('utf-8')
            except Exception as retry_error:
                logging.error(f"Failed to capture screenshot even with minimal options: {retry_error}")
                return None

    #Function for bluring locator's explicitly.
    def mask_explicitly(page: T, locators: List[str] = None, table_selectors: dict = None) -> List:
        """
        Converts user-provided selector strings into Playwright locators for screenshot masking.
        Optionally masks all cells in the given column name(s) for each table in table_selectors.
        """
        selectors = list(locators) if locators else []
        user_name_selector = f"//*[contains(text(),'{globalVar.user_name}')]"
        selectors.append(user_name_selector)
        if table_selectors:
            for table_selector, mask_column_names in table_selectors.items():
                # Ensure mask_column_names is a list
                if isinstance(mask_column_names, str):
                    mask_column_names = [mask_column_names]
                try:
                    header_cells = page.locator(f"{table_selector} thead tr th")
                    col_count = header_cells.count()
                    for mask_column_name in mask_column_names:
                        col_index = None
                        for i in range(col_count):
                            header_text = header_cells.nth(i).inner_text().strip()
                            if mask_column_name.lower() in header_text.lower():
                                col_index = i + 1  # nth-child is 1-based
                                break
                        if col_index:
                            col_selector = f"{table_selector} tbody tr td:nth-child({col_index})"
                            selectors.append(col_selector)
                except Exception as e:
                    pass
        return [page.locator(selector) for selector in selectors if isinstance(selector, str)] 
     
    #Function for masking by default values,
    # Avoids hidden fields, mask data with storing og value thru injecting attribute
    def mask_bydefault(page: T):
        airline_code = globalVar.iss_airline_code
        username = globalVar.user_name
        page.evaluate(
            """
            ({ airlineCode, userName }) => {
                // Regex: mask airline code ONLY if not glued to letters/digits
                const airlinePattern = new RegExp(
                    `(?<![A-Za-z0-9])${airlineCode}(?![A-Za-z0-9])`,
                    'g'
                );
                const escape = s =>
                    typeof s === 'string'
                        ? s.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&')
                        : '';
                const usernamePattern = new RegExp(
                    `(^|[^A-Za-z0-9])${escape(userName)}([^A-Za-z0-9]|$)`,
                    'gi'
                );
                // -------- TEXT NODES (td, span, div, etc.) --------
                const walker = document.createTreeWalker(
                    document.body,
                    NodeFilter.SHOW_TEXT,
                    null,
                    false
                );
                let node;
                while (node = walker.nextNode()) {
                    const parent = node.parentElement;
                    if (!parent) continue;
                    let text = node.nodeValue;
                    if (!text || text.includes('****')) continue;
                    // Reset regex state
                    airlinePattern.lastIndex = 0;
                    usernamePattern.lastIndex = 0;
                    if (airlinePattern.test(text) || usernamePattern.test(text)) {
                        // Store original full visible content once
                        if (!parent.hasAttribute('og_val')) {
                            parent.setAttribute('og_val', parent.textContent);
                        }
                        airlinePattern.lastIndex = 0;
                        usernamePattern.lastIndex = 0;
                        text = text.replace(airlinePattern, '****');
                        text = text.replace(usernamePattern, '****');
                        node.nodeValue = text;
                    }
                }
                // -------- INPUT & TEXTAREA --------
                document.querySelectorAll('input:not([type="hidden"]), textarea')
                    .forEach(el => {
                        if (!el.value || el.value.includes('****')) return;
                        airlinePattern.lastIndex = 0;
                        usernamePattern.lastIndex = 0;
                        if (airlinePattern.test(el.value) || usernamePattern.test(el.value)) {
                            // Store original once
                            if (!el.hasAttribute('og_val')) {
                                el.setAttribute('og_val', el.value);
                            }
                            airlinePattern.lastIndex = 0;
                            usernamePattern.lastIndex = 0;
                            el.value = el.value
                                .replace(airlinePattern, '****')
                                .replace(usernamePattern, '****');
                            // Trigger framework-safe update
                            el.dispatchEvent(new Event('input', { bubbles: true }));
                        }
                    });
            }
            """,
            {
                "airlineCode": airline_code,
                "userName": username
            }
        )

    #Function for masking/bluring locator's thru keyword driven.
    def mask_keyworddriven(page: T, locator_list: List[str] = None):
        # Ensure page is fully loaded
        page.wait_for_load_state("domcontentloaded")
        page.evaluate(
            """
            (locators) => {
                locators.forEach(xpath => {
                    const element = document.evaluate(
                        xpath,
                        document,
                        null,
                        XPathResult.FIRST_ORDERED_NODE_TYPE,
                        null
                    ).singleNodeValue;

                    if (!element) return;

                    // Case 1: Element has value attribute (inputs, textareas)
                    if (element.hasAttribute("value")) {
                        // Store original value once
                        if (!element.hasAttribute("og_val")) {
                            element.setAttribute("og_val", element.value);
                        }
                        element.value = "****";
                        element.dispatchEvent(new Event('input', { bubbles: true }));
                    }
                    // Case 2: Element has text content
                    else if (element.textContent && element.textContent.trim() !== "") {
                        // Store original text content once
                        if (!element.hasAttribute("og_val")) {
                            element.setAttribute("og_val", element.textContent);
                        }
                        element.textContent = "****";
                    }
                });
            }
            """,
            locator_list
        )

    #Restore the mask value back to original value.
    def restore_og_value(page: T):
        page.evaluate(
            """
            () => {
                // Find all elements having original value stored
                document.querySelectorAll('[og_val]').forEach(el => {
                    const original = el.getAttribute('og_val');
                    const tag = el.tagName.toUpperCase();
                    // Restore based on element type
                    if (tag === 'INPUT' || tag === 'TEXTAREA') {
                        el.value = original;
                        // Trigger input event (important for React/Angular apps)
                        el.dispatchEvent(new Event('input', { bubbles: true }));
                    } else {
                        el.textContent = original;
                    }
                    // Cleanup attribute after restore
                    el.removeAttribute('og_val');
                });
            }
            """
        )


class ElementVerifier:
    
    @staticmethod
    def scrollTo_Element(page: T, selector: str) -> None:
        """Scroll to the specified element."""
        if not page:
            logging.error("Page object cannot be None")
            return
        try:
            locator = page.locator(selector)
            if locator.count() > 0:
                locator.first.scroll_into_view_if_needed()
                #locator.first.evaluate("el => window.scrollBy(0, -100)")
        except Exception as e:
            logging.error(f"Exception while scrolling to element {selector}: {e}")
    
    @staticmethod
    def verify_text(page: T, element_name: str, selector: str, expected_text: str, 
                   case_sensitive: bool = False) -> tuple[bool, str]:
        """Verify text content of an element. Returns (result, actual_text) tuple."""
        if not page:
            logging.error("Page object cannot be None")
            return False, ""
        try:
            # Scroll to element for better interaction
            ElementVerifier.scrollTo_Element(page, selector)

            locator = page.locator(selector)
            if locator.count() == 0:
                logging.warning(f"Element '{element_name}' with selector '{selector}' not found.")
                actual_text = ""
            else:
                actual_text = locator.first.inner_text().strip()
            expected_text = expected_text.strip()
            if case_sensitive:
                result = actual_text == expected_text
            else:
                result = actual_text.lower() == expected_text.lower()
            if not result:
                logging.info(f"Text verification failed for '{element_name}':\n Actual: '{actual_text}',\n Expected: '{expected_text}'")
            return result, actual_text
        except Exception as e:
            logging.exception(f"Failed to verify {element_name} text: {str(e)}")
            return False, ""
    
    @staticmethod
    def verify_attribute(page: T, element_name: str, selector: str, attribute_name: str, 
                     expected_value: str, timeout: int = 30000) -> tuple[bool, str]:
        """Verify an attribute value of an element. Returns (result, actual_value) tuple."""
        try:
            if not page:
                raise ValueError("Page object cannot be None")
            # Scroll to element for better interaction
            ElementVerifier.scrollTo_Element(page, selector)
            locator = page.locator(selector)
            if locator.count() == 0:
                logging.warning(f"Element '{element_name}' with selector '{selector}' not found.")
                actual_value = ""
                result = False
            else:
                actual_value = locator.first.get_attribute(attribute_name) or ""
                actual_value = actual_value.strip() if actual_value else ""
                expected_value = expected_value.strip()
                result = actual_value.lower() == expected_value.lower()
            if not result:
                logging.info(f"Attribute verification failed for '{element_name}':\n Actual: '{actual_value}',\n Expected: '{expected_value}'")
            return result, actual_value
        except Exception as e:
            logging.error(f"Failed to verify {element_name} attribute {attribute_name}: {str(e)}")
            return False, ""

class TemplateRenderer:
    def __init__(self, template_path: Path):
        self.template_path = template_path
        self.env = Environment(loader=FileSystemLoader(self.template_path))

    def render_report(self, template_data: Dict[str, Any]) -> str:
        """Render the HTML report using Jinja2 template."""
        template = self.env.get_template('extent_report_template.html')
        return template.render(**template_data)

class ExtentReporting(Generic[T]):
    locator_to_mask: List[str] = []
    mask_type: str = "both"
    
    def __init__(self, config: ReportConfig):
        self.config = config
        self.step_counter: int = 1
        self.current_test_case_name: str = ""
        self.current_test_case_description: str = ""
        self.author: str = os.environ.get("USERNAME", "AUTOMATION")
        self.current_marker: str = ""
        self.current_start_time: Optional[datetime] = None
        self.current_end_time: Optional[datetime] = None
        self.overall_start_time: datetime = datetime.now()
        self.overall_end_time: Optional[datetime] = None
        self.current_test_results: Dict[str, int] = {"PASS": 0, "FAIL": 0, "SKIP": 0, "INFO": 0, "WARNING": 0}
        self.overall_test_results: Dict[str, int] = {"PASS": 0, "FAIL": 0, "SKIP": 0, "INFO": 0, "WARNING": 0}
        self.test_cases: Dict[str, TestCase] = {}
        self.page: Optional[T] = None
        self.tc_flag = False
        self.mask_fields: List[str] = []
        self.mask_table: dict = {}
        self.base_path = Path(config.report_path) if config.report_path else Path.cwd()
        self.template_path = Path(config.template_path) if config.template_path else self.base_path / "templates"
        self.reports_dir = self.base_path / config.reports_dir_name
        self.logs_dir = self.base_path / config.logs_dir_name
        self.screenshots_dir = self.base_path.parent / 'Screenshots'
        
        self._create_directories()
        self._setup_logging()
        self.template_renderer = TemplateRenderer(self.template_path)
        self.get_env_detail()

    def get_env_detail(self):
        """
        Fetch environment details from the configured database.

        If the database connection or query execution fails, the exception is
        handled safely and automation execution continues.
        """
        # Initialize default values
        globalVar.iss_airline_code = None
        globalVar.user_name = None
        try:
            # ---------------------------------------------------------
            # 1. Get environment/profile details
            # ---------------------------------------------------------
            environment = globalVar.profile
            env_path = os.path.join(globalVar.profilePath,f"{environment}.json")

            if not os.path.exists(env_path):
                logging.warning(f"Environment profile not found: {env_path}. " f"Continuing automation execution.")
                return

            with open(env_path, "r", encoding="utf-8") as file:
                profile = json.load(file)

            db_type = profile.get("dbType", "").lower()
            app_username = profile.get("app_username")
            db_username = profile.get("dbusername")
            db_password = profile.get("dbpassword")
            host = profile.get("host")
            port = profile.get("port")
            service_name = profile.get("dbName")

            # ---------------------------------------------------------
            # 2. Validate mandatory database configuration
            # ---------------------------------------------------------
            required_fields = {
                "dbType": db_type,
                "dbusername": db_username,
                "dbpassword": db_password,
                "host": host,
                "port": port,
                "dbName": service_name,
            }

            missing_fields = [
                field
                for field, value in required_fields.items()
                if value in (None, "")
            ]

            if missing_fields:
                logging.warning(
                    f"Database configuration is incomplete. "
                    f"Missing fields: {', '.join(missing_fields)}. "
                    f"Continuing automation execution."
                )
                return

            # ---------------------------------------------------------
            # 3. SQL queries
            # ---------------------------------------------------------
            sql_airline_code = "SELECT default_airline_code FROM install_tab"
            sql_username = "SELECT full_name FROM tmwss_user WHERE user_name = :app_username"

            # ---------------------------------------------------------
            # 4. Initialize Oracle client if required
            # ---------------------------------------------------------
            if db_type == "oracle":
                oracledb.init_oracle_client(lib_dir=None)
            # ---------------------------------------------------------
            # 5. Create database connection URL
            # ---------------------------------------------------------
            if db_type == "postgres":
                db_url = URL.create(
                    drivername="postgresql+psycopg2",
                    username=db_username,
                    password=db_password,
                    host=host,
                    port=port,
                    database=service_name,
                )

            elif db_type == "oracle":
                db_url = URL.create(
                    drivername="oracle+oracledb",
                    username=db_username,
                    password=db_password,
                    host=host,
                    port=port,
                    query={"service_name": service_name},
                )

            elif db_type == "mariadb":
                db_url = URL.create(
                    drivername="mysql+pymysql",
                    username=db_username,
                    password=db_password,
                    host=host,
                    port=port,
                    database=service_name,
                )
            else:
                logging.warning(
                    f"Unsupported database type: '{db_type}'. "
                    f"Continuing automation execution."
                )
                return
        # ---------------------------------------------------------
        # 6. Create database engine
        # ---------------------------------------------------------
            engine = create_engine(db_url,pool_pre_ping=True)
            # ---------------------------------------------------------
            # 7. Connect to database and execute queries
            # ---------------------------------------------------------
            with engine.connect() as conn:
                tmwss_users = conn.execute(
                    text(sql_username),
                    {
                        "app_username": app_username
                    }
                ).scalar_one_or_none()
                install_tabs = conn.execute(text(sql_airline_code)).scalar_one_or_none()
            # ---------------------------------------------------------
            # 8. Store values in global variables
            # ---------------------------------------------------------
            globalVar.iss_airline_code = install_tabs
            globalVar.user_name = tmwss_users
            logging.info(
                f"Database details fetched successfully. "
                f"Airline Code: {install_tabs}, "
                f"User Name: {tmwss_users}"
            )
        except Exception as e:
            # ---------------------------------------------------------
            # 9. Handle database/profile/SQL failure safely
            # ---------------------------------------------------------
            globalVar.iss_airline_code = None
            globalVar.user_name = None
            logging.warning(
                "Database connection could not be established. "
                "Continuing automation execution."
            )
            logging.debug(f"Database error details: {e}",exc_info=True)
            return

    def _create_directories(self) -> None:
        try:
            self.reports_dir.mkdir(parents=True, exist_ok=True)
            self.logs_dir.mkdir(parents=True, exist_ok=True)
            self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logging.error(f"Failed to create directories: {e}")
            raise

    def _setup_logging(self) -> None:
        try:
            logging.getLogger().handlers = []
            handlers = []
            if self.config.generate_log_file == 'Y':
                log_file = self.logs_dir / f"test_execution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
                file_handler = logging.FileHandler(log_file, encoding='utf-8')
                handlers.append(file_handler)
            console_handler = logging.StreamHandler()
            handlers.append(console_handler)
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=handlers
            )
            logging.info("Logging system initialized successfully")
            if self.config.generate_log_file == 'Y':
                logging.info(f"Log file will be saved to: {log_file}")
                for handler in logging.getLogger().handlers:
                    if isinstance(handler, logging.FileHandler):
                        handler.flush()
        except Exception as e:
            print(f"CRITICAL: Failed to setup logging: {e}")
            raise

    def start_test(self, test_case_name: str, 
                  test_case_description: str,
                  marker: str = "General") -> None:
        self.current_test_case_name = test_case_name
        self.current_test_case_description = test_case_description
        self.current_marker = marker
        self.current_start_time = datetime.now()
        self.step_counter = 1
        self.current_test_results = {"PASS": 0, "FAIL": 0, "SKIP": 0, "INFO": 0, "WARNING": 0}
        self.test_cases[test_case_name] = TestCase(
            name=test_case_name,
            description=test_case_description,
            marker=marker,
            start_time=self.current_start_time
        )
        logging.info(f"Started test: {test_case_name}")

    def set_page(self, page: T =None) -> None:
        self.page = page

    def test_status(self, status: str, message: str, take_screenshot: str = None, full_page: str = 'N') -> None:
        if status not in ["PASS", "FAIL", "SKIP", "INFO", "WARNING"]:
            raise ValueError("status must be one of: PASS, FAIL, SKIP, INFO, WARNING")
        if not self.current_test_case_name:
            raise RuntimeError("No active test case. Call start_test() first.")
        if take_screenshot is None:
            take_screenshot = self.config.auto_screenshot
        self.current_test_results[status] += 1
        self.test_cases[self.current_test_case_name].results[status] += 1
        timestamp = datetime.now().strftime('%H:%M:%S')
        screenshot_data = None
        screenshot_file_path = None
        if take_screenshot == 'Y' and self.page:
            # Get test case specific directory using the name from start_test
            test_case_screenshots_dir = self.get_test_case_screenshot_dir()
            timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            screenshot_file_path = test_case_screenshots_dir / f"step{self.step_counter}_{timestamp_str}.png"
            screenshot_data = ScreenshotManager.capture_screenshot(self.page, full_page == 'Y', str(screenshot_file_path),masked_fld=self.mask_fields, table_selectors=self.mask_table)
        step = TestStep(
            step_number=self.step_counter,
            status=status,
            message=message,
            timestamp=timestamp,
            screenshot_data=screenshot_data,
            is_full_page=(full_page == 'Y')
        )
        self.test_cases[self.current_test_case_name].steps.append(step)
        self.step_counter += 1
        log_message = f"Step {self.step_counter-1} - {status}: {message}"
        if status == "PASS":
            logging.info(log_message)
        elif status == "FAIL":
            self.tc_flag = True
            logging.error(log_message)
        elif status == "SKIP":
            logging.warning(log_message)
        else:
            logging.info(log_message)

    def test_info(self, message: str, take_screenshot: str = None) -> None:
        self.test_status("INFO", message, take_screenshot=take_screenshot)
        
    def explicitCaptureSS(self, message: str, fullSSFlag: str = None) -> None:
        self.test_status("INFO", message, take_screenshot='Y', full_page=fullSSFlag)

    def capture_screenshot(self, full_page: str = 'N') -> Optional[str]:
        if not self.page:
            logging.exception("Page object cannot be None")
            raise ValueError("Page object cannot be None")
        
        # Get screenshot directory based on current test case
        if self.current_test_case_name:
            screenshot_dir = self.get_test_case_screenshot_dir()
        else:
            screenshot_dir = self.screenshots_dir
            
        screenshot_file_path = screenshot_dir / f"manual_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        return ScreenshotManager.capture_screenshot(self.page, full_page == 'Y', str(screenshot_file_path),masked_fld=self.mask_fields, table_selectors=self.mask_table)

    def verify_text_and_log_status(self, element_name: str, selector: str, expected_text: str, 
                                    take_screenshot: str = None, case_sensitive: bool = False) -> bool:
        try:
            if not self.page:
                raise ValueError("Page object cannot be None")
            # Use tuple return from verify_text to avoid race condition
            match, actual_text = ElementVerifier.verify_text(self.page, element_name, selector, expected_text, case_sensitive= False)
            message = f"Verify {element_name} text<br> Actual: \"{actual_text}\"<br> Expected: \"{expected_text}\""
            status = "PASS" if match else "FAIL"
            self.test_status(status, message, take_screenshot)
            return match
        except Exception as e:
            error_message = f"Failed to verify {element_name} text: {str(e)}"
            self.test_status("FAIL", error_message, take_screenshot)
            logging.exception(error_message)
            return False

    def verify_element_attribute_value(self, element_name: str, selector: str, attribute_name: str, expected_value: str, timeout: int = 30000, take_screenshot: str = None) -> bool:
        try:
            if not self.page:
                raise ValueError("Page object cannot be None")
            
            # Use tuple return from verify_attribute to avoid race condition
            match, actual_value = ElementVerifier.verify_attribute(self.page, element_name, selector, attribute_name, expected_value, timeout)
            
            message = f"Verify {element_name} {attribute_name} attribute<br> Actual: \"{actual_value}\"<br> Expected: \"{expected_value}\""
            status = "PASS" if match else "FAIL"
            self.test_status(status, message, take_screenshot)
            return match
        except Exception as e:
            error_message = f"Failed to verify {element_name} attribute {attribute_name}: {str(e)}"
            self.test_status("FAIL", error_message, take_screenshot)
            logging.exception(error_message)
            return False

    def compare_text(self, actual_value: Any, expected_value: Any, description: str, take_screenshot: str = None,masking:str ="N") -> bool:
        actual_value = str(actual_value).strip() if actual_value is not None else ""
        expected_value = str(expected_value).strip() if expected_value is not None else ""
        match = actual_value.lower() == expected_value.lower()
        message=""
        if masking.upper() == "Y":
            message = f"Compare {description}<br> Actual: \"****\"<br> Expected: \"****\""
        else:
            message = f"Compare {description} <br> Actual: \"{actual_value}\"<br> Expected: \"{expected_value}\""
        status = "PASS" if match else "FAIL"
        self.test_status(status, message, take_screenshot)
        if status == "FAIL":
            if masking.upper() == "Y":
                logging.error(f"Comparison failed: {description}\n Actual: \"****\"\n Expected: \"****\"")
            else:
                logging.error(f"Comparison failed: {description}\n Actual: \"{actual_value}\"\n Expected: \"{expected_value}\"")
        return match

    def end_test(self) -> None:
        if not self.current_start_time:
            raise RuntimeError("Test was not started. Call start_test() first.") 
        self.current_end_time = datetime.now()
        duration = self.current_end_time - self.current_start_time
        print(f'End time: {self.current_end_time} , Duration: {duration}')   
        logging.info(f"Ending test: {self.current_test_case_name} at {self.current_end_time}, Duration: {duration}")
        test_case = self.test_cases[self.current_test_case_name]
        test_case.end_time = self.current_end_time
        test_case.duration = str(duration).split('.')[0]
        logging.info(f"Test completed: {self.current_test_case_name}")
        if self.tc_flag:
            self.tc_flag = False
            pytest.fail(f"Test case '{self.current_test_case_name}' failed. Check report for details.", pytrace=False)

    def generate_report(self) -> str:
        if self.config.generate_report_enabled != 'Y':
            logging.info("Report generation is disabled. Skipping report generation.")
            return ""
        self.overall_end_time = datetime.now()
        overall_duration = self.overall_end_time - self.overall_start_time
        # Calculate overall test results
        self.overall_test_results = {"PASS": 0, "FAIL": 0, "SKIP": 0, "INFO": 0, "WARNING": 0}
        for tc_data in self.test_cases.values():
            if tc_data.results.get('FAIL', 0) > 0:
                self.overall_test_results["FAIL"] += 1
            else:
                self.overall_test_results["PASS"] += 1
            self.overall_test_results["SKIP"] += tc_data.results.get("SKIP", 0)
            self.overall_test_results["INFO"] += tc_data.results.get("INFO", 0)
            self.overall_test_results["WARNING"] += tc_data.results.get("WARNING", 0)

        # Fixed pass rate calculation - only consider PASS and FAIL in denominator
        total_test_cases = self.overall_test_results["PASS"] + self.overall_test_results["FAIL"]
        pass_rate = (self.overall_test_results["PASS"] / total_test_cases * 100) if total_test_cases > 0 else 0        
        
        status_colors = {
            'PASS': 'green',
            'FAIL': 'red',
            'SKIP': 'yellow',
            'INFO': 'blue',
            'WARNING': 'orange'
        }
        unique_markers = []
        for tc_name, tc_data in self.test_cases.items():
            if tc_data.marker and tc_data.marker != "General":
                unique_markers.append(tc_data.marker)
            else:
                unique_markers.append(tc_name)
        unique_markers = list(set(unique_markers))
        unique_markers.sort()
        template_data = {
            'overall_start_time': self.overall_start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'overall_end_time': self.overall_end_time.strftime('%Y-%m-%d %H:%M:%S'),
            'overall_duration': str(overall_duration).split('.')[0],
            'total_test_cases': len(self.test_cases),
            'overall_test_results': self.overall_test_results,
            'total_steps': total_test_cases,  # Changed to total_test_cases for clarity
            'author': self.author,
            'pass_rate': f"{pass_rate:.1f}",
            'test_cases': [],
            'status_colors': status_colors,
            'suite_name': self.config.test_suite_name,
            'unique_markers': unique_markers
        }
        # Populate test_cases for the template
        for tc_name, tc_data in self.test_cases.items():
            tc_total_steps = tc_data.results.get('PASS', 0) + tc_data.results.get('FAIL', 0)
            tc_pass_rate = (tc_data.results.get('PASS', 0) / tc_total_steps * 100) if tc_total_steps > 0 else 0
            test_case_id = html.escape(tc_name).replace(' ', '_')
            test_case_data = {
                'name': tc_name,
                'safe_name': test_case_id,
                'description': html.escape(tc_data.description),
                'marker': html.escape(tc_data.marker),
                'start_time': tc_data.start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'end_time': tc_data.end_time.strftime('%Y-%m-%d %H:%M:%S') if tc_data.end_time else 'N/A',
                'duration': tc_data.duration or 'N/A',
                'results': tc_data.results,
                'pass_rate': f"{tc_pass_rate:.1f}",
                'steps': []
            }
            for step in tc_data.steps:
                step_data = {
                    'step_number': step.step_number,
                    'status': step.status,
                    'message': html.escape(step.message).replace('\n', '').replace('&lt;br&gt;', '<br>'),
                    'timestamp': step.timestamp,
                    'screenshot_data': step.screenshot_data,
                    'color': status_colors.get(step.status, 'gray'),
                    'is_full_page': step.is_full_page
                }
                test_case_data['steps'].append(step_data)
            template_data['test_cases'].append(test_case_data)
        html_content = self.template_renderer.render_report(template_data)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = self.reports_dir / f"{self.config.test_suite_name}_{timestamp}.html"
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logging.info(f"Report generated successfully: {report_path}")
            return str(report_path)
        except Exception as e:
            logging.error(f"Failed to save report: {e}")
            return ""

    def get_test_case_screenshot_dir(self) -> Path:
        """
        Creates and returns a test case-specific screenshot directory based on the current test case name.
        Uses the test case name that was set during start_test().
        """
        if not self.current_test_case_name:
            logging.warning("No active test case. Using general screenshot directory.")
            return self.screenshots_dir
        
        # Replace invalid characters for filesystem paths
        safe_test_case_name = self.current_test_case_name.replace('/', '_').replace('\\', '_') \
                                                  .replace(':', '_').replace('*', '_') \
                                                  .replace('?', '_').replace('"', '_') \
                                                  .replace('<', '_').replace('>', '_') \
                                                  .replace('|', '_')
        
        test_case_screenshots_dir = self.screenshots_dir / safe_test_case_name
        test_case_screenshots_dir.mkdir(parents=True, exist_ok=True)
        return test_case_screenshots_dir