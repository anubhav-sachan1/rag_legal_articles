import os
import pandas as pd
import ast
import numpy as np
import faiss
import pickle

class EmbeddingsIndexer:
    def __init__(self, input_directory, output_directory, nlist):
        self.input_directory = input_directory
        self.output_directory = output_directory
        self.nlist = nlist
        self.combined_df = None
        os.makedirs(self.output_directory, exist_ok=True)

    def load_and_combine_csvs(self):
        dataframes = []
        for root, dirs, files in os.walk(self.input_directory):
            for file in files:
                if file == 'chunk_embeddings.csv':
                    csv_path = os.path.join(root, file)
                    df = pd.read_csv(csv_path)
                    df['Embedding'] = df['Embedding'].apply(ast.literal_eval)
                    dataframes.append(df)
        self.combined_df = pd.concat(dataframes, ignore_index=True) if dataframes else pd.DataFrame()

    def create_faiss_index(self):
        if not self.combined_df.empty:
            embeddings = np.array(self.combined_df['Embedding'].tolist()).astype('float32')
            dim = embeddings.shape[1]
            quantizer = faiss.IndexFlatL2(dim)
            index = faiss.IndexIVFFlat(quantizer, dim, self.nlist, faiss.METRIC_L2)
            index.train(embeddings)
            index.add(embeddings)
            faiss.write_index(index, os.path.join(self.output_directory, "embeddings_index_ivfflat.faiss"))

    def save_text_mapping(self):
        if not self.combined_df.empty:
            with open(os.path.join(self.output_directory, "index_to_text.pkl"), "wb") as f:
                pickle.dump(self.combined_df['Chunk Text'].to_dict(), f)

    def process(self):
        self.load_and_combine_csvs()
        self.create_faiss_index()
        self.save_text_mapping()

def main():
    input_directory = "embedder"
    output_directory = "indexer"
    nlist = 200
    indexer = EmbeddingsIndexer(input_directory, output_directory, nlist)
    indexer.process()
    print("IVF Flat Embedding indexing and mapping saved successfully.")

if __name__ == "__main__":
    main()
