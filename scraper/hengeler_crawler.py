import os
import time
from selenium.webdriver.common.by import By

from scraper_base import Scraper

class HenglerScraper(Scraper):

    def fetch_data(self):
        url = self.base_url
        self.driver.get(url)
        time.sleep(2)
        elements = self.driver.find_elements(By.CSS_SELECTOR, 'div.article')
        
        for element in elements:
            title = element.find_element(By.CSS_SELECTOR, "a.article-title h3").text
            link = element.find_element(By.CSS_SELECTOR, "a.article-title")
            doc_date = element.find_element(By.CSS_SELECTOR, "div.article-date span").text
            # Convert '11 March 2024' to datetime object
            doc_date = self.convert_to_date_type(doc_date, '%d %B %Y').date()
            doc_url = link.get_attribute('href')
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
                html_element = self.driver.find_element(By.CSS_SELECTOR, "div.articlePage-content")
                links = html_element.find_elements(By.CSS_SELECTOR, "a")
                urls = [link.get_attribute('href') for link in links]
                pdf_urls= [url for url in urls if '.pdf' in url]
                if len(pdf_urls) > 0:
                    pdf_url = pdf_urls[0]
                    if not pdf_url.startswith('http'):
                        pdf_url = f"{self.get_scheme_and_domain()}{pdf_url}"
                    csv_row = {'title': entry['title'], 'url': pdf_url, 'date': entry['date']}
                    self.download_pdf_with_user_agent(pdf_url, f"{entry['title']}.pdf")
                else:
                    html_content = html_element.get_attribute('outerHTML')
                    self.download_page_as_html(html_content, f"{entry['title']}.html")
                    csv_row = {'title': entry['title'], 'url': entry['url'], 'date': entry['date']}
                csv_data.append(csv_row)
            except Exception:
                print(f"Failed to retrieve PDF URL for {entry['title']}")
        
        self.write_csv(csv_data)

def main():
    base_url = 'https://hengeler-news.com/en/latest-articles'
    scraper = HenglerScraper(base_url)
    scraper.fetch_data()
    scraper.download_pdfs_and_prepare_csv()
    scraper.close()

if __name__ == "__main__":
    main()
