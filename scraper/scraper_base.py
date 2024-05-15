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

class Scraper:
    PDF_FOLDER_NAME = 'files'
    CSV_FILE_NAME = 'publications.csv'
    CHUNKS_FILE_NAME = 'chunks.csv'
    LAST_DATE = None

    def __init__(self, base_url, last_date_str='31.12.2021', date_format='%d.%m.%Y'):
        self.base_url = base_url
        self.driver = self.init_driver()
        self.prepare_output()
        self.data = []
        self.set_last_date(last_date_str, date_format)
    
    def init_driver(self):
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.208 Safari/537.36"
        chrome_options = Options()
        # chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        # chrome_options.add_argument("--disable-extensions")
        # chrome_options.add_experimental_option('useAutomationExtension', False)
        # chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        # chrome_options.add_argument(f"user-agent={user_agent}")
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
        file_path = os.path.join(self.DOWNLOAD_FOLDER, filename)
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(html_content)
        return file_path

    def write_csv(self, data):
        with open(self.CSV_FILE_NAME, 'w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=['title', 'url', 'date'])
            writer.writeheader()
            writer.writerows(data)
    
    def write_chunks_csv(self, firm_name, container_element, class_name):
        parsed_uri = urlparse(self.base_url)
        root_folder_name = parsed_uri.netloc
        chunks_file = os.path.join(root_folder_name, self.CHUNKS_FILE_NAME)
        self.CHUNKS_FILE_NAME = chunks_file
        with open(self.CHUNKS_FILE_NAME, mode="w", newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=['Firm', 'Publication Title', 'Chunk Text'])
            writer.writeheader()
            df = pd.read_csv(self.CSV_FILE_NAME)
            with open(self.CHUNKS_FILE_NAME, mode="w", newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=['Firm', 'Publication Title', 'Chunk Text'])
                writer.writeheader()
                for _, row in df.iterrows():
                    content_chunks = self.extract_text_from_html(row["url"],container_element,class_name)
                    for chunk in content_chunks:
                        writer.writerow({'Firm': firm_name, 'Publication Title': row["title"], 'Chunk Text': chunk})
    
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
        clean_text = text.encode('utf-8', errors='ignore').decode('utf-8')
        chunks = chunk_text(clean_text)
        return chunks

    def extract_text_from_pdf(pdf_path, type='text'):
        document = fitz.open(pdf_path)
        full_text = ""
        for page in document:
            full_text += page.get_text(type)
        document.close()
        return full_text
    
    @classmethod
    def convert_to_date_type(cls, date_str, format_str):
        return datetime.strptime(date_str, format_str)
    
class ScraperType(Enum):
    PDF = 1
    HTML = 2
    URL = 3