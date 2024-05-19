from selenium import webdriver
import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import urllib.request
from urllib.parse import urlparse
import csv
import os
import fitz
from enum import Enum
from datetime import datetime
import pandas as pd
import requests
from bs4 import BeautifulSoup
from chunk_text import chunk_text
import re

class Scraper:
    PDF_FOLDER_NAME = 'files'
    CSV_FILE_NAME = 'publications.csv'
    CHUNKS_FILE_NAME = 'chunks.csv'
    LAST_DATE = None

    def __init__(self, base_url, last_date_str='31.12.2021', date_formats=['%d.%m.%Y']):
        self.base_url = base_url
        self.driver = self.init_driver()
        self.prepare_output()
        self.data = []
        self.date_formats = date_formats
        self.set_last_date(last_date_str, date_formats[0])
    
    def init_driver(self):
        user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
        chrome_options = Options()
        # add user agent
        # chrome_options.add_argument(f"user-agent={user_agent}")

        # chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        # chrome_options.add_argument("--disable-extensions")
        # chrome_options.add_experimental_option('useAutomationExtension', False)
        # chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        # chrome_options.add_argument("--headless")
        driver = uc.Chrome(options=chrome_options)
        # driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.implicitly_wait(2)
        return driver
    
    def set_last_date(self, last_date_str, date_format):
        try:
            self.LAST_DATE = datetime.strptime(last_date_str, date_format).date()
        except ValueError as e:
            print(f"Error setting last date with format {date_format}: {e}")
            raise
    
    def download_pdf_with_user_agent(self, url, filename):
        file_path = os.path.join(self.DOWNLOAD_FOLDER, filename)
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
        request = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(request) as response, open(file_path, 'wb') as f:
            f.write(response.read())
    
    def download_page_as_html(self, html_content, filename):
        try:
            file_path = os.path.join(self.DOWNLOAD_FOLDER, filename)
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(html_content)
            return file_path
        except:
            return ""

    def write_csv(self, data):
        with open(self.CSV_FILE_NAME, 'w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=['title', 'url', 'date'])
            writer.writeheader()
            writer.writerows(data)
    
    def write_chunks_csv(self, firm_name, container_element, class_name, read_files=False):
        parsed_uri = urlparse(self.base_url)
        root_folder_name = parsed_uri.netloc
        chunks_file = os.path.join(root_folder_name, self.CHUNKS_FILE_NAME)
        files_dir = os.path.join(root_folder_name, self.PDF_FOLDER_NAME)

        with open(chunks_file, mode="w", newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=['Firm', 'Publication Title', 'Chunk Text'], escapechar='\\', quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()

            if read_files:
                for filename in os.listdir(files_dir):
                    file_path = os.path.join(files_dir, filename)
                    if filename.endswith('.pdf'):
                        text = self.extract_text_from_pdf(file_path)
                    elif filename.endswith('.html'):
                        text = self.extract_text_from_html_file(file_path, container_element, class_name)
                    else:
                        continue
                    if text=="Failed to read PDF." or text=="No content found.":
                        continue
                    content_chunks = chunk_text(text)
                    title = os.path.splitext(filename)[0]  
                    for chunk in content_chunks:
                        try:
                            writer.writerow({'Firm': firm_name, 'Publication Title': title, 'Chunk Text': chunk})
                        except Exception as e:
                            print(f"Error writing row for {title}: {e}")
            else:
                df = pd.read_csv(self.CSV_FILE_NAME)
                for _, row in df.iterrows():
                    content_chunks = self.extract_text_from_html(row["url"], container_element, class_name)
                    for chunk in content_chunks:
                        try:
                            writer.writerow({'Firm': firm_name, 'Publication Title': row["title"], 'Chunk Text': chunk})
                        except Exception as e:
                            print(f"Error writing row for {row['title']}: {e}")

    def extract_text_from_html_file(self, file_path, container_element, class_name):
        with open(file_path, 'r', encoding='utf-8') as file:
            html_content = file.read()
        soup = BeautifulSoup(html_content, 'html.parser')
        article_content = soup.find(container_element, class_=class_name)
        if article_content:
            return ' '.join(article_content.stripped_strings)
        return "No content found."
    
    def prepare_output(self):
        parsed_uri = urlparse(self.base_url)
        root_folder_name = parsed_uri.netloc
        download_folder = os.path.join(root_folder_name, self.PDF_FOLDER_NAME)
        csv_file = os.path.join(root_folder_name, self.CSV_FILE_NAME)
        os.makedirs(download_folder, exist_ok=True)
        self.DOWNLOAD_FOLDER = download_folder
        self.CSV_FILE_NAME = csv_file

    def get_scheme_and_domain(self):
        parsed_uri = urlparse(self.base_url)
        return f"{parsed_uri.scheme}://{parsed_uri.netloc}"

    def close(self):
        self.driver.quit()
    
    def extract_text_from_html(self,url,container_element,class_name):
        headers = {
            'User-Agent': 'Chrome/124.0.6367.202'
        }
        response = requests.get(url, headers = headers)
        if response.status_code != 200:
            return "Failed to retrieve the page."
        soup = BeautifulSoup(response.content, 'html.parser')
        article_content = soup.find(container_element, class_=class_name)
        if not article_content:
            return "No article content found."
        text = ' '.join(article_content.stripped_strings)
        clean_text = text.encode('ascii', errors='ignore').decode('ascii')
        chunks = chunk_text(clean_text)
        return chunks

    def extract_text_from_pdf(self,pdf_path):
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            
            clean_text = text.replace('\n', ' ').replace('\t', ' ')  
            clean_text = re.sub(r'[ ]{2,}', ' ', clean_text)  
            clean_text = clean_text.encode('ascii', errors='ignore').decode('ascii')
            
            return clean_text
        except Exception as e:
            return "Failed to read PDF."
    
    @classmethod
    def convert_to_date_type(cls, date_str, format_str):
        return datetime.strptime(date_str, format_str)
    
    def get_parsed_date(self, date_str) -> datetime.date:
        for date_format in self.date_formats:
            try:
                return self.convert_to_date_type(date_str, date_format).date()
            except ValueError:
                continue
        return None

    
class ScraperType(Enum):
    PDF = 1
    HTML = 2
    URL = 3