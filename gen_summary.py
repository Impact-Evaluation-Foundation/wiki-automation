import pandas as pd
import os
from openai import OpenAI
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
import time
import re

# Load environment variables from .env file
load_dotenv()

# Initialize the OpenAI client with the API key from environment variable
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def sanitize_file_name(file_name):
    # Replace or remove special characters
    sanitized_name = re.sub(r'[<>:"/\\|?*]', '_', file_name)
    return sanitized_name

def read_project_info(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None
    except OSError as e:
        print(f"Error reading file {file_path}: {str(e)}")
        return None

def generate_summary(project_name, project_info):
    if project_info is None:
        return project_name, "NO INFO"

    try:
        prompt = f"""Generate a concise two-paragraph summary of the project based on the scraped data below. The first paragraph should focus on the project's mission and key features. The second paragraph should highlight any unique technologies, solutions, or partnerships. If the data is incomplete, irrelevant, or contains errors (e.g., 404 page, domain for sale), return "NO INFO". Provide only the summary or "NO INFO".

{project_info}"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes project information."},
                {"role": "user", "content": prompt}
            ]
            )

        return project_name, response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating summary for {project_name}: {str(e)}")
        return project_name, "ERROR"

def process_project(project_name, project_info_path):
    project_info = read_project_info(project_info_path)
    return generate_summary(project_name, project_info)

def main():
    df = pd.read_csv('resources/mixed_data.csv')

    os.makedirs('summaries', exist_ok=True)

    projects = [(row['Name'], f'info/{sanitize_file_name(row["Name"].replace(" ", "_"))}.txt') for _, row in df.iterrows()]


    with ThreadPoolExecutor(max_workers=5) as executor:
        
        future_to_project = {executor.submit(process_project, name, info_path): name for name, info_path in projects}

        with tqdm(total=len(future_to_project), desc="Generating summaries", 
                  bar_format="{l_bar}\033[92m{bar}\033[0m{r_bar}") as pbar:
            for future in as_completed(future_to_project):
                project_name, summary = future.result()
                if summary not in ["NO INFO", "ERROR"]:
                    sanitized_project_name = sanitize_file_name(project_name.replace(" ", "_"))
                    output_file = f'summaries/{sanitized_project_name}.txt'
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(summary)
                    print(f"\nSummary for {project_name} saved to {output_file}")
                else:
                    print(f"\nNo valid information found for {project_name}")
                pbar.update(1)

if __name__ == "__main__":
    main()
