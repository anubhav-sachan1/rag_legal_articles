import time
from selenium import webdriver
from selenium.webdriver.common.by import By
import requests
from bs4 import BeautifulSoup
from chunk_text import chunk_text
import csv
import json
from datetime import datetime

def scrape_articles():
    skip_value = 0
    all_articles = []
    last_date_reached = False
    driver = webdriver.Chrome()

    while not last_date_reached:
        url = f"https://www.skadden.com/insights?skip={str(skip_value)}&panelid=tab-find-mode&paneltogglestate=2&type=9cbfe518-3bc0-4632-ae13-6ac9cee8eb31"
        driver.get(url)
        time.sleep(5)
        articles = driver.find_elements(By.CSS_SELECTOR, 'li.listing-articles-item.ng-scope')
        last_article = articles[-1]
        date_str = last_article.find_element(By.CSS_SELECTOR, "span[ng-bind-html='result.DisplayDate']").text.strip()
        print(date_str)
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

        if article_date and article_date <= datetime(2021, 12, 31):
            last_date_reached = True
        
        for article in articles:
            date_str = ""
            try:
                date_str = article.find_element(By.CSS_SELECTOR, "span[ng-bind-html='result.DisplayDate']").text.strip()
            except Exception as e:
                pass
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
            if article_date and article_date <= datetime(2021, 12, 31):
                continue
            try:
                title = article.find_element(By.CSS_SELECTOR, 'span.listing-articles-title-label.ng-binding').text.strip()
                link = article.find_element(By.CSS_SELECTOR, 'a.listing-articles-title').get_attribute('href')

                all_articles.append({
                    "date": date_str,
                    "title": title,
                    "link": link
                    })
            except:
                continue

        skip_value += 20

    driver.quit()
    return all_articles

def fetch_and_clean_content(url):
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

    clean_text = text.encode('ascii', errors='ignore').decode('ascii')
    chunks = chunk_text(clean_text)
    return chunks

def write_articles_to_csv(articles):
    with open("skadden_chunks.csv", mode="w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Firm', 'Publication Title', 'Chunk Text'])
        
        for article in articles:
            content_chunks = fetch_and_clean_content(article["link"])
            title = article["title"]
            firm = "Skadden" 
            
            for chunk in content_chunks:
                writer.writerow([firm, title, chunk])

articles = scrape_articles()
print(f"Collected {len(articles)} articles.")

write_articles_to_csv(articles)
