import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime

from scraper_base import Scraper, ScraperType

class DebevoiseScraper(Scraper):

    def accept_cookies(self):
        try:
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'a#cookie-apply-all'))
            ).click()
        except Exception as e:
            print("Cookie button not found or not clickable.")

    def fetch_data(self):
        self.driver.get(self.base_url)
        time.sleep(5)
        self.accept_cookies()

        continue_loading = True
        last_article_date = datetime.today().date()

        while continue_loading:
            elements = self.driver.find_elements(By.CSS_SELECTOR, "li.articles-list__item.insights-list-item")
            if elements:
                last_element = elements[-1]
                last_article_date =  datetime(2022, 1, 1).date()
                try:
                    doc_date_str = last_element.find_element(By.CSS_SELECTOR, "div.insights-list-subtitle").text
                    last_article_date = self.convert_to_date(doc_date_str)
                except:
                    pass
            if last_article_date <= datetime(2021, 12, 31).date():
                continue_loading = False
            else:
                try:
                    load_more_button = WebDriverWait(self.driver, 30).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, 'a.btn.btn-accordion.search.js-accordion-trigger'))
                    )
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", load_more_button)
                    time.sleep(2)
                    load_more_button.click()
                    time.sleep(5)  
                except Exception as e:
                    print("No more 'View More Insights' button found or other error: " + str(e))
                    continue_loading = False

        for element in elements:
            link = element.find_element(By.CSS_SELECTOR, 'a.insights-list-title')
            title = link.text
            try:
                doc_date_str = element.find_element(By.CSS_SELECTOR, "div.insights-list-subtitle").text
                doc_date = self.convert_to_date(doc_date_str)

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
            except:
                pass

    def convert_to_date(self, date_str):
        date_formats = ['%d %B %Y', '%B %Y', '%d %B, %Y']
        for date_format in date_formats:
            try:
                return datetime.strptime(date_str, date_format).date()
            except ValueError:
                continue
        return None

    def download_html_and_save_csv(self):
        csv_data = []
        for entry in self.data:
            try:
                self.driver.get(entry['url'])
                html_element = self.driver.find_element(By.CSS_SELECTOR, "div.rich-text")
                article_links = html_element.find_elements(By.CSS_SELECTOR, "a")
                pdf_urls = [link.get_attribute('href') for link in article_links if '.pdf' in link.get_attribute('href')]
                if len(pdf_urls) > 0:
                    pdf_url = pdf_urls[0]
                    if not pdf_url.startswith('http'):
                        pdf_url = f"{self.get_scheme_and_domain()}{pdf_url}"
                    self.download_pdf_with_user_agent(pdf_url, f"{entry['title']}.pdf")
                    csv_row = {'title': entry['title'], 'url': pdf_url, 'date': entry['date']}
                else:
                    html_content = html_element.get_attribute('outerHTML')
                    self.download_page_as_html(html_content, f"{entry['title']}.html")
                    csv_row = {'title': entry['title'], 'url': entry['url'], 'date': entry['date']}
                csv_data.append(csv_row)
            except Exception as e:
                pass
        
        self.write_csv(csv_data)

def main():
    base_url = 'https://www.debevoise.com/insights/search'
    scraper = DebevoiseScraper(base_url)
    scraper.fetch_data()
    scraper.download_html_and_save_csv()
    scraper.close()

if __name__ == "__main__":
    main()
