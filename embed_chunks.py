import os
import pandas as pd
import requests
import csv
import numpy as np

class EmbeddingsGenerator:
    def __init__(self, directory, api_key):
        self.directory = directory
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.url = "https://api.openai.com/v1/embeddings"

    def read_chunks(self):
        csv_path = os.path.join(self.directory, 'chunks.csv')
        return pd.read_csv(csv_path)

    def create_chunk_batches(self, dataframe, batch_size=2048):
        total_batches = []
        for start in range(0, len(dataframe), batch_size):
            batch = dataframe[start:start + batch_size]
            total_batches.append(batch['Chunk Text'].tolist())
        return total_batches

    import numpy as np

    def get_embeddings(self, text_batches):
        embeddings = []
        for batch in text_batches:
            # Clean each text in the batch individually
            clean_batch = []
            for text in batch:
                if isinstance(text, str):
                    clean_batch.append(text)
                elif isinstance(text, float) and (np.isnan(text) or np.isinf(text)):
                    clean_batch.append("invalid data")  # Replace problematic floats
                else:
                    clean_batch.append(str(text))  # Ensure everything is a string

            try:
                response = requests.post(self.url, headers=self.headers, json={"input": clean_batch, "model": "text-embedding-3-small"})
                response.raise_for_status()  # This will raise an exception for HTTP error responses
                for embeddingJSON in response.json()['data']:
                    embedding = embeddingJSON["embedding"]
                    embeddings.append(embedding)
            except requests.exceptions.RequestException as e:
                print(f"Request failed: {e}")
                # Optionally, handle specific response errors here
                continue  # Skip this batch on failure but continue processing
        return embeddings


    def save_embeddings(self, text_batches, embeddings):
        chunks = [chunk for batch in text_batches for chunk in batch]
        with open(os.path.join(self.directory, 'chunk_embedding.csv'), 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Chunk Text', 'Embedding'])
            for text, embed in zip(chunks, embeddings):
                writer.writerow([text, embed])

    def process_directory(self):
        df = self.read_chunks()
        text_batches = self.create_chunk_batches(df)
        embeddings = self.get_embeddings(text_batches)
        self.save_embeddings(text_batches, embeddings)

def main():
    directories = [
        "scraper/www.advant-beiten.com", 
        "scraper/www.skadden.com", 
        "scraper/www.goodwinlaw.com",
        "scraper/www.noerr.com",
        "scraper/www.debevoise.com",
        "scraper/www.cooley.com",
        "scraper/www.lw.com",
        "scraper/www.gleisslutz.com",
        "scraper/www.sidley.com",
        "scraper/www.stblaw.com",
        "scraper/cms.law",
        "scraper/hengeler-news.com",
        "scraper/www.linklaters.com"
        ]
    api_key_path = 'secret_key.txt'
    with open(api_key_path, 'r') as f:
        api_key = f.readline().strip()
    
    for directory in directories:
        generator = EmbeddingsGenerator(directory, api_key)
        generator.process_directory()
        print(f"Processed and saved embeddings for directory: {directory}")

if __name__ == "__main__":
    main()
