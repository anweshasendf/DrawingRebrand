import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import time
import csv
import os
import random

# SharePoint link
sharepoint_url = "https://danfoss-my.sharepoint.com/personal/priyanshu_chatuphale_danfoss_com/_layouts/15/onedrive.aspx?e=5%3Af56338cb32c2425284d2f1e90cbac49e&sharingv2=true&fromShare=true&at=9&clickparams=eyAiWC1BcHBOYW1lIiA6ICJNaWNyb3NvZnQgT3V0bG9vayIsICJYLUFwcFZlcnNpb24iIDogIjE2LjAuMTc3MjYuMjAyMDYiLCAiT1MiIDogIldpbmRvd3MiIH0&CID=37de46a1%2Dc03f%2D9000%2D8dfa%2D3125fc7b4745&cidOR=SPO&id=%2Fpersonal%2Fpriyanshu%5Fchatuphale%5Fdanfoss%5Fcom%2FDocuments%2FMetal%20Rebranding%5FAutoCAD%2F15000%5FDS%5F1&FolderCTID=0x012000272D88745F2092418772780C0E0073E5&view=0&isAscending=true&sortField=Modified&noAuthRedirect=1"

#DS2sharepoint_url = "https://danfoss-my.sharepoint.com/personal/priyanshu_chatuphale_danfoss_com/_layouts/15/onedrive.aspx?e=5%3Acdba51cdceec47e8a74b7f2f840260fc&sharingv2=true&fromShare=true&at=9&clickparams=eyAiWC1BcHBOYW1lIiA6ICJNaWNyb3NvZnQgT3V0bG9vayIsICJYLUFwcFZlcnNpb24iIDogIjE2LjAuMTc3MjYuMjAyMDYiLCAiT1MiIDogIldpbmRvd3MiIH0%3D&CID=b7ee46a1%2Dc093%2D9000%2Dac50%2D137e96314cec&cidOR=SPO&id=%2Fpersonal%2Fpriyanshu%5Fchatuphale%5Fdanfoss%5Fcom%2FDocuments%2FMetal%20Rebranding%5FAutoCAD%2F%5FDS%5F2&FolderCTID=0x012000272D88745F2092418772780C0E0073E5&view=0"

# Local CSV file path
csv_file_path = "file_names_15k.csv"

# Set up Chrome options
options = uc.ChromeOptions()
options.add_argument("profile-directory=Default")

def scroll_to_last_element(driver):
    elements = driver.find_elements(By.CLASS_NAME, "heroTextWithHeroCommandsWrapped_82022aff")
    if elements:
        last_element = elements[-1]
        driver.execute_script("arguments[0].scrollIntoView();", last_element)
        driver.execute_script("window.scrollBy(0, 200);")  # Scroll a bit more to trigger loading
        time.sleep(random.uniform(1, 3))  # Random wait after scrolling
        return True
    return False

def save_progress(file_names):
    with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["File Name"])
        for name in file_names:
            csv_writer.writerow([name])

def load_progress():
    if os.path.exists(csv_file_path):
        with open(csv_file_path, 'r', newline='', encoding='utf-8') as csvfile:
            csv_reader = csv.reader(csvfile)
            next(csv_reader)  # Skip header
            return set(row[0] for row in csv_reader)
    return set()

try:
    driver = uc.Chrome(options=options)
    
    # Navigate to the SharePoint page
    driver.get(sharepoint_url)

    # Wait for the file list to load
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CLASS_NAME, "heroTextWithHeroCommandsWrapped_82022aff"))
    )

    # Zoom out to see more files
    driver.execute_script("document.body.style.zoom = '15%'")
    time.sleep(2)  # Wait for zoom to take effect

    file_names = load_progress()
    scroll_attempt = 0
    max_scroll_attempts = 20500
    consecutive_no_new_names = 0
    max_consecutive_no_new_names = 510

    while True:
        try:
            # Find all file name elements
            elements = driver.find_elements(By.CLASS_NAME, "heroTextWithHeroCommandsWrapped_82022aff")
            
            # Add new file names to the set
            new_names_count = 0
            for element in elements:
                name = element.text.strip()
                if name and name not in file_names:
                    file_names.add(name)
                    new_names_count += 1
                    print(f"Found name: {name}")
            
            print(f"Added {new_names_count} new names in this iteration")
            print(f"Total unique file names: {len(file_names)}")

            if new_names_count == 0:
                consecutive_no_new_names += 1
            else:
                consecutive_no_new_names = 0

            # Try to scroll to the last element
            if scroll_to_last_element(driver):
                print("Scrolled to the last element")
            else:
                print("Failed to scroll")

            # Save progress every 100 attempts
            if scroll_attempt % 100 == 0:
                save_progress(file_names)
                print("Progress saved")

        except StaleElementReferenceException:
            # If elements become stale, retry
            continue

        scroll_attempt += 1
        print(f"Scroll attempt: {scroll_attempt}")

        # Break if we've found 15,000 or more unique names
        if len(file_names) >= 15000:
            print("Reached 15,000 unique file names. Ending search.")
            break

        # Break if we've reached the maximum number of scroll attempts
        if scroll_attempt >= max_scroll_attempts:
            print("Reached maximum scroll attempts. Ending search.")
            break

        # Break if no new names were found in consecutive attempts
        if consecutive_no_new_names >= max_consecutive_no_new_names:
            print(f"No new names found in {max_consecutive_no_new_names} consecutive attempts. Ending search.")
            break

        time.sleep(random.uniform(2, 7))  # Random wait between scrolls

    # Final save of progress
    save_progress(file_names)

    print(f"Found {len(file_names)} unique file names. Saved to {csv_file_path}")

except TimeoutException:
    print("Timed out waiting for page to load")
except Exception as e:
    print(f"An error occurred: {e}")
finally:
    if 'driver' in locals():
        driver.quit()