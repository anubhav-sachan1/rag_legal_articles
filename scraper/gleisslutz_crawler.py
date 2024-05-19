import os
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
from selenium.webdriver.common.action_chains import ActionChains

from scraper_base import Scraper, ScraperType

class GleissLutzScraper(Scraper):

    def accept_cookies(self):
        try:
            cookie_button = self.driver.find_element(By.CSS_SELECTOR, '#ccm-widget button.ccm--save-settings')
            if cookie_button:
                cookie_button.click()
        except Exception as e:
            print(f"Error: {e}")
            print("Failed to accept cookies")

    def fetch_data(self):
        url = self.base_url
        self.driver.get(url)
        time.sleep(2)
        self.accept_cookies()

        last_date = datetime.today().date()
        target_date = datetime.strptime('31.12.2021', '%d.%m.%Y').date()

        while True:
            elements = self.driver.find_elements(By.CSS_SELECTOR, "div.js-content-container-all article.node--type-knowhow")
            page_data_fetched = False  
            for element in elements:
                link = element.find_element(By.CSS_SELECTOR, 'a.teaser__more-link')
                title = element.find_element(By.CSS_SELECTOR, "span.teaser__headline").text
                doc_date = element.find_element(By.CSS_SELECTOR, "time").text
                doc_date = self.convert_to_date_type(doc_date, '%d.%m.%Y').date()

                if doc_date > target_date:
                    doc_url = link.get_attribute('href')
                    if not doc_url.startswith('http'):
                        doc_url = f"{self.get_scheme_and_domain()}{doc_url}"
                    self.data.append({
                        'title': title,
                        'date': doc_date,
                        'url': doc_url,
                        'type': ScraperType.HTML
                    })
                    page_data_fetched = True

                if doc_date < last_date:
                    last_date = doc_date

            if not page_data_fetched or last_date <= target_date:
                break

            try:
                next_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Next')]/ancestor::a"))
                )
                ActionChains(self.driver).move_to_element(next_button).perform()
                self.driver.execute_script("arguments[0].click();", next_button)
                time.sleep(2)
            except Exception as e:
                print(f"Could not find the 'Next ›' button or no more pages to load: {e}")
                break

        return last_date

    def download_html_and_save_csv(self):
        csv_data = []
        for entry in self.data:
            try:
                self.driver.get(entry['url'])
                html_element = self.driver.find_element(By.CSS_SELECTOR, "div.paragraph__content-container")
                html_content = html_element.get_attribute('outerHTML')
                title = self.driver.find_element(By.CSS_SELECTOR, "h1").text  
                file_path = self.download_page_as_html(html_content, f"{title}.html")
                doc_date = self.driver.find_element(By.CSS_SELECTOR, "time").text
                doc_date = self.convert_to_date_type(doc_date, '%d.%m.%Y').date()
                csv_row = {'title': title, 'url': entry['url'], 'date': doc_date}
                csv_data.append(csv_row)
            except Exception as e:
                print(f"Failed to process {entry['url']}: {e}")

        self.write_csv(csv_data)

def main():
    base_url = 'https://www.gleisslutz.com/en/news-events/know-how'
    scraper = GleissLutzScraper(base_url)
    scraper.fetch_data()
    scraper.download_html_and_save_csv()
    scraper.close()

if __name__ == "__main__":
    main()
