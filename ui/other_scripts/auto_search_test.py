# python -m ui.other_scripts.auto_search_test.py

import time
import random
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# List of random search queries
search_queries = [
    "Python automation with Selenium",
    "Latest AI advancements",
    "How to use Microsoft Edge WebDriver",
    "Best programming languages 2025",
    "Weather forecast today",
    "Tech news updates",
    "How to cook pasta",
    "Random fun facts",
    "AWS EC2 official documentation",
    "AWS Lambda function tutorial",
    "How to deploy Docker on AWS ECS",
    "Amazon EKS vs ECS comparison",
    "AWS ECR best practices",
    "How to set up auto-scaling in EC2",
    "AWS Lambda vs EC2 pricing",
    "AWS Step Functions use cases",
    "How to configure IAM roles for AWS services",
    "AWS CloudFormation vs Terraform"
]

# Path to Edge WebDriver (Change this path if needed)
webdriver_path = "D:/Users/IrshadAl/tge/ird-project/my_pyautomation/scripts/driver/msedgedriver.exe"

# Setup Microsoft Edge WebDriver
service = Service(executable_path=webdriver_path)
options = webdriver.EdgeOptions()

# Start Microsoft Edge browser
driver = webdriver.Edge(service=service, options=options)

# Function to randomly scroll up and down
def random_scroll(driver):
    scroll_time = random.randint(10, 20)  # Scroll for 5 to 10 seconds
    start_time = time.time()
    
    while time.time() - start_time < scroll_time:
        scroll_distance = random.randint(500, 1000)  # Random scroll distance
        direction = random.choice(["up", "down"])  # Choose scroll direction

        if direction == "down":
            driver.execute_script(f"window.scrollBy(0, {scroll_distance});")
        else:
            driver.execute_script(f"window.scrollBy(0, -{scroll_distance});")
        
        time.sleep(random.uniform(1, 2))  # Short delay between scrolls
    
    print(f"Scrolled randomly for {scroll_time} seconds.")

try:
    # Open Bing search once
    driver.get("https://www.bing.com")
    time.sleep(3)  # Initial wait for page to load

    while True:  # Infinite loop for continuous execution
        # Select a random search query
        random_query = random.choice(search_queries)

        # Locate search bar, clear it, and enter random text
        search_box = driver.find_element(By.NAME, "q")
        search_box.clear()
        search_box.send_keys(random_query)
        search_box.send_keys(Keys.RETURN)  # Press Enter

        print(f"Searching for: {random_query}")

        # Wait for search results to load
        time.sleep(random.randint(10, 20))  # Random short wait

        # Find the first two search result links
        search_results = WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.b_algo h2 a"))
        )[:2]  # Get first two results

        if search_results:
            # Choose randomly between first and second result
            selected_result = random.choice(search_results)
            
            # Scroll into view before clicking
            driver.execute_script("arguments[0].scrollIntoView();", selected_result)
            time.sleep(2)  # Small delay to allow scrolling

            try:
                # Open link in a new tab
                selected_result.send_keys(Keys.CONTROL + Keys.RETURN)  # Opens in a new tab
                print("Opened result in a new tab.")

                # Switch to the new tab
                driver.switch_to.window(driver.window_handles[-1])

                # Scroll up and down randomly
                random_scroll(driver)

                # Wait on the page before closing
                wait_time = random.randint(10, 30)
                print(f"Waiting for {wait_time} seconds on the page...")
                time.sleep(wait_time)

                # Close the current tab
                driver.close()
                print("Closed the current tab.")

                # Switch back to the original search tab
                driver.switch_to.window(driver.window_handles[0])

            except Exception as e:
                print(f"Error handling tab: {e}")

        else:
            print("No search results found.")

        # Random delay before next search
        time.sleep(random.randint(10, 40))

except KeyboardInterrupt:
    print("\nScript stopped by user.")

finally:
    # Close browser when exiting the loop
    driver.quit()
