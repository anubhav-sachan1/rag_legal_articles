from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import csv
import os
import urllib.request
import time

class Scraper:
    def __init__(self, base_url):
        self.base_url = base_url
        self.driver = self.init_driver()
        self.data = []
    
    def init_driver(self):
        chrome_options = Options()
        # chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
        return driver
    
    def download_pdf_with_user_agent(self, url, filename):
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
        request = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(request) as response, open(filename, 'wb') as f:
            f.write(response.read())
    
    def close(self):
        self.driver.quit()

class SidleyScraper(Scraper):

    def fetch_data(self, page_number):
        url = f'{self.base_url}&skip={page_number}'
        self.driver.get(url)
        time.sleep(2)
        elements = self.driver.find_elements(By.CLASS_NAME, 'search-result')
        
        for element in elements:
            title = element.find_element(By.CLASS_NAME, 'result-title').text
            link = element.find_element(By.CSS_SELECTOR, "a[data-bind*='NavigateLink.Url']")
            doc_date = element.find_element(By.CSS_SELECTOR, "span[data-bind='text: DisplayDate']").text
            doc_url = link.get_attribute('href')
            self.data.append({
                'title': title,
                'date': doc_date,
                'url': doc_url
            })

    def write_csv(self, csv_file, data):
        with open(csv_file, 'w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=['title', 'url', 'date'])
            writer.writeheader()
            writer.writerows(data)

    def download_pdfs_and_prepare_csv(self, download_folder, csv_file):
        csv_data = []
        for entry in self.data:
            try:
                self.driver.get(entry['url'])
                links = self.driver.find_elements(By.CSS_SELECTOR, "div.inner-wrapper a")
                urls = [link.get_attribute('href') for link in links]
                pdf_url = [url for url in urls if '.pdf' in url][0]
                csv_row = {'title': entry['title'], 'url': pdf_url, 'date': entry['date']}
                self.download_pdf_with_user_agent(pdf_url, os.path.join(download_folder, f"{entry['title']}.pdf"))
                csv_data.append(csv_row)
            except Exception:
                print(f"Failed to retrieve PDF URL for {entry['title']}")
        
        self.write_csv(csv_file, csv_data)


def prepare_output(base_url):
    root_folder_name = base_url.split('/')[2].split('.')[1]
    download_folder = os.path.join(root_folder_name, 'files')
    csv_file = os.path.join(root_folder_name, 'publications.csv')
    os.makedirs(download_folder, exist_ok=True)
    return download_folder, csv_file

def main():
    base_url = 'https://www.sidley.com/en/us/insights/?articletypes=9cbfe518-3bc0-4632-ae13-6ac9cee8eb31'
    scraper = SidleyScraper(base_url)
    page_number = 10
    download_folder, csv_file = prepare_output(base_url)
    scraper.fetch_data(page_number)
    scraper.download_pdfs_and_prepare_csv(download_folder, csv_file)
    scraper.close()

if __name__ == "__main__":
    main()
