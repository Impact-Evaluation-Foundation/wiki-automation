import csv
import pandas as pd

def read_carboncopy_csv(file_path):
    data = []
    with open(file_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            data.append({
                'Name': row['Project name'],
                'Description': row['Description'],
                'Website': row['Website']
            })
    return data

def read_positiveblockchain_csv(file_path):
    df = pd.read_csv(file_path)
    data = []
    for _, row in df.iterrows():
        data.append({
            'Name': row['Project name'],
            'Description': row['DESCRIPTION SHORT = VALUE PROPOSITION IN A TWEET'],
            'Website': row['Website']
        })
    return data

def combine_and_save(carboncopy_data, positiveblockchain_data, output_file):
    # Filter carboncopy_data
    cc_dict = {
        item['Website'].lower(): item 
        for item in carboncopy_data 
        if item.get('Website') and isinstance(item['Website'], str)
    }

    # Filter positiveblockchain_data
    pb_dict = {
        item['Website'].lower(): item 
        for item in positiveblockchain_data 
        if item.get('Website') and isinstance(item['Website'], str)
    }

    # Combine the datasets
    mixed_data = list(cc_dict.values()) + [
        item for item in pb_dict.values() 
        if item['Website'].lower() not in cc_dict
    ]

    # Remove duplicates based on Website (case-insensitive)
    unique_data = {}
    for item in mixed_data:
        website_lower = item['Website'].lower() if item['Website'] else item['Name'].lower()
        if website_lower not in unique_data:
            unique_data[website_lower] = item
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Name', 'Description', 'Website']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for item in unique_data.values():
            writer.writerow(item)

def main():
    carboncopy_file = 'resources/carboncopy_projects.csv'
    positiveblockchain_file = 'resources/PositiveBlockchain_data.csv'
    output_file = 'resources/mixed_data.csv'

    carboncopy_data = read_carboncopy_csv(carboncopy_file)
    positiveblockchain_data = read_positiveblockchain_csv(positiveblockchain_file)

    combine_and_save(carboncopy_data, positiveblockchain_data, output_file)
    print(f"Combined data saved to {output_file}")

if __name__ == "__main__":
    main()
