import schedule
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os


def main():
    # Load credentials from environment variables for security
    linkedin_email = os.getenv('LINKEDIN_EMAIL', 'raj.kumar@gmail.com')  # Replace with your environment variable
    linkedin_password = os.getenv('LINKEDIN_PASSWORD', 'some_password')  # Replace with your environment variable

    # Configure WebDriver with proper options
    service = Service(executable_path='C:/Users/username/my_proj/my_pyautomation/scripts/driver/chromedriver.exe')
    options = webdriver.ChromeOptions()

    # Disable GPU hardware acceleration and enable headless mode if necessary
    options.add_argument('--disable-gpu')
    options.add_argument('--headless')  # Optional: Run in headless mode (use if GUI is not needed)
    options.add_argument('--disable-software-rasterizer')  # Use software rendering
    options.add_argument('--log-level=3')  # Suppress GPU warnings

    driver = webdriver.Chrome(service=service, options=options)

    try:
        # Log in to LinkedIn
        driver.get('https://www.linkedin.com/login')
        email = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'username')))
        password = driver.find_element(By.ID, 'password')
        email.send_keys(linkedin_email)
        password.send_keys(linkedin_password)
        password.send_keys(Keys.RETURN)

        # Wait until logged in
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'global-nav-typeahead'))
        )

        # Go to the jobs page
        driver.get('https://www.linkedin.com/jobs/')

        # Search for jobs
        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'jobs-search-box__text-input'))
        )
        search_box.send_keys('Software Engineer')  # Customize the job title here
        search_box.send_keys(Keys.RETURN)

        # Wait until search results are loaded
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'job-card-container'))
        )

        # Loop through job listings and apply
        while True:
            jobs = driver.find_elements(By.CLASS_NAME, 'job-card-container')
            for job in jobs:
                try:
                    job.click()
                    time.sleep(2)  # Wait for the page to load

                    # Click the Easy Apply button
                    easy_apply_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'jobs-apply-button')]"))
                    )
                    easy_apply_button.click()

                    # Handle the application form if needed
                    submit_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[@type='submit' and @aria-label='Submit application']"))
                    )
                    submit_button.click()
                    time.sleep(2)

                except Exception as e:
                    print(f"Could not apply for job: {e}")
                    continue

            # Check if there's a next page of jobs
            try:
                next_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Next']"))
                )
                next_button.click()
                time.sleep(5)  # Wait for the next page to load
            except:
                print("No more pages.")
                break

    finally:
        driver.quit()


if __name__ == "__main__":
    main()

    # Schedule the script to run at specific times
    schedule.every().day.at("05:00").do(main)  # 5:00 AM
    schedule.every().day.at("17:00").do(main)  # 5:00 PM

    # Keep the script running to check the schedule
    while True:
        schedule.run_pending()
        time.sleep(60)
