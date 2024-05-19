import argparse
import re
import os
import csv
import fitz
import spacy
import json
from bs4 import BeautifulSoup
from langchain.text_splitter import SpacyTextSplitter
from concurrent.futures import ThreadPoolExecutor

class Chunker:
    HTML_PDF_FOLDER_NAME = 'files'
    CHUNKS_FILE_NAME = 'chunks.csv'

    def __init__(self, config):
        self.input_directory = config["input_directory"]
        self.output_directory = os.path.join('chunker', os.path.basename(self.input_directory))
        os.makedirs(self.output_directory, exist_ok=True)
        self.firm_name = config["firm_name"]
        self.container_element = config["container_element"]
        self.class_name = config["class_name"]

    def chunk_text(self, text, max_chunk_length=4000):
        spacy.util.fix_random_seed(0)  
        max_length = 1000000  
        text_splitter = SpacyTextSplitter()
        
        if len(text) > max_length:
            parts = [text[i:i + max_length] for i in range(0, len(text), max_length)]
        else:
            parts = [text]

        initial_chunks = []
        for part in parts:
            initial_chunks.extend(text_splitter.split_text(part))
        
        final_chunks = []
        for chunk in initial_chunks:
            if len(chunk) <= max_chunk_length:
                final_chunks.append(chunk)
            else:
                while len(chunk) > max_chunk_length:
                    last_space = chunk.rfind(' ', 0, max_chunk_length)
                    if last_space == -1:  
                        last_space = max_chunk_length
                    final_chunks.append(chunk[:last_space].strip())
                    chunk = chunk[last_space:].strip()
                if chunk:
                    final_chunks.append(chunk)

        return final_chunks
    
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

    def extract_text_from_html_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            html_content = file.read()
        soup = BeautifulSoup(html_content, 'html.parser')
        article_content = soup.find(self.container_element, class_=self.class_name)
        if article_content:
            return ' '.join(article_content.stripped_strings)
        return "No content found."
    
    def write_chunks_csv(self):
        chunks_file = os.path.join(self.output_directory, self.CHUNKS_FILE_NAME)
        files_dir = os.path.join(self.input_directory, self.HTML_PDF_FOLDER_NAME)

        with open(chunks_file, mode="w", newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=['Firm', 'Publication Title', 'Chunk Text'], escapechar='\\', quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()

            for filename in os.listdir(files_dir):
                file_path = os.path.join(files_dir, filename)
                if filename.endswith('.pdf'):
                    text = self.extract_text_from_pdf(file_path)
                elif filename.endswith('.html'):
                    text = self.extract_text_from_html_file(file_path)
                else:
                    continue
                if text=="Failed to read PDF." or text=="No content found.":
                    continue
                content_chunks = self.chunk_text(text)
                title = os.path.splitext(filename)[0]  
                for chunk in content_chunks:
                    try:
                        writer.writerow({'Firm': self.firm_name, 'Publication Title': title, 'Chunk Text': chunk})
                    except Exception as e:
                        print(f"Error writing row for {title}: {e}")

def load_configurations(file_path):
    with open(file_path, 'r') as file:
        config = json.load(file)
    return config["scrapers"]

def process_chunker(config):
    print("Starting processing for:", config['firm_name'])
    try:
        chunker = Chunker(config)
        chunker.write_chunks_csv()
        print(f"Processed chunks for {config['firm_name']} at {config['input_directory']}")
    except Exception as e:
        print(f"Failed to process chunks for {config['firm_name']}: {e}")

def get_arguments():
    parser = argparse.ArgumentParser(description='Process chunks for multiple scrapers with configurable threading and configuration file.')
    parser.add_argument('-t', '--threads', type=int, default=4, help='Number of threads to use for concurrent processing.')
    parser.add_argument('-c', '--config', type=str, default='chunker_config.json', help='Path to the configuration JSON file.')
    args = parser.parse_args()
    return args.threads, args.config

if __name__ == "__main__":
    threads, config_path = get_arguments()
    configurations = load_configurations(config_path)

    with ThreadPoolExecutor(max_workers=threads) as executor:
        executor.map(process_chunker, configurations)

# if __name__ == "__main__":
#     chunker = Chunker("scraper/www.gleisslutz.com","Gleiss Lutz", "div", "paragraph__content-container")
#     chunker.write_chunks_csv()