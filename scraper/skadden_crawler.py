import time
from selenium import webdriver
from selenium.webdriver.common.by import By
import requests
from bs4 import BeautifulSoup
from chunk_text import chunk_text
import csv
from datetime import datetime
import os

class SkaddenScraper:
    def __init__(self, base_url):
        self.base_url = base_url
        self.driver = webdriver.Chrome()
        self.articles = []

    def fetch_articles(self):
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
                if last_article_date and last_article_date <= datetime(2021, 12, 31):
                    last_date_reached = True
                else:
                    self.collect_articles(page_articles)
                skip_value += 20
            else:
                break
        self.driver.quit()

    def parse_date(self, date_str):
        article_date = ""
        try:
            if len(date_str.split()) == 1:
                article_date = datetime.strptime(date_str, '%Y')
            elif len(date_str.split()) == 2:
                article_date = datetime.strptime(date_str, '%B %Y')
            else:
                article_date = datetime.strptime(date_str, '%B %d, %Y')
        except ValueError:
            pass
        return article_date

    def collect_articles(self, articles):
        for article in articles:
            try:
                date_str = article.find_element(By.CSS_SELECTOR, "span[ng-bind-html='result.DisplayDate']").text.strip()
                article_date = self.parse_date(date_str)
                if not article_date or article_date > datetime(2021, 12, 31):
                    title = article.find_element(By.CSS_SELECTOR, 'span.listing-articles-title-label.ng-binding').text.strip()
                    link = article.find_element(By.CSS_SELECTOR, 'a.listing-articles-title').get_attribute('href')
                    self.articles.append({"date": date_str, "title": title, "link": link})
            except Exception as e:
                continue
    
    def fetch_and_clean_content(self,url):
        headers = {
            'User-Agent': 'Chrome/124.0.6367.202'
        }
        response = requests.get(url, headers = headers)
        if response.status_code != 200:
            return "Failed to retrieve the page."
        soup = BeautifulSoup(response.content, 'html.parser')
        article_content = soup.find('div', class_='article-body-copy')
        if not article_content:
            return "No article content found."
        text = ' '.join(article_content.stripped_strings)
        clean_text = text.encode('utf-8', errors='ignore').decode('utf-8')
        chunks = chunk_text(clean_text)
        return chunks

    def write_articles_summary_csv(self):
        directory = "skadden.com"
        os.makedirs(directory, exist_ok=True)
        file_path = os.path.join(directory, "publications.csv")
        with open(file_path, mode="w", newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Title', 'Date', 'Link'])
            for article in self.articles:
                writer.writerow([article["title"], article["date"], article["link"]])

    def write_articles_to_csv(self):
        directory = "skadden.com"
        os.makedirs(directory, exist_ok=True)
        file_path = os.path.join(directory, "skadden_chunks.csv")
        with open(file_path, mode="w", newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Firm', 'Publication Title', 'Chunk Text'])
            for article in self.articles:
                content_chunks = self.fetch_and_clean_content(article["link"])
                for chunk in content_chunks:
                    writer.writerow(['Skadden', article["title"], chunk])

def main():
    scraper = SkaddenScraper("https://www.skadden.com/insights?panelid=tab-find-mode&paneltogglestate=2&type=9cbfe518-3bc0-4632-ae13-6ac9cee8eb31")
    scraper.fetch_articles()
    scraper.write_articles_summary_csv()
    print(f"Collected {len(scraper.articles)} articles and summaries written.")
    scraper.write_articles_to_csv()

if __name__ == "__main__":
    main()
