import time
from selenium.webdriver.common.by import By
from scraper_base import Scraper
from datetime import datetime

class SkaddenScraper(Scraper):
    def fetch_data(self):
        skip_value = 0
        last_date_reached = False

        while not last_date_reached:
            url = f"{self.base_url}&skip={skip_value}"
            self.driver.get(url)
            time.sleep(5)
            page_articles = self.driver.find_elements(By.CSS_SELECTOR, 'li.listing-articles-item.ng-scope')
            if page_articles:
                last_date_str = page_articles[-1].find_element(By.CSS_SELECTOR, "span[ng-bind-html='result.DisplayDate']").text.strip()
                last_article_date = self.parse_date(last_date_str)
                if last_article_date and last_article_date <= self.LAST_DATE:
                    last_date_reached = True
                else:
                    self.collect_articles(page_articles)
                skip_value += 20
            else:
                break
        self.driver.quit()

    def parse_date(self, date_str):
        try:
            if len(date_str.split()) == 1:
                return datetime.strptime(date_str, '%Y').date()
            elif len(date_str.split()) == 2:
                return datetime.strptime(date_str, '%B %Y').date()
            return datetime.strptime(date_str, '%B %d, %Y').date()
        except ValueError:
            return None

    def collect_articles(self, articles):
        for article in articles:
            try:
                date_str = article.find_element(By.CSS_SELECTOR, "span[ng-bind-html='result.DisplayDate']").text.strip()
                article_date = self.parse_date(date_str)
                if article_date and article_date > self.LAST_DATE:
                    title = article.find_element(By.CSS_SELECTOR, 'span.listing-articles-title-label.ng-binding').text.strip()
                    link = article.find_element(By.CSS_SELECTOR, 'a.listing-articles-title').get_attribute('href')
                    self.data.append({'title': title, 'url': link, 'date': date_str})
            except Exception as e:
                continue

def main():
    base_url = "https://www.skadden.com/insights?panelid=tab-find-mode&paneltogglestate=2&type=9cbfe518-3bc0-4632-ae13-6ac9cee8eb31"
    scraper = SkaddenScraper(base_url, '31 December 2021', '%d %B %Y')
    scraper.fetch_data()
    scraper.write_csv(scraper.data)
    scraper.write_chunks_csv("Skadden","div","article-body-copy")
    scraper.close()

if __name__ == "__main__":
    main()
