import os
import time
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

from scraper_base import Scraper

class HenglerScraper(Scraper):

    def load_all_articles(self):
        """Load all articles up to the target date using the 'Load More' button."""
        self.driver.get(self.base_url)
        time.sleep(2)

        target_date = datetime.strptime('31/12/2021', '%d/%m/%Y').date()
        last_date = datetime.today().date()

        while last_date > target_date:
            try:
                load_more_button = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "a.pill.articleFilter-loadMore"))
                )
                # Scroll the button into view and then click it
                ActionChains(self.driver).move_to_element(load_more_button).perform()
                load_more_button.click()
                time.sleep(5)  # Wait for the page to load more articles

                # Check the date of the last loaded article to decide if we need to load more
                last_element = self.driver.find_elements(By.CSS_SELECTOR, 'div.article-date span')[-1]
                last_date = datetime.strptime(last_element.text, '%d %B %Y').date()
            except Exception as e:
                print("Could not find the 'Load More' button or no more pages to load:", e)
                break

    def fetch_data(self):
        """Fetch data from all loaded articles."""
        elements = self.driver.find_elements(By.CSS_SELECTOR, 'div.article')
        for element in elements:
            title = element.find_element(By.CSS_SELECTOR, "a.article-title h3").text
            link = element.find_element(By.CSS_SELECTOR, "a.article-title")
            doc_date = datetime.strptime(element.find_element(By.CSS_SELECTOR, "div.article-date span").text, '%d %B %Y').date()
            doc_url = link.get_attribute('href')
            
            self.data.append({
                'title': title,
                'date': doc_date,
                'url': doc_url
            })

    def download_pdfs_and_prepare_csv(self):
        """Download PDFs and prepare CSV from the fetched data."""
        csv_data = []
        for entry in self.data:
            try:
                self.driver.get(entry['url'])
                html_element = self.driver.find_element(By.CSS_SELECTOR, "div.articlePage-content")
                links = html_element.find_elements(By.CSS_SELECTOR, "a")
                pdf_urls = [link.get_attribute('href') for link in links if '.pdf' in link.get_attribute('href')]
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
                print(f"Failed to retrieve content for {entry['title']}: {e}")
        
        self.write_csv(csv_data)

def main():
    base_url = 'https://hengeler-news.com/en/latest-articles'
    scraper = HenglerScraper(base_url)
    scraper.load_all_articles()  # Load all articles up to the target date
    scraper.fetch_data()  # Fetch data from loaded articles
    scraper.download_pdfs_and_prepare_csv()
    scraper.write_chunks_csv("Hengeler Mueller", "div", "articlePage-content", True)
    scraper.close()

if __name__ == "__main__":
    main()
