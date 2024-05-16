import os
import time
from selenium.webdriver.common.by import By
from datetime import datetime

from scraper_base import Scraper, ScraperType

class CooleyScraper(Scraper):

    def __init__(self, base_url, last_date_str='31.12.2021', date_format='%d.%m.%Y'):
        super().__init__(base_url, last_date_str, date_format)
        self.cookies_accepted = False  

    def accept_cookies(self):
        if not self.cookies_accepted:
            try:
                cookie_button = self.driver.find_element(By.CSS_SELECTOR, 'button#onetrust-accept-btn-handler')
                if cookie_button:
                    cookie_button.click()
                    self.cookies_accepted = True  
            except Exception as e:
                print(f"Error: {e}")
                print("Failed to accept cookies")

    def fetch_data(self):
        page_number = 0
        last_date = datetime.today().date()
        while True:
            url = self.base_url.format(page_number)
            self.driver.get(url)
            time.sleep(5)
            if not self.cookies_accepted:
                self.accept_cookies()

            elements = self.driver.find_elements(By.CSS_SELECTOR, 'div.coveo-list-layout.CoveoResult')
            page_last_date = datetime.today().date()
            for element in elements:
                try:
                    title = element.find_element(By.CSS_SELECTOR, "a.teaser-title.h3 span.CoveoFieldValue").text
                    doc_date = element.find_element(By.CSS_SELECTOR, "div.teaser-date").text
                    doc_date = datetime.strptime(doc_date, '%B %d, %Y').date()
                    doc_url = element.find_element(By.CSS_SELECTOR, "a.teaser-title.h3").get_attribute('href')

                    if doc_date < self.LAST_DATE:
                        return  

                    self.data.append({
                        'title': title,
                        'date': doc_date,
                        'url': doc_url,
                        'type': ScraperType.HTML
                    })

                    if doc_date < page_last_date:
                        page_last_date = doc_date

                except Exception as e:
                    print(f"Error processing element: {e}")

            if page_last_date < self.LAST_DATE:
                break  
            page_number += 10

    def download_html_and_save_csv(self):
        csv_data = []
        for entry in self.data:
            try:
                self.driver.get(entry['url'])
                html_element = self.driver.find_element(By.CSS_SELECTOR, "#maincontent > article > article.rich-text")
                html_content = html_element.get_attribute('outerHTML')
                self.download_page_as_html(html_content, f"{entry['title']}.html")
                csv_row = {'title': entry['title'], 'url': entry['url'], 'date': entry['date']}
                csv_data.append(csv_row)
            except Exception as e:
                print(f"Failed to retrieve HTML for {entry['title']}")
        
        self.write_csv(csv_data)

def main():
    base_url = 'https://www.cooley.com/news/search-media#first={}&sort=%40sortdatecoveo%20descending&f:cooley-coveo-facet-sections=[Insight]'
    scraper = CooleyScraper(base_url, last_date_str='31.12.2021', date_format='%d.%m.%Y')
    
    scraper.fetch_data()
    scraper.download_html_and_save_csv()
    scraper.write_chunks_csv("Cooley", "article", "rich-text wysiwyg-content")
    scraper.close()

if __name__ == "__main__":
    main()
