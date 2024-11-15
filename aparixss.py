import time
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

# Define common XSS payloads
XSS_PAYLOADS = [
    "<script>alert('XSS')</script>",
    "'><script>alert('XSS')</script>",
    "\"'><script>alert('XSS')</script>",
    "<img src=x onerror=alert('XSS')>",
]

# ASCII Art Banner for 'aparixss'
BANNER = """
    _   _                           _   __   __ _____ _____ 
   /_\ | |__  _   _ _ __ ___  ___   / \\  \\ \\ / /| ____|_   _|
  //_\\\\| '_ \\| | | | '__/ __|/ _ \\ / _ \\  \\ V / |  _|   | |  
 /  _  \\ | | | |_| | |  \\__ \\  __// ___ \\  | |  | |___  | |  
 \\_/ \\_/_| |_|\\__,_|_|  |___/\\___/_/   \\_\\ |_|  |_____| |_|  
                                                             """
# CLI Usage Instructions
USAGE = """
Usage: python aparixss.py [URL1] [URL2] ...

Example:
    python aparixss.py https://example.com/page1 https://example.com/page2

Description:
    ApariXSS is an automated tool for detecting reflected XSS vulnerabilities
    in web applications. It scans all forms on each provided URL, injects XSS
    payloads, submits the forms, and analyzes the responses. Potential
    vulnerabilities are listed and saved to a file for manual review.
"""

def initialize_browser():
    # Setup Chrome options
    options = Options()
    options.add_argument("--headless")  # Run in headless mode for faster execution
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    # Setup the Chrome WebDriver using WebDriverManager to automatically get the right driver version
    service = Service(ChromeDriverManager().install())
    
    # Initialize the Chrome driver
    browser = webdriver.Chrome(service=service, options=options)
    return browser

def scan_page_for_forms(browser, url):
    browser.get(url)
    time.sleep(2)  # Wait for page load
    soup = BeautifulSoup(browser.page_source, "html.parser")
    forms = soup.find_all("form")
    return forms

def test_xss_in_form(browser, form, url):
    vulnerable_forms = []
    for payload in XSS_PAYLOADS:
        browser.get(url)
        time.sleep(1)
        try:
            # Fill form fields with the XSS payload
            for input_tag in form.find_all(["input", "textarea"]):
                name = input_tag.get("name")
                if name:
                    field = browser.find_element(By.NAME, name)
                    field.clear()
                    field.send_keys(payload)

            # Attempt to submit the form
            submit_button = browser.find_element(By.XPATH, "//input[@type='submit']") or \
                            browser.find_element(By.XPATH, "//button[@type='submit']")
            submit_button.click()
            time.sleep(1)
            
            # Check if payload appears in page source
            if payload in browser.page_source:
                vulnerable_forms.append({
                    "url": url,
                    "form": form,
                    "payload": payload
                })
                break
        except Exception as e:
            print(f"[ERROR] Could not test form on {url}: {e}")
    return vulnerable_forms

def find_xss_vulnerabilities(browser, url):
    xss_vulnerable = []
    forms = scan_page_for_forms(browser, url)
    print(f"[INFO] Found {len(forms)} forms on {url}")
    for form in forms:
        vulnerabilities = test_xss_in_form(browser, form, url)
        if vulnerabilities:
            xss_vulnerable.extend(vulnerabilities)
    return xss_vulnerable

def main(urls):
    # Display banner and usage instructions
    print(BANNER)
    if not urls:
        print(USAGE)
        return
    
    browser = initialize_browser()
    all_vulnerabilities = {}

    try:
        for url in urls:
            print(f"\n[INFO] Scanning {url} for XSS vulnerabilities...")
            vulnerabilities = find_xss_vulnerabilities(browser, url)
            if vulnerabilities:
                all_vulnerabilities[url] = vulnerabilities
                print(f"[ALERT] Potential XSS vulnerabilities found on {url}!")
        
        # Report results
        if all_vulnerabilities:
            print("\n[SUMMARY] XSS Vulnerabilities detected:")
            report_filename = "aparixss_report.txt"
            with open(report_filename, "w") as report_file:
                for url, issues in all_vulnerabilities.items():
                    print(f"\nURL: {url}")
                    report_file.write(f"\nURL: {url}\n")
                    for issue in issues:
                        form_details = f"  Form: {issue['form']}\n  Payload: {issue['payload']}\n"
                        print(form_details)
                        report_file.write(form_details)
            print(f"\n[INFO] Vulnerabilities report saved to {report_filename}")
        else:
            print("[INFO] No XSS vulnerabilities detected.")
    
    finally:
        browser.quit()

# Run the script with URLs provided in command-line arguments
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(BANNER)
        print(USAGE)
    else:
        main(sys.argv[1:])
