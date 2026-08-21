generate_report="Y"
generate_log_file="Y"
headless_mode="N"
record_video="N"
#------------------------------------------------------------------------------------------
#------------Enter Product name below: PRA, CRA etc---------
product="PRA"   

#------------Enter browser name below: chrome, etc---------
browser="chrome"
 
#------------Enter Profile name below: EKDEV,EKDET..etc (Make sure profile exists)----
profile="DEFAULT"
 
#------------Enter Testcases Marker name below which need to be executed in Suite-----
markers = ["test_sampleTC"]

#------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------
 

if __name__ == "__main__":
    import os
    import sys
    import subprocess
    from pathlib import Path
    project_root = os.getcwd()
    sys.path.append(project_root)
    # Get current file name without extension
    current_file_name = Path(__file__).stem
    os.environ['PYTEST_SUITE_NAME'] = current_file_name
    import Keywords.projectVariables as var
    import logging as log
    
    #-----------------------------------------------------
    var.product = product
    var.browser = browser
    var.profile = profile
    var.generate_report_enabled= generate_report
    var.generate_log_file= generate_log_file
    var.headless = headless_mode.upper()
    var.record_video = record_video.upper()
    
    # Pass markers to pytest as a CLI param
    markers_str = ",".join(markers)
    
    params = f"{generate_report},{generate_log_file},{headless_mode},{record_video},{product},{browser},{profile}"         
    # ACTUAL RUN
    print("------------------------------Running tests for marker(s)------------------------------")
    subprocess.run([
    sys.executable, "-m", "pytest",
    f"--suite-markers={markers_str}",
        "--log-cli-level=INFO",
        "-m", " or ".join(markers),
        "--disable-pytest-warnings",
        "-q",
        f"--params={params}"
    ])

#"--continue-on-collection-errors",