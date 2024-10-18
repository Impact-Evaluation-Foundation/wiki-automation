from unicodedata import category
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import csv
import time
from tqdm import tqdm
import re
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=chrome_options)

def get_total_projects(driver):
    title = driver.find_element(By.TAG_NAME, "h1").text
    match = re.search(r'\((\d+)\)', title)
    return int(match.group(1)) if match else None

def scrape_projects(url):
    driver = setup_driver()
    projects = []

    try:
        driver.get(url)
        logging.info(f"Navigated to URL: {url}")
        
        total_projects = get_total_projects(driver)
        logging.info(f"Total projects to scrape: {total_projects}")
        
        with tqdm(total=total_projects, desc="Scraping projects", ncols=100) as pbar:
            while True:
                try:
                    WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.TAG_NAME, "table"))
                    )
                    logging.info("Table element found on the page")
                    
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                    
                    rows = driver.find_elements(By.TAG_NAME, "tr")
                    logging.info(f"Found {len(rows)} rows in the table")
                    
                    for row in rows[1:]:  # Skip header row
                        try:
                            columns = row.find_elements(By.TAG_NAME, "td")
                            if len(columns) >= 5:
                                image = columns[0].find_element(By.TAG_NAME, "img").get_attribute("src")
                                name_element = columns[1].find_element(By.TAG_NAME, "a")
                                name = name_element.text.strip()
                                project_link = name_element.get_attribute("href")
                                description = columns[2].text.strip()
                                
                                # Navigate to the project page
                                driver.get(project_link)
                                logging.info(f"Navigated to project page: {project_link}")
                                
                                # Extract website URL
                                website_url = None
                                try:
                                    globe_icon = WebDriverWait(driver, 10).until(
                                        EC.presence_of_element_located((By.CSS_SELECTOR, "i.bi.bi-globe"))
                                    )
                                    website_link = globe_icon.find_element(By.XPATH, "..")
                                    website_url = website_link.get_attribute('href')
                                except:
                                    logging.warning(f"Could not find website for project: {name}")
                                
                                # Navigate back to the main page
                                driver.back()
                                
                                projects.append({
                                    'Project image': image,
                                    'Project name': name,
                                    'Project link': project_link,
                                    'Description': description,
                                    'Website': website_url
                                })
                                pbar.update(1)
                        except Exception as e:
                            logging.error(f"Error processing a row: {str(e)}")
                    
                    next_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Next']"))
                    )
                    if not next_button.is_enabled():
                        logging.info("Reached the last page")
                        break
                    next_button.click()
                    logging.info("Clicked the 'Next' button")
                    time.sleep(2)  # Wait for the page to load
                except TimeoutException:
                    logging.error("Timeout waiting for elements on the page")
                    break
                except NoSuchElementException:
                    logging.error("Could not find the 'Next' button")
                    break
                except Exception as e:
                    logging.error(f"Unexpected error during scraping: {str(e)}")
                    break
                
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
    finally:
        driver.quit()
    
    logging.info(f"Total projects scraped: {len(projects)}")
    return projects

def save_to_csv(projects, filename):
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Project image', 'Project name', 'Project link', 'Description', 'Website']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for project in projects:
            writer.writerow(project)

if __name__ == "__main__":
    url = "https://carboncopy.news/projects"
    projects = scrape_projects(url)
    save_to_csv(projects, 'resources/carboncopy_projects.csv')
    print(f"\nScraped {len(projects)} projects and saved to carboncopy_projects.csv")