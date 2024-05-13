import pandas as pd
import ast
import numpy as np
import faiss
import pickle

# Load the CSV
df = pd.read_csv('skadden_chunk_embedding.csv')
df['Embedding'] = df['Embedding'].apply(ast.literal_eval)

# Convert embeddings to a suitable numpy array
embeddings = np.array(df['Embedding'].tolist()).astype('float32')

# Create and populate FAISS index
dim = embeddings.shape[1]
index = faiss.IndexFlatL2(dim)
index.add(embeddings)

# Save the index
faiss.write_index(index, "embeddings_index.faiss")

# Save the mapping from index to chunk text
with open("index_to_text.pkl", "wb") as f:
    pickle.dump(df['Chunk Text'].to_dict(), f)
