import os
import time
from selenium.webdriver.common.by import By

from scraper_base import Scraper

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

    def download_pdfs_and_prepare_csv(self):
        csv_data = []
        for entry in self.data:
            try:
                self.driver.get(entry['url'])
                links = self.driver.find_elements(By.CSS_SELECTOR, "div.inner-wrapper a")
                urls = [link.get_attribute('href') for link in links]
                pdf_url = [url for url in urls if '.pdf' in url][0]
                csv_row = {'title': entry['title'], 'url': pdf_url, 'date': entry['date']}
                self.download_pdf_with_user_agent(pdf_url, f"{entry['title']}.pdf")
                csv_data.append(csv_row)
            except Exception:
                print(f"Failed to retrieve PDF URL for {entry['title']}")
        
        self.write_csv(csv_data)

def main():
    base_url = 'https://www.sidley.com/en/us/insights/?articletypes=9cbfe518-3bc0-4632-ae13-6ac9cee8eb31'
    scraper = SidleyScraper(base_url)
    page_number = 10  
    scraper.fetch_data(page_number)
    scraper.download_pdfs_and_prepare_csv()
    scraper.close()

if __name__ == "__main__":
    main()
