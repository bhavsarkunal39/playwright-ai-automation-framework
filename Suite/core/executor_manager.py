import time
import threading
import subprocess
import os
from .utils import create_junit_directory, prepare_pytest_args, create_environment, extract_test_summary

def run_single_execution(config, generate_report, generate_log_file, headless_mode, record_video, product):
    """Run single execution using pytest.main()"""
    print("🔹 Single execution mode")
    print(f"Profile: {config['profile']}, Browser: {config['browser']}")
    print(f"Markers: {config['markers']}")
    
    try:
        import pytest
        import Keywords.projectVariables as var
        
        var.product = product
        var.browser = config['browser']
        var.profile = config['profile']
        var.generate_report_enabled = generate_report
        var.generate_log_file = generate_log_file
        var.headless = headless_mode.upper()
        var.record_video = record_video.upper()
        
        junit_dir = create_junit_directory()
        junit_file = os.path.join(junit_dir, "junit_report.xml")
        
        valid_markers = [marker for marker in config['markers'] if marker and marker.strip()]
        if not valid_markers:
            raise ValueError(f"No valid markers found in config: {config['markers']}")
        
        pytest_args = [
            "--log-cli-level=INFO",
            "-m", " or ".join(valid_markers),
            "--disable-pytest-warnings",
            "--continue-on-collection-errors",
            f"--junitxml={junit_file}",
            "--capture=tee-sys",
            "--tb=long",
            f"--suite-markers={','.join(valid_markers)}",
            f"--params={generate_report},{generate_log_file},{headless_mode},{record_video},{product},{config['browser']},{config['profile']}",
            "."
        ]
        
        start_time = time.time()
        exit_code = pytest.main(pytest_args)
        duration = round(time.time() - start_time, 2)
        
        status = "✅ PASSED" if exit_code == 0 else "❌ FAILED"
        
        print("\n" + "=" * 60)
        print("📊 SINGLE EXECUTION SUMMARY")
        print("=" * 60)
        print(f"Profile: {config['profile']}")
        print(f"Browser: {config['browser']}")
        print(f"Markers: {', '.join(valid_markers)}")
        print(f"Status: {status}")
        print(f"Duration: {duration}s")
        print("=" * 60)
        
        return exit_code
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return 1

def run_subprocess_execution(config, generate_report, generate_log_file, headless_mode, record_video, product):
    """Run execution using subprocess with enhanced summary"""
    thread_prefix = f"[Thread-{config['thread_id']}]" if config['thread_id'] else ""
    
    try:
        junit_dir = create_junit_directory()
        if config['thread_id']:
            junit_file = os.path.join(junit_dir, f"junit_thread_{config['thread_id']}_{config['profile']}.xml")
        else:
            junit_file = os.path.join(junit_dir, f"junit_{config['profile']}_{config['markers'][0]}.xml")
        
        pytest_args = prepare_pytest_args(config, junit_file, generate_report, generate_log_file, headless_mode, record_video, product)
        env = create_environment(config, generate_report, generate_log_file, headless_mode, record_video, product)
        
        print(f"{thread_prefix}Running: Profile={config['profile']}, Markers={config['markers']}, Browser={config['browser']}")
        
        start_time = time.time()
        result = subprocess.run(
            pytest_args,
            env=env,
            cwd=os.getcwd(),
            capture_output=True,
            text=True,
            timeout=3600
        )
        duration = round(time.time() - start_time, 2)
        
        test_summary = extract_test_summary(result.stdout)
        
        if test_summary != "No output available" and test_summary != "Summary not available":
            print(f"{thread_prefix}STDOUT: {test_summary}")
        
        if result.stdout:
            lines = result.stdout.split('\n')
            important_lines = [line for line in lines if any(keyword in line.lower() for keyword in 
                             ['collected', 'deselected', 'error']) and test_summary not in line]
            for line in important_lines[-3:]:
                if line.strip():
                    print(f"{thread_prefix}STDOUT: {line}")
        
        if result.stderr and result.returncode != 0:
            error_lines = [line for line in result.stderr.split('\n') if 'error' in line.lower()]
            for line in error_lines[-3:]:
                if line.strip():
                    print(f"{thread_prefix}STDERR: {line}")
        
        status = "✅ PASSED" if result.returncode == 0 else "❌ FAILED"
        print(f"{thread_prefix}{status} (Duration: {duration}s)")
        
        return result.returncode
        
    except subprocess.TimeoutExpired:
        print(f"{thread_prefix}❌ TIMEOUT after 1 hour")
        return 124
    except Exception as e:
        print(f"{thread_prefix}❌ ERROR: {str(e)}")
        return 1

def run_parallel_execution(configs, generate_report, generate_log_file, headless_mode, record_video, product):
    """Run multiple executions in parallel"""
    print("🚀 PARALLEL EXECUTION ENABLED")
    print("=" * 60)
    print(f"Total Threads: {len(configs)}")
    
    for config in configs:
        print(f"Thread-{config['thread_id']}: Profile={config['profile']}, Markers={config['markers']}, Browser={config['browser']}")
    print("=" * 60)
    
    junit_dir = create_junit_directory()
    print(f"📄 JUnit XML reports: {junit_dir}")
    
    threads = []
    results = {}
    
    def thread_wrapper(config):
        results[config['thread_id']] = {
            'exit_code': run_subprocess_execution(config, generate_report, generate_log_file, headless_mode, record_video, product),
            'config': config
        }
    
    start_time = time.time()
    for config in configs:
        t = threading.Thread(target=thread_wrapper, args=(config,))
        threads.append(t)
        t.start()
        print(f"🔄 Thread-{config['thread_id']} started")
    
    for t in threads:
        t.join()
    
    total_duration = round(time.time() - start_time, 2)
    print("\n" + "=" * 60)
    print("📊 PARALLEL EXECUTION SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for r in results.values() if r['exit_code'] == 0)
    failed = len(results) - passed
    
    for thread_id, result in results.items():
        config = result['config']
        status = "✅ PASSED" if result['exit_code'] == 0 else f"❌ FAILED ({result['exit_code']})"
        print(f"Thread-{thread_id} [{config['profile']}|{config['markers'][0]}]: {status}")
    
    print(f"Total Duration: {total_duration}s")
    print(f"Results: {passed} PASSED, {failed} FAILED")
    print(f"📁 All reports in: {junit_dir}")
    print("=" * 60)
    
    return 0 if failed == 0 else 1