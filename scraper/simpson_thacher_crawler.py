import os
import time
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from scraper_base import Scraper

class SimpsonThacherScraper(Scraper):

    def accept_cookies(self):
        try:
            cookie_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '#klaro-cookie-notice button.cm-btn-success'))
            )
            cookie_button.click()
        except Exception as e:
            print(f"Error accepting cookies: {e}")

    def set_records_per_page(self):
        try:
            dropdown_toggle = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "span.k-select"))
            )
            dropdown_toggle.click()
            time.sleep(2)  
            ActionChains(self.driver).send_keys(Keys.ARROW_DOWN).send_keys(Keys.ARROW_DOWN).send_keys(Keys.ARROW_DOWN).send_keys(Keys.ARROW_DOWN).send_keys(Keys.ENTER).perform()
            time.sleep(2)  
        except Exception as e:
            print(f"Failed to set records per page to 100: {e}")

    def fetch_data(self):
        url = self.base_url
        self.driver.get(url)
        time.sleep(2)
        self.accept_cookies()
        self.set_records_per_page()

        continue_loading = True
        target_date = datetime.strptime('12.31.2021', '%m.%d.%Y').date()

        while continue_loading:
            elements = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'ul.news-list-items li'))
            )
            last_date_on_page = datetime.min.date()

            for idx, element in enumerate(elements):
                try:
                    date_text = element.find_element(By.CSS_SELECTOR, "span.sfnewsMetaDate").text
                    if not date_text:
                        continue  

                    doc_date = datetime.strptime(date_text, '%m.%d.%y').date()
                    if doc_date > last_date_on_page:
                        last_date_on_page = doc_date

                    if doc_date > target_date:
                        link = element.find_element(By.CSS_SELECTOR, "a.anchor-when-reading_News")
                        title = link.text
                        ActionChains(self.driver).move_to_element(link).perform()
                        link.click()
                        time.sleep(2)

                        html_element = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "div[id^='cph_main'] div.show-when-reading-inner"))
                        )
                        html_content = html_element.get_attribute('outerHTML')
                        close_button = self.driver.find_element(By.CSS_SELECTOR, "a.back-when-reading")
                        self.data.append({
                            'title': title,
                            'date': doc_date,
                            'html_content': html_content,
                        })
                        close_button.click()
                        time.sleep(1)
                except Exception as e:
                    print(f"Error processing data for index {idx}: {e}")

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
            except Exception as e:
                print(f"Failed to process HTML content for {entry['title']}: {e}")
        
        self.write_csv(csv_data)

def main():
    base_url = 'https://www.stblaw.com/about-us/news'
    scraper = SimpsonThacherScraper(base_url)
    scraper.fetch_data()
    scraper.download_htmls_and_prepare_csv()
    scraper.close()

if __name__ == "__main__":
    main()
