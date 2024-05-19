import time
from selenium.webdriver.common.by import By
from scraper_base import Scraper

class SkaddenScraper(Scraper):

    def fetch_data(self):
        skip_value = 0
        last_date_reached = False

        while not last_date_reached:
            url = f"{self.base_url}&skip={skip_value}"
            self.driver.get(url)
            time.sleep(2)
            page_articles = self.driver.find_elements(By.CSS_SELECTOR, 'li.listing-articles-item.ng-scope')
            if page_articles:
                last_date_str = page_articles[-1].find_element(By.CSS_SELECTOR, "span[ng-bind-html='result.DisplayDate']").text.strip()
                last_article_date = self.get_parsed_date(last_date_str)
                if last_article_date and last_article_date <= self.LAST_DATE:
                    last_date_reached = True
                else:
                    self.collect_articles(page_articles)
                skip_value += 20
            else:
                break

    def collect_articles(self, articles):
        for article in articles:
            try:
                date_str = article.find_element(By.CSS_SELECTOR, "span[ng-bind-html='result.DisplayDate']").text.strip()
                article_date = self.get_parsed_date(date_str)
                if article_date and article_date > self.LAST_DATE:
                    title = article.find_element(By.CSS_SELECTOR, 'span.listing-articles-title-label.ng-binding').text.strip()
                    link = article.find_element(By.CSS_SELECTOR, 'a.listing-articles-title').get_attribute('href')
                    self.data.append({'title': title, 'url': link, 'date': date_str})
            except Exception:
                pass

    def download_html_and_save_csv(self):
        csv_data = []
        for entry in self.data:
            try:
                self.driver.get(entry['url'])
                article_element = self.driver.find_element(By.CSS_SELECTOR, "div.article-body")
                links = article_element.find_elements(By.CSS_SELECTOR, "a")
                pdf_urls = [link.get_attribute('href') for link in links if 'pdf' in link.get_attribute('href')]
                if len(pdf_urls) > 0:
                    pdf_url = pdf_urls[0]
                    if not pdf_url.startswith('http'):
                        pdf_url = f"{self.get_scheme_and_domain()}{pdf_url}"
                    self.download_pdf_with_user_agent(pdf_url, f"{entry['title']}.pdf")
                    csv_row = {'title': entry['title'], 'url': pdf_url, 'date': entry['date']}
                else:
                    html_content = article_element.get_attribute('outerHTML')
                    self.download_page_as_html(html_content, f"{entry['title']}.html")
                    csv_row = {'title': entry['title'], 'url': entry['url'], 'date': entry['date']}
                csv_data.append(csv_row)
            except Exception:
                pass
        
        self.write_csv(csv_data)

def main():
    base_url = "https://www.skadden.com/insights?panelid=tab-find-mode&paneltogglestate=2&type=9cbfe518-3bc0-4632-ae13-6ac9cee8eb31"
    last_date_str = "December 31, 2021"
    date_formats = ['%B %d, %Y', '%B %Y', '%Y']
    scraper = SkaddenScraper(base_url, last_date_str=last_date_str, date_formats=date_formats)
    scraper.fetch_data()
    scraper.download_html_and_save_csv()
    scraper.write_chunks_csv("Skadden","div","article-body", True)
    scraper.close()

if __name__ == "__main__":
    main()
