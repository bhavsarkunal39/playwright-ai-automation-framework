import xml.etree.ElementTree as ET
import sys
import os
import glob

def find_junit_xml_files():
    """Find all JUnit XML files in the Test_Reports/JUnit_Reports directory"""
    junit_dir = os.path.join("Test_Reports", "JUnit_Reports")
    
    if not os.path.exists(junit_dir):
        print(f"❌ JUnit Reports directory not found at {junit_dir}")
        return []
    
    # Look for various JUnit XML file patterns
    patterns = [
        os.path.join(junit_dir, "junit_report.xml"),          # Single execution
        os.path.join(junit_dir, "junit_thread_*.xml"),        # Parallel execution threads
        os.path.join(junit_dir, "junit_*.xml"),               # Other junit files
        os.path.join(junit_dir, "report.xml")                 # Legacy report name
    ]
    
    xml_files = []
    for pattern in patterns:
        xml_files.extend(glob.glob(pattern))
    
    # Remove duplicates and sort
    xml_files = list(set(xml_files))
    xml_files.sort()
    
    return xml_files

def parse_single_xml_file(file_path):
    """Parse a single XML file and return test results"""
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # Initialize counters for this file
        file_results = {
            'file_path': file_path,
            'total_failures': 0,
            'total_errors': 0,
            'total_tests': 0,
            'total_skipped': 0,
            'total_deselected': 0,
            'passed_count': 0,
            'collection_errors': 0,
            'detailed_issues': []
        }
        
        # Handle both single testsuite and testsuites with multiple testsuite elements
        testsuites = root.findall("testsuite") if root.tag == "testsuites" else [root]
        
        for testsuite in testsuites:
            failures = int(testsuite.attrib.get('failures', 0))
            errors = int(testsuite.attrib.get('errors', 0))
            tests = int(testsuite.attrib.get('tests', 0))
            skipped = int(testsuite.attrib.get('skipped', 0))
            
            file_results['total_failures'] += failures
            file_results['total_errors'] += errors
            file_results['total_tests'] += tests
            file_results['total_skipped'] += skipped
            
            # Check each testcase in this testsuite
            for testcase in testsuite.findall("testcase"):
                test_name = testcase.attrib.get('name', 'unknown')
                class_name = testcase.attrib.get('classname', testsuite.attrib.get('name', 'unknown'))
                
                error = testcase.find("error")
                failure = testcase.find("failure")
                skipped_elem = testcase.find("skipped")
                
                # Check if this is a collection error (test file couldn't be imported/collected)
                if error is not None:
                    error_type = error.attrib.get('type', '')
                    error_message = error.attrib.get('message', 'No message')
                    
                    # Collection errors usually have specific types
                    if any(err_type in error_type.lower() for err_type in ['import', 'collection', 'attributeerror', 'modulenotfounderror']):
                        file_results['collection_errors'] += 1
                        file_results['detailed_issues'].append(
                            f"🚨 COLLECTION ERROR in {class_name}::{test_name}: {error_message}"
                        )
                    else:
                        file_results['detailed_issues'].append(
                            f"❌ ERROR in {class_name}::{test_name}: {error_message}"
                        )
                    
                    if error.text and error.text.strip():
                        # Only show first few lines of error details
                        error_lines = error.text.strip().split('\n')[:3]
                        for line in error_lines:
                            if line.strip():
                                file_results['detailed_issues'].append(f"   {line.strip()}")
                                
                elif failure is not None:
                    file_results['detailed_issues'].append(
                        f"❌ FAILURE in {class_name}::{test_name}: {failure.attrib.get('message', 'No message')}"
                    )
                    if failure.text and failure.text.strip():
                        # Only show first few lines of failure details
                        failure_lines = failure.text.strip().split('\n')[:3]
                        for line in failure_lines:
                            if line.strip():
                                file_results['detailed_issues'].append(f"   {line.strip()}")
                elif skipped_elem is None:
                    # Test passed (not error, not failure, not skipped)
                    file_results['passed_count'] += 1
        
        return file_results
        
    except ET.ParseError as e:
        print(f"❌ Failed to parse XML file {file_path}: {e}")
        return None
    except Exception as e:
        print(f"❌ Error processing XML file {file_path}: {e}")
        return None

def main():
    """Main function to check test results from JUnit XML reports"""
    print("🔍 Checking JUnit XML test results...")
    
    # Find all JUnit XML files
    xml_files = find_junit_xml_files()
    
    if not xml_files:
        print("❌ No JUnit XML files found in Test_Reports/JUnit_Reports directory")
        print("   Expected files: junit_report.xml, junit_thread_*.xml, or junit_*.xml")
        sys.exit(1)
    
    print(f"📁 Found {len(xml_files)} JUnit XML file(s):")
    for xml_file in xml_files:
        print(f"   - {os.path.basename(xml_file)}")
    
    # Parse all XML files
    all_results = []
    for xml_file in xml_files:
        result = parse_single_xml_file(xml_file)
        if result:
            all_results.append(result)
    
    if not all_results:
        print("❌ Failed to parse any XML files")
        sys.exit(1)
    
    # Aggregate results from all files
    total_failures = sum(r['total_failures'] for r in all_results)
    total_errors = sum(r['total_errors'] for r in all_results)
    total_tests = sum(r['total_tests'] for r in all_results)
    total_skipped = sum(r['total_skipped'] for r in all_results)
    passed_count = sum(r['passed_count'] for r in all_results)
    collection_errors = sum(r['collection_errors'] for r in all_results)
    
    # Calculate actual test execution errors (excluding collection errors)
    execution_errors = total_errors - collection_errors
    
    # Print overall summary
    print("\n" + "=" * 60)
    print("📊 OVERALL TEST RESULTS SUMMARY")
    print("=" * 60)
    print(f"📋 Total Tests Found: {total_tests}")
    print(f"✅ Passed: {passed_count}")
    print(f"❌ Failed: {total_failures}")
    print(f"🚨 Execution Errors: {execution_errors}")
    print(f"⏭️ Skipped: {total_skipped}")
    if collection_errors > 0:
        print(f"🚨 Collection Errors: {collection_errors} (files that couldn't be imported/collected)")
    
    # Print per-file breakdown if multiple files
    if len(all_results) > 1:
        print("\n📁 Per-File Breakdown:")
        for result in all_results:
            file_name = os.path.basename(result['file_path'])
            print(f"   {file_name}: {result['total_tests']} tests, {result['passed_count']} passed, "
                  f"{result['total_failures']} failed, {result['total_errors']} errors")
    
    # Print detailed issues if any
    all_issues = []
    for result in all_results:
        if result['detailed_issues']:
            file_name = os.path.basename(result['file_path'])
            all_issues.append(f"\n📄 Issues in {file_name}:")
            all_issues.extend(result['detailed_issues'])
    
    if all_issues:
        print("\n" + "=" * 60)
        print("🔍 DETAILED ISSUES FOUND")
        print("=" * 60)
        for issue in all_issues:
            print(issue)
    
    # Determine exit status based on actual test execution results
    # Collection errors are warnings, not test failures
    if total_failures > 0 or execution_errors > 0:
        print(f"\n❌ Pipeline failed due to test failures or execution errors.")
        if collection_errors > 0:
            print(f"⚠️  Note: {collection_errors} collection error(s) found - these indicate issues with test file imports.")
        print("=" * 60)
        sys.exit(1)
    elif passed_count > 0:
        print(f"\n✅ All executed tests passed successfully! ({passed_count} passed)")
        if collection_errors > 0:
            print(f"⚠️  Note: {collection_errors} collection error(s) found - fix these to run more tests.")
        print("=" * 60)
        sys.exit(0)
    elif collection_errors > 0 and total_tests == 0:
        print(f"\n⚠️  Only collection errors found ({collection_errors}), no tests executed.")
        print("   Fix import/collection issues to run tests.")
        print("=" * 60)
        sys.exit(1)
    else:
        print("\n⚠️ No tests found in any report.")
        print("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    main()