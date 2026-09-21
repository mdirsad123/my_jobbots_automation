import requests
from bs4 import BeautifulSoup
import pandas as pd

# Step 1: Fetch webpage content
def fetch_webpage(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        raise Exception(f"Failed to fetch webpage: {response.status_code}")

# Step 2: Parse and convert HTML tables into DataFrame
def convert_structure_format(tables):
    all_data = []

    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            cols = row.find_all(['th', 'td'])  # include both header and data cells
            cols = [ele.get_text(strip=True) for ele in cols]
            if cols:  # only append non-empty rows
                all_data.append(cols)

    # Convert list of lists to DataFrame
    df = pd.DataFrame(all_data)

    # Optional: use first row as header if it looks like column names
    if not df.empty:
        df.columns = df.iloc[0]  # set first row as header
        df = df[1:].reset_index(drop=True)

    print("Extracted DataFrame:")
    print(df)
    return df


# Step 3: Main script logic
if __name__ == "__main__":
    url = "https://www.reddit.com/"  # Replace with your actual URL

    # Fetch the webpage
    html_content = fetch_webpage(url)
    print("Webpage fetched successfully!")

    # Parse HTML using BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    print("HTML structure parsed successfully!")
    print(soup.prettify()[:1000])  # Print first 1000 characters of prettified HTML

    # Find all tables
    tables = soup.find_all('table')
    print(f"Total tables found: {len(tables)}")

    # If tables exist, convert and print DataFrame
    if tables:
        df = convert_structure_format(tables)
    else:
        print("No tables found on the webpage.")
