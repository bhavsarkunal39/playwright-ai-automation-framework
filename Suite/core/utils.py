import os
import sys

def create_junit_directory():
    """Create JUnit reports directory"""
    junit_dir = os.path.join("Test_Reports", "JUnit_Reports")
    os.makedirs(junit_dir, exist_ok=True)
    return junit_dir

def prepare_pytest_args(config, junit_file, generate_report, generate_log_file, headless_mode, record_video, product):
    """Prepare pytest arguments with marker validation"""
    valid_markers = [marker for marker in config['markers'] if marker and marker.strip()]
    if not valid_markers:
        raise ValueError(f"No valid markers found in config: {config['markers']}")
    
    markers_str = ",".join(valid_markers)
    params = f"{generate_report},{generate_log_file},{headless_mode},{record_video},{product},{config['browser']},{config['profile']}"
    
    return [
        sys.executable, "-m", "pytest",
        "--log-cli-level=INFO",
        "-m", " or ".join(valid_markers),
        "--disable-pytest-warnings",
        "--continue-on-collection-errors",
        f"--junitxml={junit_file}",
        "--capture=no" if config['thread_id'] else "--capture=tee-sys",
        "--tb=long",
        f"--suite-markers={markers_str}",
        f"--params={params}",
        "."
    ]

def create_environment(config, generate_report, generate_log_file, headless_mode, record_video, product):
    """Create environment variables for subprocess"""
    env = os.environ.copy()
    env.update({
        'PROFILE': config['profile'],
        'BROWSER': config['browser'],
        'PRODUCT': product,
        'GENERATE_REPORT': generate_report,
        'GENERATE_LOG_FILE': generate_log_file,
        'HEADLESS_MODE': headless_mode,
        'RECORD_VIDEO': record_video,
        'THREAD_ID': str(config['thread_id']) if config['thread_id'] else '0'
    })
    return env

def extract_test_summary(output):
    """Extract test summary from pytest output"""
    if not output:
        return "No output available"
    
    lines = output.split('\n')
    for line in reversed(lines):
        if any(keyword in line.lower() for keyword in ['passed', 'failed', 'error', 'deselected', 'warnings']) and '==' in line:
            return line.strip()
    
    for line in reversed(lines):
        if 'passed' in line.lower() or 'failed' in line.lower():
            return line.strip()
    
    return "Summary not available"