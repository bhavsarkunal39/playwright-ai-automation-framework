import os
import ast
import json

def get_ci_overrides():
    """Get CI/CD environment variable overrides"""
    overrides = {}
    
    # Check for CI/CD variables
    if os.environ.get('PROFILE'):
        overrides['profile'] = os.environ.get('PROFILE')
    
    if os.environ.get('BROWSER'):
        overrides['browser'] = os.environ.get('BROWSER')
    
    if os.environ.get('PARALLEL_RUN'):
        overrides['parallel_run'] = os.environ.get('PARALLEL_RUN')
    
    if os.environ.get('MARKERS'):
        overrides['markers'] = os.environ.get('MARKERS')
    
    if os.environ.get('PRODUCT'):
        overrides['product'] = os.environ.get('PRODUCT')
    
    if os.environ.get('GENERATE_REPORT'):
        overrides['generate_report'] = os.environ.get('GENERATE_REPORT')
    
    if os.environ.get('HEADLESS_MODE'):
        overrides['headless_mode'] = os.environ.get('HEADLESS_MODE')
    
    # NEW: Support for CI/CD Suite Configuration
    if os.environ.get('PARALLEL_SUITE_CONFIG'):
        overrides['parallel_suite_config'] = os.environ.get('PARALLEL_SUITE_CONFIG')
    
    return overrides

def apply_ci_overrides(default_profile, default_browser, default_markers, product, parallel_run, 
                       generate_report, generate_log_file, headless_mode, record_video):
    """Apply CI/CD overrides to default configuration"""
    overrides = get_ci_overrides()
    
    # Apply overrides
    final_profile = overrides.get('profile', default_profile)
    final_browser = overrides.get('browser', default_browser)
    final_markers = overrides.get('markers', default_markers)
    final_product = overrides.get('product', product)
    final_parallel_run = overrides.get('parallel_run', parallel_run)
    final_generate_report = overrides.get('generate_report', generate_report)
    final_headless_mode = overrides.get('headless_mode', headless_mode)
    
    # Print CI/CD override information
    if overrides:
        print("🔄 CI/CD Environment Overrides Detected:")
        print("=" * 50)
        for key, value in overrides.items():
            print(f"   {key.upper()}: {value}")
        print("=" * 50)
    
    return {
        'profile': final_profile,
        'browser': final_browser,
        'markers': final_markers,
        'product': final_product,
        'parallel_run': final_parallel_run,
        'generate_report': final_generate_report,
        'generate_log_file': generate_log_file,
        'headless_mode': final_headless_mode,
        'record_video': record_video
    }

def validate_configuration(default_profile, default_browser, default_markers, product, parallel_run, 
                          generate_report="Y", generate_log_file="Y", headless_mode="N", record_video="N"):
    """Enhanced validation with CI/CD support"""
    
    # Get final configuration after applying CI/CD overrides
    config = apply_ci_overrides(default_profile, default_browser, default_markers, product, 
                               parallel_run, generate_report, generate_log_file, headless_mode, record_video)
    
    # Use final config for validation
    final_profile = config['profile']
    final_browser = config['browser'] 
    final_markers = config['markers']
    final_product = config['product']
    final_parallel_run = config['parallel_run']
    
    # Your existing validation logic here using final_* variables
    errors = []
    parallel_enabled = final_parallel_run.upper() == 'Y'
    
    # Profile validation - STRICT for non-parallel
    if isinstance(final_profile, (tuple, list)):
        valid_profiles = [profile for profile in final_profile if profile and str(profile).strip()]
        if not valid_profiles:
            errors.append("❌ default_profile contains only empty values!")
        elif len(valid_profiles) > 1 and not parallel_enabled:
            errors.append(f"❌ Multiple profiles detected ({len(valid_profiles)} profiles) but parallel_run='N'! Use single profile only")
    elif isinstance(final_profile, str):
        if not final_profile or final_profile.strip() == "":
            errors.append("❌ default_profile is empty!")
    
    # Browser validation - STRICT for non-parallel
    if isinstance(final_browser, (tuple, list)):
        valid_browsers = [browser for browser in final_browser if browser and str(browser).strip()]
        if not valid_browsers:
            errors.append("❌ default_browser contains only empty values!")
        elif len(valid_browsers) > 1 and not parallel_enabled:
            errors.append(f"❌ Multiple browsers detected ({len(valid_browsers)} browsers) but parallel_run='N'! Use single browser only")
    elif isinstance(final_browser, str):
        if not final_browser or final_browser.strip() == "":
            errors.append("❌ default_browser is empty!")
    
    # Markers validation - ALLOW multiple for non-parallel (sequential execution)
    if isinstance(final_markers, list):
        valid_markers = [marker for marker in final_markers if marker and marker.strip()]
        if not valid_markers:
            errors.append("❌ default_markers contains only empty values!")
        elif len(valid_markers) > 1 and not parallel_enabled:
            # Allow multiple markers for sequential execution
            print(f"ℹ️  Sequential execution with {len(valid_markers)} markers: {valid_markers}")
    elif not final_markers or len(final_markers) == 0:
        errors.append("❌ default_markers is empty!")
    
    if not final_product or final_product.strip() == "":
        errors.append("❌ product is empty!")
    
    if errors:
        print("\n" + "="*60)
        print("🚨 CONFIGURATION VALIDATION ERRORS")
        print("="*60)
        for error in errors:
            print(error)
        print("\n📋 Please update your configuration in RunTestsuite.py:")
        if not parallel_enabled:
            print("   For SEQUENTIAL execution (parallel_run='N'):")
            print("   - default_profile = 'SINGLE_PROFILE_NAME'  # Only ONE profile")
            print("   - default_browser = 'chrome'  # Only ONE browser")
            print("   - default_markers = ['marker1', 'marker2', ...]  # Multiple markers OK")
        else:
            print("   For PARALLEL execution (parallel_run='Y'):")
            print("   - default_profile = ('PROFILE1', 'PROFILE2') or 'SINGLE_PROFILE'")
            print("   - default_browser = ('chrome', 'firefox') or 'chrome'")
            print("   - default_markers = ['test_ReveraTC', 'test_DatabaseTC']")
        print("   - product = 'Project Automation")
        print("="*60)
        return False
    
    return True

def parse_config_value(value):
    """Parse configuration values into list format with validation"""
    if isinstance(value, (tuple, list)):
        parsed_list = [item for item in list(value) if item and str(item).strip()]
        return parsed_list if parsed_list else []
    elif isinstance(value, str) and ',' in value:
        parsed_list = [item.strip() for item in value.split(',') if item.strip()]
        return parsed_list if parsed_list else []
    else:
        return [value] if value and str(value).strip() else []

def get_suite_parallel_configs(parallel_run, parallel_config):
    """Parse the suite-based parallel configuration with CI/CD support"""
    # Check for CI/CD override first
    ci_suite_config = os.environ.get('PARALLEL_SUITE_CONFIG')
    
    if ci_suite_config:
        print("🔄 Using CI/CD Suite Configuration Override")
        try:
            configs = json.loads(ci_suite_config)
            return configs if configs else None
        except (json.JSONDecodeError, TypeError) as e:
            print(f"❌ Invalid PARALLEL_SUITE_CONFIG format: {e}")
            print("Falling back to default configuration")
    
    # Use local configuration if no CI/CD override
    if parallel_run.upper() == 'Y' and parallel_config:
        try:
            configs = json.loads(parallel_config)
            return configs if configs else None
        except (json.JSONDecodeError, TypeError):
            print("❌ Invalid PARALLEL_CONFIG format, falling back to default configuration")
            return None
    return None

def get_parallel_configs(default_profile, default_browser, default_markers):
    """Get configurations for parallel execution"""
    profiles = parse_config_value(default_profile)
    browsers = parse_config_value(default_browser)
    markers = parse_config_value(default_markers)
    
    print(f"Debug - Profiles: {profiles}")
    print(f"Debug - Browsers: {browsers}")
    print(f"Debug - Markers: {markers}")
    
    if not profiles:
        raise ValueError("No valid profiles found after parsing default_profile")
    if not browsers:
        raise ValueError("No valid browsers found after parsing default_browser")
    if not markers:
        raise ValueError("No valid markers found after parsing default_markers")
    
    max_threads = max(len(profiles), len(browsers), len(markers))
    
    configs = []
    for i in range(max_threads):
        config = {
            'profile': profiles[i % len(profiles)],
            'browser': browsers[i % len(browsers)],
            'markers': [markers[i % len(markers)]],
            'thread_id': i + 1,
            'sequential': False
        }
        configs.append(config)
    
    return configs

def get_single_config(default_profile, default_browser, default_markers):
    """Get configuration for single execution with validation and env override support"""
    profile_env = os.environ.get('PROFILE')
    browser_env = os.environ.get('BROWSER')
    markers_env = os.environ.get('MARKERS')
    
    if profile_env:
        profile = profile_env
    else:
        if isinstance(default_profile, (tuple, list)):
            profile = default_profile[0]  # Take first profile only
        elif isinstance(default_profile, str):
            if ',' in default_profile:
                profiles = [p.strip() for p in default_profile.split(',') if p.strip()]
                profile = profiles[0]  # Take first profile only
            else:
                profile = default_profile
        else:
            profile = str(default_profile)
    
    if browser_env:
        browser = browser_env
    else:
        if isinstance(default_browser, (tuple, list)):
            browser = default_browser[0]  # Take first browser only
        elif isinstance(default_browser, str):
            if ',' in default_browser:
                browsers = [b.strip() for b in default_browser.split(',') if b.strip()]
                browser = browsers[0]  # Take first browser only
            else:
                browser = default_browser
        else:
            browser = str(default_browser)
    
    if markers_env:
        try:
            markers = ast.literal_eval(markers_env)
        except:
            markers = [m.strip() for m in markers_env.split(',') if m.strip()]
    else:
        if isinstance(default_markers, list):
            markers = default_markers  # Keep ALL markers for sequential execution
        else:
            markers = [default_markers]
    
    valid_markers = [marker for marker in markers if marker and marker.strip()]
    if not valid_markers:
        raise ValueError("No valid markers found in configuration")
    
    return {
        'profile': profile,
        'browser': browser,
        'markers': valid_markers,  # Return all markers for sequential execution
        'thread_id': None
    }