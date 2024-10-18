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

def capture_full_page_screenshot(index, website, project_name):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--log-level=3")  # Only show fatal errors
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    driver = webdriver.Chrome(options=chrome_options)
    try:
        driver.get(website)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        # Attempt to close cookie prompts (some websites open a cookie prompt)
        # try:
        #    cookie_buttons = driver.find_elements(By.XPATH, "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accept') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'agree') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'got it')]")
        #    for button in cookie_buttons:
        #        driver.execute_script("arguments[0].click();", button)
        # except:
        #    pass

        # Get the height of the entire page
        total_height = driver.execute_script("return document.body.parentNode.scrollHeight")
        
        # Set the viewport size to the full height
        driver.set_window_size(1920, total_height)
        
        # Scroll to the bottom to ensure all elements are loaded
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)  # Wait for any lazy-loaded content
        
        # Use project_name for the filename, replacing spaces with underscores
        filename = f"screenshots/{project_name.replace(' ', '_')}.png"
        driver.get_screenshot_as_file(filename)
        return f"Full page screenshot saved for {website} as {filename}"
    except Exception as e:
        return f"Error capturing {website}: {e}"
    finally:
        driver.quit()


df = pd.read_csv('resources/mixed_data.csv')

os.makedirs('screenshots', exist_ok=True)

# Filter out rows with missing Website or Name
valid_rows = df.dropna(subset=['Website', 'Name'])

with ThreadPoolExecutor(max_workers=5) as executor:
    future_to_website = {executor.submit(capture_full_page_screenshot, index, row['Website'], row['Name']): row['Website']
                         for index, row in valid_rows.iterrows()}
    
    with tqdm(total=len(future_to_website), desc="Capturing screenshots", 
              bar_format="{l_bar}\033[94m{bar}\033[0m{r_bar}") as pbar:
        for future in as_completed(future_to_website):
            result = future.result()
            pbar.update(1)

