import os
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime

from scraper_base import Scraper

class SidleyScraper(Scraper):
    def __init__(self, base_url):
        super().__init__(base_url)
        self.seen_titles = set()  

    def fetch_data(self):
        self.driver.get(self.base_url)
        time.sleep(2)

        target_date = datetime.strptime('31.12.2021', '%d.%m.%Y').date()
        last_date = datetime.today().date()

        while True:
            elements = self.driver.find_elements(By.CLASS_NAME, 'search-result')
            for element in elements:
                title = element.find_element(By.CLASS_NAME, 'result-title').text
                if title in self.seen_titles:
                    continue  
                self.seen_titles.add(title)

                link = element.find_element(By.CSS_SELECTOR, "a[data-bind*='NavigateLink.Url']")
                doc_date = element.find_element(By.CSS_SELECTOR, "span[data-bind='text: DisplayDate']").text
                doc_url = link.get_attribute('href')
                date_formats = ['%B %d, %Y', '%B %Y']

                for date_format in date_formats:
                    try:
                        parsed_date = datetime.strptime(doc_date, date_format).date()
                        if parsed_date > target_date:
                            self.data.append({
                                'title': title,
                                'date': parsed_date,
                                'url': doc_url
                            })
                        break
                    except ValueError:
                        continue

                if parsed_date < last_date:
                    last_date = parsed_date

            if last_date <= target_date:
                break

            try:
                load_more_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".btn-read-more.js-rte-trigger")))
                load_more_button.click()
                time.sleep(2)
            except Exception as e:
                print("Could not find the 'Load More' button or no more pages to load")
                print(e)
                break

    def download_content_and_prepare_csv(self):
        csv_data = []
        for entry in self.data:
            try:
                self.driver.get(entry['url'])
                html_element = self.driver.find_element(By.CSS_SELECTOR, "div.inner-wrapper")
                links = html_element.find_elements(By.CSS_SELECTOR, "a")
                urls = [link.get_attribute('href') for link in links]
                pdf_urls = [url for url in urls if '.pdf' in url]
                if len(pdf_urls) > 0:
                    pdf_url = pdf_urls[0]
                    if not pdf_url.startswith('http'):
                        pdf_url = f"{self.get_scheme_and_domain()}{pdf_url}"
                    csv_row = {'title': entry['title'], 'url': pdf_url, 'date': entry['date']}
                    self.download_pdf_with_user_agent(pdf_url, f"{entry['title']}.pdf")
                else:
                    summary_element = html_element.find_element(By.CSS_SELECTOR, "div.article-summary")
                    html_content = summary_element.get_attribute('outerHTML')
                    self.download_page_as_html(html_content, f"{entry['title']}.html")
                    csv_row = {'title': entry['title'], 'url': entry['url'], 'date': entry['date']}
                csv_data.append(csv_row)
            except Exception as e:
                pass

        self.write_csv(csv_data)

def main():
    base_url = 'https://www.sidley.com/en/us/insights/?articletypes=9cbfe518-3bc0-4632-ae13-6ac9cee8eb31'
    scraper = SidleyScraper(base_url)
    scraper.fetch_data()
    scraper.download_content_and_prepare_csv()
    scraper.write_chunks_csv("Sidley", "div", "rich-text-content", True)
    scraper.close()

if __name__ == "__main__":
    main()
