import os
import time
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from scraper_base import Scraper, ScraperType

class CmsScraper(Scraper):

    def accept_cookies(self):
        try:
            cookie_button = self.driver.find_element(By.CSS_SELECTOR, 'a#cookie-apply-all')
            if cookie_button:
                cookie_button.click()
        except Exception as e:
            print(f"Error: {e}")
            print("Failed to accept cookies")

    def load_all_articles(self):
        """ Load all articles up to a certain date by clicking the 'Load more articles' button. """
        self.driver.get(self.base_url)
        time.sleep(5)
        self.accept_cookies()

        target_date = datetime.strptime('31/12/2021', '%d/%m/%Y').date()
        last_date = datetime.today().date()

        while last_date > target_date:
            try:
                last_element = self.driver.find_elements(By.CSS_SELECTOR, "div.tile__date")[-1]
                last_date = datetime.strptime(last_element.text, '%d/%m/%Y').date()
                if last_date > target_date:
                    load_more_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn.load-more.js-load-more"))
                    )
                    load_more_button.click()
                    time.sleep(5)  # Wait for more articles to load
            except Exception as e:
                print("Could not find the 'Load more articles' button or no more pages to load")
                print(e)
                break

    def fetch_data(self):
        """ Fetch data from all loaded articles. """
        elements = self.driver.find_elements(By.CSS_SELECTOR, "div.tile--bucket-publication")
        for element in elements:
            link = element.find_element(By.CSS_SELECTOR, 'a.tile__link')
            title = element.find_element(By.CSS_SELECTOR, "div.tile__heading").text
            doc_date = element.find_element(By.CSS_SELECTOR, "div.tile__date").text
            doc_date = datetime.strptime(doc_date, '%d/%m/%Y').date()
            doc_url = link.get_attribute('href')
            if not doc_url.startswith('http'):
                doc_url = f"{self.get_scheme_and_domain()}{doc_url}"
            self.data.append({
                'title': title,
                'date': doc_date,
                'url': doc_url,
                'type': ScraperType.HTML
            })

    def download_html_and_save_csv(self):
        """ Download HTML content and save to CSV. """
        csv_data = []
        for entry in self.data:
            try:
                self.driver.get(entry['url'])
                html_element = self.driver.find_element(By.CSS_SELECTOR, "div.block_rich_publication_text_block")
                html_content = html_element.get_attribute('outerHTML')
                file_path = self.download_page_as_html(html_content, f"{entry['title']}.html")
                csv_row = {'title': entry['title'], 'url': entry['url'], 'date': entry['date']}
                csv_data.append(csv_row)
            except Exception as e:
                pass

        self.write_csv(csv_data)

def main():
    base_url = 'https://cms.law/en/int/publication'
    scraper = CmsScraper(base_url)
    scraper.load_all_articles()  # Load all relevant articles first
    scraper.fetch_data()         # Then fetch data from all loaded articles
    scraper.download_html_and_save_csv()
    scraper.write_chunks_csv("CMS", "div", "block_rich_publication block_rich_publication_text_block rich-publication-richtext block-view_full", True)
    scraper.close()

if __name__ == "__main__":
    main()
