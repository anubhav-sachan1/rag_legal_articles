import requests
from bs4 import BeautifulSoup
from lxml import html

def scrape_page(url):
    # Send a GET request to the website
    headers = {
        'User-Agent': 'Chrome/124.0.6367.202'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        # Parse the HTML content of the page
        soup = BeautifulSoup(response.text, 'html.parser')
        # Find elements containing publications, assuming they are in <div> tags with a specific class
        publications = soup.find_all('ul', class_='search-results-list')
        tree = html.fromstring(response.content)
        xpath_expression = "/html/body/main/div[3]/section/div[4]/div/div/ul/li"
        # Execute the XPath selection
        list_items = tree.xpath(xpath_expression)
        
        for item in list_items:
            # Extract and print the text of each <li> element
            print(item.text_content().strip()) 
    else:
        print("Failed to retrieve the webpage. Status code: ", response.status_code)

def main():
    # Initial URL of the website (page 1)
    url = 'https://www.sidley.com/en/us/insights/?articletypes=9cbfe518-3bc0-4632-ae13-6ac9cee8eb31&skip='
    page_number = 10
    print(f"Scraping page {page_number}")
    scrape_page(url + str(page_number))

if __name__ == "__main__":
    main()

