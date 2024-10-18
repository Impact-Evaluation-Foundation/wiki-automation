import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import time
import os
import re

def scrape_contact_info(index, website, project_name):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-webgl")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    chrome_options.add_argument("user-agent=Mozilla/5.0")

    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get(website)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # Scroll to ensure full content is loaded
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)

        # Extract emails and filter out image filenames
        raw_emails = set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', driver.page_source))
        valid_emails = {email for email in raw_emails if not re.search(r'\d+x\d+|\.(png|jpg|jpeg|gif|bmp|svg)$', email)}
        email = '; '.join(valid_emails) if valid_emails else None

        # Extract social media links
        social_links = driver.find_elements(By.XPATH, "//a[contains(@href, 'facebook.com') or "
                                                      "contains(@href, 'twitter.com') or "
                                                      "contains(@href, 'instagram.com') or "
                                                      "contains(@href, 'linkedin.com') or "
                                                      "contains(@href, 'youtube.com')]")
        social_sites = [link.get_attribute('href') for link in social_links]
        socials_string = '; '.join(social_sites)

        return {
            "Project Name": project_name,
            "Email": email,
            "Socials": socials_string
        }

    except Exception as e:
        return {
            "Project Name": project_name,
            "Email": None,
            "Socials": '',
            "Error": str(e)
        }

    finally:
        driver.quit()


df = pd.read_csv('resources/mixed_data.csv')

# Ensure output directory exists
os.makedirs('resources', exist_ok=True)

# Filter out rows with missing Website or Name
valid_rows = df.dropna(subset=['Website', 'Name'])

# Output CSV setup
output_csv = 'resources/contact_info.csv'

# Open the CSV file in append mode and write the headers if file doesn't exist
if not os.path.exists(output_csv):
    with open(output_csv, mode='w', newline='', encoding='utf-8') as f:
        f.write("Project Name,Email,Socials\n")

with ThreadPoolExecutor(max_workers=5) as executor:
    future_to_website = {executor.submit(scrape_contact_info, index, row['Website'], row['Name']): row['Website']
                         for index, row in valid_rows.iterrows()}

    with tqdm(total=len(future_to_website), desc="Scraping contact info", 
              bar_format="{l_bar}\033[95m{bar}\033[0m{r_bar}") as pbar:
        for future in as_completed(future_to_website):
            result = future.result()

            # Write the result directly to the CSV file row-by-row
            with open(output_csv, mode='a', newline='', encoding='utf-8') as f:
                f.write(f"{result['Project Name']},{result['Email']},{result['Socials']}\n")
            
            pbar.update(1)
