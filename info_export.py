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

def scrape_project_info(index, website, project_name):
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
        
        # Scroll to the bottom to ensure all elements are loaded
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)  # Wait for any lazy-loaded content
        
        # Extract relevant information
        info = f"Project Name: {project_name}\n"
        info += f"Website: {website}\n\n"
        
        # Meta description
        try:
            meta_description = driver.find_element(By.XPATH, "//meta[@name='description']").get_attribute("content")
            info += f"Meta Description: {meta_description}\n\n"
        except:
            pass
        
        # Title
        info += f"Page Title: {driver.title}\n\n"
        
        # All headers (h1, h2, h3)
        headers = driver.find_elements(By.XPATH, "//h1 | //h2 | //h3")
        info += "Headers:\n" + "\n".join([h.text for h in headers if h.text.strip()]) + "\n\n"
        
        # Main content (paragraphs, lists, etc.)
        main_content = driver.find_elements(By.XPATH, "//p | //ul | //ol")
        info += "Main Content:\n" + "\n".join([elem.text for elem in main_content if elem.text.strip()]) + "\n\n"
        
        # About section (common in many websites)
        about_sections = driver.find_elements(By.XPATH, "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'about')]")
        if about_sections:
            info += "About Section:\n"
            for section in about_sections[:3]:  # Limit to first 3 matches
                info += section.text + "\n\n"
        
        # Mission or Vision statements
        mission_elements = driver.find_elements(By.XPATH, "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'mission') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'vision')]")
        if mission_elements:
            info += "Mission/Vision:\n"
            for element in mission_elements[:2]:  # Limit to first 2 matches
                info += element.text + "\n\n"
        

        filename = f"info/{project_name.replace(' ', '_')}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(info)
        
        return f"Information saved for {website} as {filename}"
    except Exception as e:
        return f"Error scraping {website}: {e}"
    finally:
        driver.quit()

df = pd.read_csv('resources/mixed_data.csv')


os.makedirs('info', exist_ok=True)

# Filter out rows with missing Website or Name
valid_rows = df.dropna(subset=['Website', 'Name'])


with ThreadPoolExecutor(max_workers=5) as executor:
    future_to_website = {executor.submit(scrape_project_info, index, row['Website'], row['Name']): row['Website']
                         for index, row in valid_rows.iterrows()}
    
   
    with tqdm(total=len(future_to_website), desc="Scraping project info", 
              bar_format="{l_bar}\033[95m{bar}\033[0m{r_bar}") as pbar:
        for future in as_completed(future_to_website):
            result = future.result()
            pbar.update(1)

