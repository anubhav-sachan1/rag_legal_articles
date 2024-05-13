from langchain.text_splitter import SpacyTextSplitter

def chunk_text(text):
    text_splitter = SpacyTextSplitter()
    chunks = text_splitter.split_text(text)
    return chunks