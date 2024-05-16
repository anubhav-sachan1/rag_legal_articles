import os
import time
from selenium.webdriver.common.by import By

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
        url = self.base_url
        self.driver.get(url)
        time.sleep(5)
        self.accept_cookies()

        
        elements = self.driver.find_elements(By.CSS_SELECTOR, 'div.coveo-list-layout')
        original_window = self.driver.current_window_handle
        for idx in range(1, len(elements)):
            element = elements[idx]
            title = element.find_element(By.CSS_SELECTOR, "h3.content-card__title span.CoveoFieldValue span").text
            link = element.find_element(By.CSS_SELECTOR, "a.content-card__link")
            doc_date = element.find_element(By.CSS_SELECTOR, "div.content-card__info span span").text
            link.click()
            self.driver.switch_to.window(self.driver.window_handles[-1]) 
            doc_url = self.driver.current_url
            if '.pdf' in doc_url:
                self.driver.close()
                self.driver.switch_to.window(original_window)
                self.data.append({
                    'title': title,
                    'date': doc_date,
                    'url': doc_url,
                    'contains_pdf': '.pdf' in doc_url
                })
            else:
                self.driver.back()
                elements = self.driver.find_elements(By.CSS_SELECTOR, 'div.coveo-list-layout')
                time.sleep(2)

    def download_pdfs_and_prepare_csv(self):
        csv_data = []
        for entry in self.data:
            try:
                if not entry['contains_pdf']:
                    continue
                pdf_url = entry['url']
                csv_row = {'title': entry['title'], 'url': pdf_url, 'date': entry['date']}
                self.download_pdf_with_user_agent(pdf_url, f"{entry['title']}.pdf")
                csv_data.append(csv_row)
            except Exception:
                print(f"Failed to retrieve PDF URL for {entry['title']}")
        
        self.write_csv(csv_data)

def main():
    base_url = 'https://www.lw.com/en/insights-listing#sort=%40newsandinsightsdate%20descending&f:@newsandinsightstypefacet=[Publication]'
    scraper = LathamWatkinsScraper(base_url)
    try:
        scraper.fetch_data()
        scraper.download_pdfs_and_prepare_csv()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        scraper.close()

if __name__ == "__main__":
    main()
