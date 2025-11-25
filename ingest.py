"""
Ingestion Pipeline for RAG

This script loads a PDF document, chunks it into smaller text segments,
and uploads the vector embeddings to Pinecone.

Usage:
    python ingest.py

Environment Variables:
    PINECONE_API_KEY: Required for vector store access.
    PINECONE_INDEX_NAME: The target index in Pinecone.
"""

import os
import sys
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from langchain_huggingface import HuggingFaceEmbeddings

def setup_env():
    print("Loading environment variables...")
    load_dotenv()
    print("Variables loaded.")
    
    pdf_directory = "data"
    
    # Check for PDF folder, create one if it doesn't exist
    if os.path.isdir(pdf_directory):
        if not os.listdir(pdf_directory):
            print(f'PDF folder {pdf_directory}/ is empty. Please add PDFs.')
            sys.exit(0)
    elif not os.path.isdir(pdf_directory):
        os.makedirs(pdf_directory, exist_ok=True)
        print(f'PDF folder {pdf_directory}/ does not exist. Folder has been created, please add PDFs.')
        sys.exit(0)
        

def ingest_docs():
    pdf_directory = "data"

    # Check if file exists before crashing
    if not os.path.exists(pdf_directory):
        print(f"Error: Folder {pdf_directory} not found.")
        sys.exit(1)

    # Load all PDFs in folder
    loader = PyPDFDirectoryLoader(pdf_directory)
    print(f"Loading {len(os.listdir(pdf_directory))} PDFs...")
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
    # print(f"Content of Chunk 1: \n{splits[0].page_content[:200]}...")
    return splits

def connect_to_cloud(splits):
    try:
        PINECONE_INDEX_NAME = os.environ["PINECONE_INDEX_NAME"]
    except Exception as e:
        print(f"Environment variable missing: {e}")
        sys.exit(1)

    # Initialize the "Converter" (Text -> Numbers)
    print("Initializing Local AI Embedding Model...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    # Batch Processing Logic
    batch_size = 50  # Small batch to stay under free tier limits
    total_chunks = len(splits)

    for i in range(0, total_chunks, batch_size):
        batch = splits[i:i+batch_size]
        print(f"Processing batch {i} to {i+len(batch)}")

        try:
            PineconeVectorStore.from_documents(
                documents=batch,
                embedding=embeddings,
                index_name=PINECONE_INDEX_NAME
            )
        except Exception as e:
            print(f"Error on batch: {e}")
            sys.exit(1)
    
    print("Upload complete.")

def main():
    try:
        setup_env()
        text_chunks = ingest_docs()
        connect_to_cloud(text_chunks)
    except Exception as e:
        print(f"Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()