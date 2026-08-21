# Pybot

**Pybot** is a hybrid, keyword-driven QA automation framework built with **Python** and **Playwright**, developed by the QA team at **Accelya**.

## Overview

Pybot provides a robust, scalable solution for automating UI and API tests. It combines the simplicity of keyword-driven testing with the power of Playwright's modern automation capabilities. The framework is designed to make test creation intuitive for QA engineers of all skill levels while maintaining flexibility for complex test scenarios.

## Features
- Keyword-driven and hybrid test logic
- Page Object Model (POM) structure
- Parallel and cross-browser execution (Chromium, Firefox, WebKit)
- API and UI automation support
- Built-in HTML reporting and logging
- Environment and profile management
- Screenshots and video recording
- Customizable keyword libraries
- Continuous Integration friendly

## Directory Structure
playwright-ai-automation-framework/
├── Keywords/           # Keyword libraries and reusable functions
├── Object_Repository/  # Page locators and element definitions
├── Profiles/           # Encrypted environment profiles
├── Suite/              # Test suite runners and configuration
├── Test_Cases/         # Individual test case files
├── Test_Reports/       # Generated test reports and logs
├── Test_Videos/        # Video recordings of test runs
├── Utility/            # Utility scripts and helpers
├── Data_Files/         # Input/output data files
├── conftest.py         # Pytest fixtures and hooks
├── pytest.ini          # Pytest configuration
├── requirements.txt    # Python dependencies
└── README.md           # Project documentation

## Pre-requisites:
1. Download and install Microsoft Build Tools: 
>Link: https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. Download oracle instant client: 
>Link: https://www.oracle.com/in/database/technologies/instant-client/winx64-64-downloads.html
   2.1 Extract the folder and keep the extracted folder into c:/oracle/
   2.2 Set the path into System Environment variables.


## Getting Started
### 1. Clone the repository
```bash
git clone https://your-git-url/playwright-ai-automation-framework.git

checkout the feature branch
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
playwright install
```

### 3. Creating Testcases:
1. Create a Python file with .py extension under the Tests folder.
2. Inside the empty .py file type 'import UI TC' and click on the option displayed. 
   (It will import the testcase template with required import libraries)
3. Start writing testcases following these conventions:
   - For custom keywords use 'key.' prefix, e.g. `customkey.login()`
   - For playwright keywords use 'page.' prefix, e.g. `page.click()`

Example test case:
```python
# Import required libraries
from Lib.base import *

class TestLogin(Base):
    def test_valid_login(self):
        # Initialize page and keywords
        key.navigate_to_login_page()
        key.login_with_credentials("validUser", "validPass")
        key.verify_login_success()
```

### 4. Test Suite Creation:
1. Add tests into the RunTestsuite.py file.

### 5. Test Execution:
```bash
# Run a specific test
python -m Tests.test_login

# Run a test suite
python -m Suite.US12345

# Run with specific environment
python -m Suite.US12345 --env=staging
```

### 6. Viewing Reports:
After test execution, reports can be found in the Reports directory.

### 7. Cleaning up __pycache__ folders:
Use this command on terminal:
```bash
Get-ChildItem -Path . -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
```
### 8. git Command for skipping unneeded file changes to get pushed into git.
git update-index --skip-worktree Profiles/PROJECT/*.json 

## Configuration

Environment configurations are stored in the Config directory. To switch environments, use the `--env` parameter during test execution or modify the default environment in `Config/settings.py`.

## Contributing

1. Create a feature branch from `develop`
2. Make your changes
3. Submit a pull request to `develop`
4. Ensure all tests pass before merging

## License

This project is proprietary software owned by KUNAL B.

## Support

For support, contact the KUNAL B.