import pandas as pd
import requests
import csv

def create_chunk_batches(dataframe, batch_size=2048):
    total_batches = []
    for start in range(0, len(dataframe), batch_size):
        batch = dataframe[start:start + batch_size]
        total_batches.append(batch['Chunk Text'].tolist())
    return total_batches

def get_embeddings(text_batches):
    url = "https://api.openai.com/v1/embeddings"
    embeddings = []
    for batch in text_batches:
        response = requests.post(url, headers=headers, json={"input": batch, "model": "text-embedding-3-small"})
        for embeddingJSON in response.json()['data']:
            embedding = embeddingJSON["embedding"]
            embeddings.append(embedding)
    return embeddings

def save_embeddings(text_batches, embeddings):
    chunks = []
    for batch in text_batches:
        chunks += batch
    with open('skadden_chunk_embedding.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Chunk Text', 'Embedding'])
        for text, embed in zip(chunks, embeddings):
            writer.writerow([text, embed])

df = pd.read_csv('skadden_chunks.csv')
text_batches = create_chunk_batches(df)
with open('secret_key.txt','r') as f:
    API_KEY = f.readline().strip()
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}
embeddings = get_embeddings(text_batches)
save_embeddings(text_batches, embeddings)