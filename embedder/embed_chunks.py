import os
import pandas as pd
import requests
import csv
from concurrent.futures import ThreadPoolExecutor
import argparse
import numpy as np

class EmbeddingsGenerator:
    def __init__(self, input_directory, output_directory, api_key):
        self.input_directory = input_directory
        self.output_directory = output_directory
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.url = "https://api.openai.com/v1/embeddings"
        os.makedirs(self.output_directory, exist_ok=True)

    def read_chunks(self):
        csv_path = os.path.join(self.input_directory, 'chunks.csv')
        return pd.read_csv(csv_path) if os.path.exists(csv_path) else pd.DataFrame()

    def create_chunk_batches(self, dataframe, batch_size=2048):
        return [dataframe[start:start + batch_size]['Chunk Text'].tolist() for start in range(0, len(dataframe), batch_size)]

    def get_embeddings(self, text_batches):
        embeddings = []
        for batch in text_batches:
            clean_batch = []
            for text in batch:
                if isinstance(text, str):
                    clean_batch.append(text)
                elif isinstance(text, float) and (np.isnan(text) or np.isinf(text)):
                    clean_batch.append("invalid data")
                else:
                    clean_batch.append(str(text))  

            try:
                response = requests.post(self.url, headers=self.headers, json={"input": clean_batch, "model": "text-embedding-3-small"})
                response.raise_for_status()
                for embeddingJSON in response.json()['data']:
                    embedding = embeddingJSON["embedding"]
                    embeddings.append(embedding)
            except requests.exceptions.RequestException as e:
                print(f"Request failed: {e}")
                continue
        return embeddings

    def save_embeddings(self, text_batches, embeddings):
        csv_path = os.path.join(self.output_directory, 'chunk_embeddings.csv')
        chunks = [chunk for batch in text_batches for chunk in batch]
        with open(csv_path, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Chunk Text', 'Embedding'])
            for text, embed in zip(chunks, embeddings):
                writer.writerow([text, embed])

    def process_directory(self):
        df = self.read_chunks()
        if not df.empty:
            text_batches = self.create_chunk_batches(df)
            embeddings = self.get_embeddings(text_batches)
            self.save_embeddings(text_batches, embeddings)
            print(f"Processed and saved embeddings for directory: {self.output_directory}")

def find_directories(input_root):
    directories = []
    for dirpath, dirnames, _ in os.walk(input_root):
        for dirname in dirnames:
            sub_dir = os.path.join(dirpath, dirname)
            if 'chunks.csv' in os.listdir(sub_dir):
                directories.append(sub_dir)
    return directories

def main(api_key, threads):
    input_root = "chunker"
    output_root = "embedder"

    directories = find_directories(input_root)
    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = [executor.submit(EmbeddingsGenerator(dir, os.path.join(output_root, os.path.basename(dir)), api_key).process_directory) for dir in directories]
        for future in futures:
            future.result()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate embeddings from text chunks.')
    parser.add_argument('--threads', type=int, default=4, help='Number of concurrent threads.')
    args = parser.parse_args()

    api_key_path = 'secret_key.txt'
    with open(api_key_path, 'r') as f:
        api_key = f.readline().strip()

    main(api_key, args.threads)
