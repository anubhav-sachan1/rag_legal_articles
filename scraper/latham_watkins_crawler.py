import os
import time
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException

from scraper_base import Scraper

class LathamWatkinsScraper(Scraper):

    def accept_cookies(self):
        try:
            cookie_button = self.driver.find_element(By.CSS_SELECTOR, 'button#onetrust-accept-btn-handler')
            if cookie_button:
                cookie_button.click()
        except Exception as e:
            print(f"Error: {e}")
            print("Failed to accept cookies")

    def fetch_data(self):
        homepage_url = 'https://www.lw.com'
        self.driver.get(homepage_url)
        time.sleep(5)
        self.accept_cookies()

        first = 0
        last_date = datetime.today().date()
        last_date_threshold = datetime.strptime('31 December 2021', '%d %B %Y').date()

        while last_date > last_date_threshold:
            url = f'{self.base_url}#first={first}&sort=%40newsandinsightsdate%20descending&f:@newsandinsightstypefacet=[Publication]'
            self.driver.get(url)
            time.sleep(5)

            elements = self.driver.find_elements(By.CSS_SELECTOR, 'div.coveo-list-layout')
            if not elements:
                break

            original_window = self.driver.current_window_handle
            idx = 0
            while idx < len(elements):
                try:
                    time.sleep(2)
                    element = elements[idx]
                    title = element.find_element(By.CSS_SELECTOR, "h3.content-card__title span.CoveoFieldValue span").text
                    link = element.find_element(By.CSS_SELECTOR, "a.content-card__link")
                    doc_date = element.find_element(By.CSS_SELECTOR, "div.content-card__info span span").text
                    doc_date = datetime.strptime(doc_date, '%B %d, %Y').date()
                    if doc_date < last_date_threshold:
                        last_date = doc_date
                        break
                    link.click()
                    time.sleep(3)
                    if len(self.driver.window_handles) > 1:
                        self.driver.switch_to.window(self.driver.window_handles[-1])
                    doc_url = self.driver.current_url
                    contains_pdf = '.pdf' in doc_url
                    self.data.append({
                        'title': title,
                        'date': doc_date,
                        'url': doc_url,
                        'contains_pdf': contains_pdf
                    })
                    if contains_pdf or self.driver.current_window_handle != original_window:
                        self.driver.close()
                        self.driver.switch_to.window(original_window)
                    else:
                        self.driver.back()
                        time.sleep(2)
                    idx += 1
                except StaleElementReferenceException:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, 'div.coveo-list-layout')[idx:]
                    continue
                except NoSuchElementException:
                    print(f"Element not found, skipping index {idx}")
                    idx += 1

            if last_date >= last_date_threshold:
                first += 20

    def download_content_and_prepare_csv(self):
        csv_data = []
        for entry in self.data:
            file_extension = 'pdf' if entry['contains_pdf'] else 'html'
            file_path = f"{entry['title'].replace('/', '_')}.{file_extension}"
            try:
                if entry['contains_pdf']:
                    self.download_pdf_with_user_agent(entry['url'], file_path)
                else:
                    self.driver.get(entry['url'])
                    html_content = self.driver.page_source
                    self.download_page_as_html(html_content, file_path)
                csv_row = {'title': entry['title'], 'url': entry['url'], 'date': entry['date']}
                csv_data.append(csv_row)
            except Exception:
                print(f"Failed to retrieve content for {entry['title']}")

        self.write_csv(csv_data)

def main():
    base_url = 'https://www.lw.com/en/insights-listing'
    scraper = LathamWatkinsScraper(base_url)
    scraper.fetch_data()
    scraper.download_content_and_prepare_csv()
    scraper.write_chunks_csv("Latham & Watkins", "div", "component-content", True)
    scraper.close()

if __name__ == "__main__":
    main()
