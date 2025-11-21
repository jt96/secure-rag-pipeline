"""
Database Verification Script

Performs a semantic search query against the Pinecone index to verify
that data was uploaded correctly and is retrievable.

"""

import os
import sys
from ingest import setup_env
from langchain_pinecone import PineconeVectorStore
from langchain_huggingface import HuggingFaceEmbeddings


def test_index():
    try:
        PINECONE_INDEX_NAME = os.environ["PINECONE_INDEX_NAME"]
    except Exception as e:
        print(f"Environment variable missing: {e}")
        sys.exit(1)
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vector_store = PineconeVectorStore(
        embedding=embeddings,
        index_name=PINECONE_INDEX_NAME)
    query = "legal advice"
    results = vector_store.similarity_search(query=query)
    for result in results:
        print(result.page_content)
    
def main():
    setup_env()
    test_index()

if __name__ == "__main__":
    main()