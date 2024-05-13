import os
import time
from selenium.webdriver.common.by import By

from scraper_base import Scraper

class SimpsonThacherScraper(Scraper):

    def accept_cookies(self):
        try:
            # Modify the selector to match the cookie acceptance button on the specific website
            cookie_button = self.driver.find_element(By.CSS_SELECTOR, '#klaro-cookie-notice button.cm-btn-success')
            # If button exists, click it
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

        
        elements = self.driver.find_elements(By.CSS_SELECTOR, 'ul.news-list-items li')
        original_window = self.driver.current_window_handle
        for idx in range(1, len(elements)):
            try:
                element = elements[idx]
                link = element.find_element(By.CSS_SELECTOR, "a.anchor-when-reading_News")
                title = link.text
                doc_date = element.find_element(By.CSS_SELECTOR, "span.sfnewsMetaDate").text
                doc_date = self.convert_to_date_type(doc_date, '%d.%m.%y').date()
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
            except Exception as e:
                print(f"Error: {e}")

    def download_pdfs_and_prepare_csv(self):
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
    try:
        scraper.fetch_data()
        scraper.download_pdfs_and_prepare_csv()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        scraper.close()

if __name__ == "__main__":
    main()
