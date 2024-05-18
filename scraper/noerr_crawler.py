import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime

from scraper_base import Scraper, ScraperType

class NoerrScraper(Scraper):

    def accept_cookies(self):
        try:
            # Wait until the cookie button is clickable and then click it
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'a#cookie-apply-all'))
            ).click()
        except Exception as e:
            print("Cookie button not found or not clickable.")

    def fetch_data(self):
        self.driver.get(self.base_url)
        time.sleep(5)
        self.accept_cookies()

        last_date = datetime.today().date()
        last_article_date = last_date
        continue_loading = True

        while continue_loading:
            elements = self.driver.find_elements(By.CSS_SELECTOR, "main section:nth-child(3) > div.MuiContainer-root > div.MuiBox-root > div.MuiBox-root > div:nth-child(4) > div")
            if elements:
                last_element = elements[-1]
                doc_date_str = last_element.find_element(By.CSS_SELECTOR, "div.teaser-fixed-width > div:nth-child(2) > div").text
                last_article_date = datetime.strptime(doc_date_str, '%d.%m.%Y').date()
            
            if last_article_date <= datetime(2021, 12, 31).date():
                continue_loading = False
            else:
                try:
                    load_more_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.css-gf569q'))
                    )
                    load_more_button.click()
                    time.sleep(5)  # Wait for the content to load
                except Exception as e:
                    print("No more 'Load More' button found.")
                    continue_loading = False

        # Collect articles only after finishing loading
        for element in elements:
            link = element.find_element(By.CSS_SELECTOR, 'div.teaser-fixed-width h4 a')
            title = link.text
            doc_date = element.find_element(By.CSS_SELECTOR, "div.teaser-fixed-width > div:nth-child(2) > div").text
            doc_date = datetime.strptime(doc_date, '%d.%m.%Y').date()

            if doc_date > datetime(2021, 12, 31).date():
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
        csv_data = []
        for entry in self.data:
            self.driver.get(entry['url'])
            html_element = self.driver.find_element(By.CSS_SELECTOR, "main section:nth-child(2) > div.MuiContainer-root > div.MuiBox-root > div.MuiGrid-container > div:nth-child(2) > div.rte")
            html_content = html_element.get_attribute('outerHTML')
            self.download_page_as_html(html_content, f"{entry['title']}.html")
            csv_row = {'title': entry['title'], 'url': entry['url'], 'date': entry['date']}
            csv_data.append(csv_row)
        
        self.write_csv(csv_data)

def main():
    base_url = 'https://www.noerr.com/en/insights?i-fc-type=News'
    scraper = NoerrScraper(base_url)
    scraper.fetch_data()
    scraper.download_html_and_save_csv()
    scraper.write_chunks_csv("Noerr","div","rte MuiBox-root css-g65ho")
    scraper.close()

if __name__ == "__main__":
    main()
