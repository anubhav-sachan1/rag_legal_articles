import os
import time
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from scraper_base import Scraper

class SimpsonThacherScraper(Scraper):

    def accept_cookies(self):
        try:
            cookie_button = self.driver.find_element(By.CSS_SELECTOR, '#klaro-cookie-notice button.cm-btn-success')
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

        continue_loading = True
        target_date = datetime.strptime('12.31.2021', '%m.%d.%Y').date()

        while continue_loading:
            elements = self.driver.find_elements(By.CSS_SELECTOR, 'ul.news-list-items li')
            last_date_on_page = datetime.min.date()

            for element in elements:
                doc_date = datetime.strptime(element.find_element(By.CSS_SELECTOR, "span.sfnewsMetaDate").text, '%m.%d.%y').date()
                if doc_date > last_date_on_page:
                    last_date_on_page = doc_date

                if doc_date > target_date:
                    link = element.find_element(By.CSS_SELECTOR, "a.anchor-when-reading_News")
                    title = link.text
                    link.click()
                    time.sleep(2)
                    html_element = self.driver.find_element(By.CSS_SELECTOR, "div[id^='cph_main'] div.show-when-reading-inner")
                    html_content = html_element.get_attribute('outerHTML')
                    close_button = self.driver.find_element(By.CSS_SELECTOR, "a.back-when-reading")
                    self.data.append({
                        'title': title,
                        'date': doc_date,
                        'html_content': html_content,
                    })
                    close_button.click()

            if last_date_on_page > target_date:
                try:
                    next_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "a.k-link.k-pager-nav[aria-label='Go to the next page']"))
                    )
                    next_button.click()
                    time.sleep(2)
                except Exception as e:
                    print(f"Could not find the 'Go to the next page' button or no more pages to load: {e}")
                    continue_loading = False
            else:
                continue_loading = False

    def download_htmls_and_prepare_csv(self):
        csv_data = []
        for entry in self.data:
            try:
                html_content = entry['html_content']
                file_name = self.download_page_as_html(html_content, f"{entry['title']}.html")
                csv_row = {'title': entry['title'], 'url': file_name, 'date': entry['date']}
                csv_data.append(csv_row)
            except Exception:
                print(f"Failed to retrieve PDF URL for {entry['title']}")
        
        self.write_csv(csv_data)

def main():
    base_url = 'https://www.stblaw.com/about-us/news'
    scraper = SimpsonThacherScraper(base_url)
    scraper.fetch_data()
    scraper.download_htmls_and_prepare_csv()
    scraper.write_chunks_csv("Simpson & Thacher", "div", "show-when-reading-inner", True)
    scraper.close()

if __name__ == "__main__":
    main()
