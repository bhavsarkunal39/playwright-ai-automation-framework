import os
import sys
from pathlib import Path
import json

# Import our custom modules - UPDATE THIS LINE
from core.config_manager import validate_configuration, get_parallel_configs, get_single_config, apply_ci_overrides, get_suite_parallel_configs
from core.executor_manager import run_single_execution, run_subprocess_execution, run_parallel_execution

#------------------------------------------------------------------------------------------
#                           USER CONFIGURATION SECTION
#------------------------------------------------------------------------------------------

# Report and Video Settings
generate_report="Y"
generate_log_file="Y"
headless_mode="N"
record_video="Y"

#------------------------------------------------------------------------------------------

# Product name: PROJECT, CRA etc
product = "PROJECT"   

#------------Enter browser name below: chrome, etc---------
default_browser = "chrome"
 
#------------Enter Profile name below: EKDEV,EKDET..etc (Make sure profile exists)----
default_profile ="DEFAULT"  

#------------Enter Testcases Marker name below which need to be executed in Suite-----
default_markers = ["test_sampleTC"]  

#------------------------------------------------------------------------------------------
# Parallel Suite Configuration (overrides default configuration when set)
#------------------------------------------------------------------------------------------
#------------Parallel Execution Flag: Y to enable, N to disable---------
parallel_run="N"  
Suite_1=[{
    "profile":"DEFAULT",
    "markers":["test_DatabaseTC"],
    "browser":["firefox"]
}]

Suite_2=[{
    "profile":"DEFAULT1",
    "markers":["test_DatabaseTC"],
    "browser":["chrome"]
}]

# Use json.dumps to build a proper JSON string (double quotes)
PARALLEL_CONFIG = json.dumps(Suite_1 + Suite_2)

#------------------------------------------------------------------------------------------

def main():
    """Main execution function"""
    project_root = os.getcwd()
    sys.path.append(project_root)
    
    # Apply CI/CD overrides to get final configuration
    config = apply_ci_overrides(default_profile, default_browser, default_markers, product, 
                               parallel_run, generate_report, generate_log_file, headless_mode, record_video)
    
    # Validate final configuration
    if not validate_configuration(config['profile'], config['browser'], config['markers'], 
                                config['product'], config['parallel_run'], config['generate_report'], 
                                config['generate_log_file'], config['headless_mode'], config['record_video']):
        sys.exit(1)
        
    # Set suite name for pytest
    os.environ['PYTEST_SUITE_NAME'] = Path(__file__).stem
    
    # Check for suite-based parallel configuration first using config_manager method
    # This will now check CI/CD PARALLEL_SUITE_CONFIG first, then fall back to local PARALLEL_CONFIG
    suite_configs = get_suite_parallel_configs(config['parallel_run'], PARALLEL_CONFIG)
    
    try:
        if suite_configs:
            # Use suite-based configuration (CI/CD or local)
            config_source = "CI/CD" if os.environ.get('PARALLEL_SUITE_CONFIG') else "Local"
            print(f"🔥 {config_source} Suite-based parallel mode: {len(suite_configs)} configurations")
            for i, suite_config in enumerate(suite_configs, 1):
                browsers = suite_config.get('browser', [config['browser']])
                browser_str = browsers[0] if isinstance(browsers, list) else browsers
                print(f"  {i}. Profile: {suite_config['profile']}, Markers: {suite_config['markers']}, Browser: {browser_str}")
            
            # Convert suite configs to the format expected by run_parallel_execution
            formatted_configs = []
            for i, suite_config in enumerate(suite_configs):
                browsers = suite_config.get('browser', [config['browser']])
                browser_str = browsers[0] if isinstance(browsers, list) else browsers
                formatted_configs.append({
                    'profile': suite_config['profile'],
                    'browser': browser_str,
                    'markers': suite_config['markers'],
                    'thread_id': i + 1,
                    'sequential': False
                })
            
            exit_code = run_parallel_execution(formatted_configs, config['generate_report'], config['generate_log_file'], 
                                             config['headless_mode'], config['record_video'], config['product'])
        
        elif config['parallel_run'].upper() == 'Y':
            # Use original parallel configuration method
            configs = get_parallel_configs(config['profile'], config['browser'], config['markers'])
            if len(configs) > 1:
                print(f"🔥 Default parallel mode: {len(configs)} configurations")
                exit_code = run_parallel_execution(configs, config['generate_report'], config['generate_log_file'], 
                                                 config['headless_mode'], config['record_video'], config['product'])
            else:
                print("🔹 Single thread (only 1 config)")
                exit_code = run_subprocess_execution(configs[0], config['generate_report'], config['generate_log_file'], 
                                                   config['headless_mode'], config['record_video'], config['product'])
        else:
            print("🔹 Non-parallel execution mode")
            single_config = get_single_config(config['profile'], config['browser'], config['markers'])
            exit_code = run_single_execution(single_config, config['generate_report'], config['generate_log_file'], 
                                           config['headless_mode'], config['record_video'], config['product'])
    
    except ValueError as e:
        print(f"\n❌ Configuration Error: {str(e)}")
        print("Please check your configuration in RunTestsuite.py or CI/CD variables")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️ Execution interrupted by user")
        exit_code = 130
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        exit_code = 1
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()