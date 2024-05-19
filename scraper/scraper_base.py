from selenium import webdriver
import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import urllib.request
from urllib.parse import urlparse
import csv
import os
from datetime import datetime
from enum import Enum

class Scraper:
    HTML_PDF_FOLDER_NAME = 'files'
    CSV_FILE_NAME = 'publications.csv'
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
        driver = uc.Chrome(options=chrome_options)
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
    
    def prepare_output(self):
        parsed_uri = urlparse(self.base_url)
        root_folder_name = parsed_uri.netloc
        download_folder = os.path.join(root_folder_name, self.HTML_PDF_FOLDER_NAME)
        csv_file = os.path.join(root_folder_name, self.CSV_FILE_NAME)
        os.makedirs(download_folder, exist_ok=True)
        self.DOWNLOAD_FOLDER = download_folder
        self.CSV_FILE_NAME = csv_file

    def get_scheme_and_domain(self):
        parsed_uri = urlparse(self.base_url)
        return f"{parsed_uri.scheme}://{parsed_uri.netloc}"

    def close(self):
        self.driver.quit()
        
    @classmethod
    def convert_to_date_type(cls, date_str, format_str):
        return datetime.strptime(date_str, format_str)

class ScraperType(Enum):
    PDF = 1
    HTML = 2
    URL = 3