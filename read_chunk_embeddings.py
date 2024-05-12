import pandas as pd
import ast

df = pd.read_csv('skadden_chunk_embedding.csv')
df['Embedding'] = df['Embedding'].apply(ast.literal_eval)
print(df)
# for embedding in df['Embedding']:
#     print(type(embedding))