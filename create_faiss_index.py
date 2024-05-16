import os
import pandas as pd
import ast
import numpy as np
import faiss
import pickle

class EmbeddingsIndexer:
    def __init__(self, directories, nlist):
        self.directories = directories
        self.nlist = nlist  
        self.combined_df = None

    def load_and_combine_csvs(self):
        dataframes = []
        for directory in self.directories:
            csv_path = os.path.join(directory, 'chunk_embedding.csv')
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
                df['Embedding'] = df['Embedding'].apply(ast.literal_eval)
                dataframes.append(df)
            else:
                print(f"No CSV found in {directory}")
        if dataframes:
            self.combined_df = pd.concat(dataframes, ignore_index=True)

    def create_faiss_index(self):
        if self.combined_df is not None:
            embeddings = np.array(self.combined_df['Embedding'].tolist()).astype('float32')
            dim = embeddings.shape[1]
            
            quantizer = faiss.IndexFlatL2(dim)  
            index = faiss.IndexIVFFlat(quantizer, dim, self.nlist, faiss.METRIC_L2)
            
            assert not index.is_trained
            index.train(embeddings)  
            assert index.is_trained

            index.add(embeddings)  
            faiss.write_index(index, "embeddings_index_ivfflat.faiss")

    def save_text_mapping(self):
        if self.combined_df is not None:
            with open("index_to_text.pkl", "wb") as f:
                pickle.dump(self.combined_df['Chunk Text'].to_dict(), f)

    def process(self):
        self.load_and_combine_csvs()
        self.create_faiss_index()
        self.save_text_mapping()

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
        "scraper/www/sidley.com"
        ]
    nlist = 50  
    indexer = EmbeddingsIndexer(directories, nlist)
    indexer.process()
    print("IVF Flat Embedding indexing and mapping saved successfully.")

if __name__ == "__main__":
    main()
