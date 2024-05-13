import os
import time
from selenium.webdriver.common.by import By
from datetime import datetime

from scraper_base import Scraper, ScraperType

class CmsScraper(Scraper):

    def accept_cookies(self):
        try:
            cookie_button = self.driver.find_element(By.CSS_SELECTOR, 'a#cookie-apply-all')
            # If button exists, click it
            if cookie_button:
                cookie_button.click()
        except Exception as e:
            print(f"Error: {e}")
            print("Failed to accept cookies")


    def fetch_data(self):
        url = self.base_url
        self.driver.get(url)
        time.sleep(5)
        self.accept_cookies()

        elements = self.driver.find_elements(By.CSS_SELECTOR, "div.tile--bucket-publication")
        last_date = datetime.today().date()
        
        for element in elements:
            link = element.find_element(By.CSS_SELECTOR, 'a.tile__link')
            title = element.find_element(By.CSS_SELECTOR, "div.tile__heading").text
            doc_date = element.find_element(By.CSS_SELECTOR, "div.tile__date").text
            doc_date = self.convert_to_date_type(doc_date, '%d/%m/%Y').date()
            if doc_date < last_date:
                last_date = doc_date
            doc_url = link.get_attribute('href')
            if not doc_url.startswith('http'):
                    doc_url = f"{self.get_scheme_and_domain()}{doc_url}"
            self.data.append({
                'title': title,
                'date': doc_date,
                'url': doc_url,
                'type': ScraperType.HTML
            })
        return last_date


    def download_html_and_save_csv(self):
        csv_data = []
        for entry in self.data:
            try:
                self.driver.get(entry['url'])
                html_element = self.driver.find_element(By.CSS_SELECTOR, "div.block_rich_publication_text_block")
                html_content = html_element.get_attribute('outerHTML')
                file_path = self.download_page_as_html(html_content, f"{entry['title']}.html")
                csv_row = {'title': entry['title'], 'url': file_path, 'date': entry['date']}
                csv_data.append(csv_row)
            except Exception:
                print(f"Failed to retrieve PDF URL for {entry['title']}")
        
        self.write_csv(csv_data)

def main():
    base_url = 'https://cms.law/en/int/publication'
    scraper = CmsScraper(base_url)
    scraper.fetch_data()
    scraper.download_html_and_save_csv()
    scraper.close()

if __name__ == "__main__":
    main()
