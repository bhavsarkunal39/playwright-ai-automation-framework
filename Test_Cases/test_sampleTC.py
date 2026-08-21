import logging as log
import pytest
from Keywords.apiRequest import APIrequest
import Object_Repository.mainlocator as path
'''
For custom keywords use 'customKey.' eg. customKey.login() and for Revera Function keywords use 'functionKey.'
For API keywords use 'apiKey.' eg. apiKey.api_get() , apiKey.api_post() etc.
For playwright keywords use 'page.' ,eg. page.click()
'''
@pytest.mark.test_sampleTC
@pytest.mark.order(1)
def test_sampleTC(report,page):
    apiKey = APIrequest()
    report.set_page(page)
    testcase_name = "Sample Testcase1"
    testcase_description = """1. This is Sample Testcase for trial run.
                        2. Sample for break line.
                        3. Trial line"""
    marker_name = "test_sampleTC"
    report.start_test(testcase_name, testcase_description, marker_name)
    #Variables
    ui_value1 = "//*[@id='menu-item-1082']"
    
    report.mask_fields=[ui_value1]
    
    #Start writing test cases from below line.
    page.goto("https://www.google.com/")
    page.wait_for_timeout(2000)
    report.test_info("Navigated to Google.com",'Y')
    page.wait_for_timeout(2000)
    report.explicitCaptureSS("Full Page Screenshot",'Y')
    page.wait_for_timeout(2000)
    report.test_status('PASS',"Trial testcase status Pass","Y")
