from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import urllib.request
from urllib.parse import urlparse
import csv
import os

class Scraper:
    DOWNLOAD_FOLDER_NAME = 'files'
    CSV_FILE_NAME = 'publications.csv'

    def __init__(self, base_url):
        self.base_url = base_url
        self.driver = self.init_driver()
        self.prepare_output()
        self.data = []
    
    def init_driver(self):
        chrome_options = Options()
        # chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
        return driver
    
    def download_pdf_with_user_agent(self, url, filename):
        file_path = os.path.join(self.DOWNLOAD_FOLDER, filename)
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
        request = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(request) as response, open(file_path, 'wb') as f:
            f.write(response.read())
    
    def write_csv(self, data):
        with open(self.CSV_FILE_NAME, 'w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=['title', 'url', 'date'])
            writer.writeheader()
            writer.writerows(data)
    
    def prepare_output(self):
        parsed_uri = urlparse(self.base_url)
        root_folder_name = parsed_uri.netloc
        download_folder = os.path.join(root_folder_name, self.DOWNLOAD_FOLDER_NAME)
        csv_file = os.path.join(root_folder_name, self.CSV_FILE_NAME)
        os.makedirs(download_folder, exist_ok=True)
        self.DOWNLOAD_FOLDER = download_folder
        self.CSV_FILE_NAME = csv_file

    def get_scheme_and_domain(self):
        parsed_uri = urlparse(self.base_url)
        return f"{parsed_uri.scheme}://{parsed_uri.netloc}"

    def close(self):
        self.driver.quit()

