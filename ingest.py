"""
Ingestion Pipeline for RAG

This script loads PDF documents from a configured directory, chunks them 
into smaller text segments, and uploads the vector embeddings to Pinecone.

It implements an idempotent workflow:
1. Scans the source directory for new PDF files.
2. Ingests and vectorizes the content.
3. Moves processed files to a 'processed/' subdirectory to prevent re-ingestion.

Usage:
    python ingest.py

Environment Variables:
    PINECONE_API_KEY: Required. API key for the Pinecone vector database.
    PINECONE_INDEX_NAME: Required. Name of the target Pinecone index.
    DATA_FOLDER: Optional. Path to the directory containing PDFs to ingest. 
                 Defaults to 'data'.
"""

import os
import sys
import shutil
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_pinecone import PineconeVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from state_manager import StateManager, compute_file_hash

def setup_env():
    """
    Validates environment variables and directory structure.
    
    Returns:
        str: The path to the data directory.
    """
    print("Loading environment variables...")
    load_dotenv()
    
    data_folder = os.getenv("DATA_FOLDER", "data")
        
    # Check for PDF folder, create one if it doesn't exist
    if not os.path.isdir(data_folder):
        os.makedirs(data_folder, exist_ok=True)
        print(f'PDF folder {data_folder}/ does not exist. Folder has been created, please add PDFs.')
        sys.exit(0)
    
    return data_folder

def ingest_docs(data_folder):
    """
    Loads PDFs, splits them into chunks, and archives source files.

    Args:
        data_folder (str): Path to the directory containing PDFs.

    Returns:
        List[Document]: A list of chunked langchain Document objects.
    """
    processed_folder = os.path.join(data_folder, "processed")
    
    if not os.path.exists(processed_folder):
        os.makedirs(processed_folder)
        
    # Filter for PDFs only
    files = os.listdir(data_folder)
    pdf_files = [f for f in files if f.lower().endswith(".pdf")]
    
    if not pdf_files:
        print(f'Warning: No new PDFs found in {data_folder}.')
        sys.exit(0)

    # Load all PDFs in folder
    docs = []
    print(f"Loading {len(pdf_files)} PDFs from '{data_folder}'...")
    
    manager = StateManager()
    successful_files = {} # Stores {filename: hash} to avoid re-hashing later
    
    for pdf_file in pdf_files:
        file_path = os.path.join(data_folder, pdf_file)
        
        file_hash = compute_file_hash(file_path)
        if not file_hash:
            print(f"Skipping {pdf_file}: Could not compute hash.")
            
        if manager.is_processed(file_hash):
            print(f"Skipping {pdf_file}: Already processed.")
            continue
        
        try:
            loader = PyPDFLoader(file_path)
            docs.extend(loader.load())
            successful_files[pdf_file] = file_hash
        except Exception as e:
            print(f"Error loading {pdf_file}: {e} (SKIPPING)")
            continue
        
    if not docs:
        print("No new documents to process.")
        sys.exit(0)

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
    
    print(f"Moving processed files to {processed_folder}")
    for file_name, file_hash in successful_files.items():
        src_path = os.path.join(data_folder, file_name)
        dst_path = os.path.join(processed_folder, file_name)
        try:
            shutil.move(src_path, dst_path)
            
            # Update state ONLY after successful move to prevent data mismatch
            manager.add_processed(file_hash, file_name)
            
            print(f"Moved: {file_name} from {data_folder} to {processed_folder}")
        except Exception as e:
            print(f"Failed to move {file_name}: {e}")
            continue
    
    return splits

def vectorize_and_upload(splits):
    """
    Generates embeddings and uploads chunks to Pinecone in batches.

    Args:
        splits (List[Document]): List of document chunks to upload.
    """
    try:
        PINECONE_INDEX_NAME = os.environ["PINECONE_INDEX_NAME"]
    except Exception as e:
        print(f"Environment variable missing: {e}")
        sys.exit(1)

    # Initialize Local Embeddings (HuggingFace/all-MiniLM-L6-v2)
    # Note: If changing this model, ensure 'chunk_size' in ingest_docs is updated to match new token limits.
    print("Initializing Local AI Embedding Model...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    # batch_size=50: Prevents hitting Pinecone request size limits (2MB)
    batch_size = 50
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
        data_path = setup_env()
        text_chunks = ingest_docs(data_path)
        if text_chunks:
            vectorize_and_upload(text_chunks)
    except Exception as e:
        print(f"Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()