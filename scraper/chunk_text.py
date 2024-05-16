import spacy
from langchain.text_splitter import SpacyTextSplitter

def chunk_text(text, max_chunk_length=4000):
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