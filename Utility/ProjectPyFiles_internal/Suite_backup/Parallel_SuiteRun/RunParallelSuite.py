# RunAllSuites_parallel.py
suites = [
        "RunTestsuite.py",
        "RunTestsuite_2.py"
    ]

#---------------------------------------------------------------------
#--------------------------------------------------------------------







import subprocess
import sys
import threading
import os
from pathlib import Path
def run_suite(suite_file):
    print(f"Starting suite: {suite_file}")
    # Extract suite name without extension for environment variable
    suite_name = Path(suite_file).stem
    # Create isolated environment for this subprocess
    env = os.environ.copy()
    env['PYTEST_SUITE_NAME'] = suite_name
    # Navigate to Suite directory for subprocess
    suite_path = f"Suite/{suite_file}"
    print(f"Setting PYTEST_SUITE_NAME={suite_name} for {suite_file}")
    # Run subprocess with isolated environment
    subprocess.run([sys.executable, suite_path], env=env)

if __name__ == "__main__":
    import os
    import sys
    import subprocess
    project_root = os.getcwd()
    sys.path.append(project_root)
    threads = []
    print("Starting parallel suite execution...")
    for suite in suites:
        t = threading.Thread(target=run_suite, args=(suite,))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()
    print("\n All suites completed!")