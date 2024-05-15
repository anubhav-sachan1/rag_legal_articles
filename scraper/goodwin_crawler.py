import os
import time
from selenium.webdriver.common.by import By
from datetime import datetime
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from scraper_base import Scraper, ScraperType

class GoodwinScraper(Scraper):
    @staticmethod
    def contains_date(string, date_format="%B %d, %Y"):
        try:
            # Try to parse the string into a datetime object according to the specified format
            datetime.strptime(string, date_format)
            return True
        except ValueError:
            # If ValueError is raised, it means the string does not match the date format
            return False

    def accept_cookies(self):
        try:
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button#onetrust-accept-btn-handler'))
            )
            cookie_button = self.driver.find_element(By.CSS_SELECTOR, 'button#onetrust-accept-btn-handler')
            if cookie_button:
                cookie_button.click()
        except Exception as e:
            print(f"Error in clicking cookie button: {e}")

    def fetch_data(self, page_number):
        url = f'{self.base_url}&page={page_number}'
        self.driver.get(url)
        time.sleep(2)
        self.accept_cookies()

        elements = self.driver.find_elements(By.CSS_SELECTOR, "div[class^='InsightsInsightSearch_panels__Wirv0'] ul li")
        last_date = datetime.today().date()
        
        for element in elements:
            try:
                link = element.find_element(By.CSS_SELECTOR, 'a')
                title = element.find_element(By.CSS_SELECTOR, "h3.type__h5").text
                span_elements = element.find_elements(By.CSS_SELECTOR, "span[class^='SearchArticleResult_articleMeta']")
                date_formats = ["%B %d, %Y", "%d %B %Y"] 
                doc_date = None  

                for date_format in date_formats:
                    date_texts = [s.text for s in span_elements if self.contains_date(s.text, date_format)]
                    if date_texts:
                        doc_date = self.convert_to_date_type(date_texts[0], date_format).date()
                        break

                if doc_date and doc_date < last_date:
                    last_date = doc_date

                if doc_date:  
                    doc_url = link.get_attribute('href')
                    if not doc_url.startswith('http'):
                        doc_url = f"{self.get_scheme_and_domain()}{doc_url}"
                    self.data.append({
                        'title': title,
                        'date': doc_date,
                        'url': doc_url,
                        'type': ScraperType.HTML
                    })
            except:
                print("Failed to parse article link.")
        return last_date

    def download_html_and_save_csv(self):
        csv_data = []
        for entry in self.data:
            try:
                self.driver.get(entry['url'])
                html_element = self.driver.find_element(By.CSS_SELECTOR, "main div.rich-text")
                html_content = html_element.get_attribute('outerHTML')
                self.download_page_as_html(html_content, f"{entry['title']}.html")
                csv_row = {'title': entry['title'], 'url': entry['url'], 'date': entry['date']}
                csv_data.append(csv_row)
            except Exception:
                print(f"Failed to retrieve PDF URL for {entry['title']}")
        
        self.write_csv(csv_data)

def main():
    base_url = 'https://www.goodwinlaw.com/en/insights?getrecent=true'
    scraper = GoodwinScraper(base_url)
    page_number = 378
    scraper.fetch_data(page_number)
    scraper.download_html_and_save_csv()
    scraper.close()

if __name__ == "__main__":
    main()
