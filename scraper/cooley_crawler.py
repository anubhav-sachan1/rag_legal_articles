import os
import time
from selenium.webdriver.common.by import By

from scraper_base import Scraper

class CooleyScraper(Scraper):

    def accept_cookies(self):
        try:
            # Modify the selector to match the cookie acceptance button on the specific website
            cookie_button = self.driver.find_element(By.CSS_SELECTOR, 'button#onetrust-accept-btn-handler')
            # If button exists, click it
            if cookie_button:
                cookie_button.click()
        except Exception as e:
            print(f"Error: {e}")
            print("Failed to accept cookies")

    def fetch_data(self, page_number):
        url = self.base_url.format(page_number)
        self.driver.get(url)
        time.sleep(5)
        # self.accept_cookies()

        
        elements = self.driver.find_elements(By.CSS_SELECTOR, 'div.coveo-list-layout.CoveoResult')
        original_window = self.driver.current_window_handle
        for idx in range(1, len(elements)):
            element = elements[idx]
            link = element.find_element(By.CSS_SELECTOR, "a.teaser-title.h3")
            title = link.find_element(By.CSS_SELECTOR, "span.CoveoFieldValue").text
            doc_date = element.find_element(By.CSS_SELECTOR, "div.teaser-date").text
            # self.driver.switch_to.window(self.driver.window_handles[-1]) 
            # Get the URL of the new tab
            doc_url = link.get_attribute('href')
            self.data.append({
                'title': title,
                'date': doc_date,
                'url': doc_url,
            })

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
            except Exception:
                print(f"Failed to retrieve PDF URL for {entry['title']}")
        
        self.write_csv(csv_data)

def main():
    base_url = 'https://www.cooley.com/news/search-media#first={}&sort=%40sortdatecoveo%20descending&f:cooley-coveo-facet-sections=[Insight]'
    scraper = CooleyScraper(base_url)
    try:
        page_number = 10
        scraper.fetch_data(page_number)
        scraper.download_html_and_save_csv()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        scraper.close()

if __name__ == "__main__":
    main()
