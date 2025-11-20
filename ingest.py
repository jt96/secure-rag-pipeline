import os
import sys
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

def ingest_docs():
    file_path = "sample.pdf"

    # Check if file exists before crashing
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        sys.exit(1)

    loader = PyPDFLoader(file_path)
    print("Loading PDF...")
    docs = loader.load()

    # 1000 chars is about 250 words.
    # 200 overlap ensures we don't cut a sentence in half.
    chunk_size = 1000
    chunk_overlap = 200

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    print("Splitting documents...")
    splits = text_splitter.split_documents(docs)

    if not splits:
        print("Warning: No Text found in PDF. Possible scanned image.")
        sys.exit(1)

    print(f"Success! Original Pages: {len(docs)}")
    print(f"Created {len(splits)} vector chunks.")

    # Print the first chunk to prove it worked
    print(f"Content of Chunk 1: \n{splits[0].page_content[:200]}...")

def main():
    try:
        ingest_docs()
    except Exception as e:
        print(f"Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()