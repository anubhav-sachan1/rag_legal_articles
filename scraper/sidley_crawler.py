import os
import time
from selenium.webdriver.common.by import By

from scraper_base import Scraper

class SidleyScraper(Scraper):

    def fetch_data(self, page_number):
        url = f'{self.base_url}&skip={page_number}'
        self.driver.get(url)
        time.sleep(2)
        elements = self.driver.find_elements(By.CLASS_NAME, 'search-result')
        
        for element in elements:
            title = element.find_element(By.CLASS_NAME, 'result-title').text
            link = element.find_element(By.CSS_SELECTOR, "a[data-bind*='NavigateLink.Url']")
            doc_date = element.find_element(By.CSS_SELECTOR, "span[data-bind='text: DisplayDate']").text
            doc_url = link.get_attribute('href')
            date_formats = ['%B %d, %Y', '%B %Y']
            for date_format in date_formats:
                try:
                    doc_date = self.convert_to_date_type(doc_date, date_format).date()
                    break
                except ValueError:
                    pass
            self.data.append({
                'title': title,
                'date': doc_date,
                'url': doc_url
            })

    def download_pdfs_and_prepare_csv(self):
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
                print(f"Failed to retrieve PDF URL for {entry['title']}")
                print(e)
        
        self.write_csv(csv_data)

def main():
    base_url = 'https://www.sidley.com/en/us/insights/?articletypes=9cbfe518-3bc0-4632-ae13-6ac9cee8eb31'
    scraper = SidleyScraper(base_url)
    page_number = 10  
    scraper.fetch_data(page_number)
    scraper.download_pdfs_and_prepare_csv()
    scraper.close()

if __name__ == "__main__":
    main()
