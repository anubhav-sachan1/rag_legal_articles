import os
import time
from dateutil import parser
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

from scraper_base import Scraper

class LinklatersScraper(Scraper):

    target_date = datetime.strptime('31/12/2021', '%d/%m/%Y').date()

    def accept_cookies(self):
        try:
            WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'div#CybotCookiebotDialog button#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowallSelection'))
            ).click()
        except Exception as e:
            print("Cookie button not found or not clickable.")

    def skip_navigation(self):
        try:
            WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'a.introjs-skipbutton'))
            ).click()
        except Exception as e:
            print("Cookie button not found or not clickable.")

    def load_all_articles(self):
        self.driver.get(self.base_url)
        time.sleep(2)
        self.accept_cookies()
        self.skip_navigation()

        last_date = datetime.today().date()

        while last_date > self.target_date:
            try:
                load_more_button = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.loadMoreContainer button"))
                )
                ActionChains(self.driver).move_to_element(load_more_button).perform()
                load_more_button.click()
                time.sleep(3)  

                last_element = self.driver.find_elements(By.CSS_SELECTOR, 'div.searchResults.cardRow div.result-item.card')[-1]
                last_element_date = last_element.find_element(By.CSS_SELECTOR, 'div.card__box div.card__details p').text
                last_date_tmp = parser.parse(last_element_date, fuzzy=True).date()
                last_date = last_date_tmp
            except Exception as e:
                print("Could not find the 'Load More' button or no more pages to load:", e)
                break

    def fetch_data(self):
        elements = self.driver.find_elements(By.CSS_SELECTOR, 'div.searchResults.cardRow div.result-item.card')
        for element in elements:
            link = element.find_element(By.CSS_SELECTOR, "div.card__box h4.card__title a")
            title = link.text
            doc_date_text = element.find_element(By.CSS_SELECTOR, 'div.card__box div.card__details p').text
            doc_date = parser.parse(doc_date_text, fuzzy=True).date()
            doc_url = link.get_attribute('href')
            if doc_date > self.target_date:
                self.data.append({
                    'title': title,
                    'date': doc_date,
                    'url': doc_url
                })

    def has_obscured_content(self):
        try:
            return WebDriverWait(self.driver, 4).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.ckp-obfuscated__content"))
            )
        except Exception as e:
            return False

    def download_pdfs_and_prepare_csv(self):
        csv_data = []
        for entry in self.data:
            try:
                self.driver.get(entry['url'])
                if self.has_obscured_content():
                    continue
                html_element = self.driver.find_element(By.CSS_SELECTOR, "div.containerOuter div.content-block__content")
                links = html_element.find_elements(By.CSS_SELECTOR, "a")
                pdf_urls = [link.get_attribute('href') for link in links if 'pdf' in link.get_attribute('href')]
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
    base_url = 'https://www.linklaters.com/en/knowledge'
    scraper = LinklatersScraper(base_url)
    scraper.load_all_articles()  
    scraper.fetch_data()  
    scraper.download_pdfs_and_prepare_csv()
    scraper.close()

if __name__ == "__main__":
    main()