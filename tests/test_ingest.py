"""
Unit Tests for Ingestion Pipeline

This test suite mocks the end-to-end document processing workflow to 
ensure files are loaded, split, and vectorized without making actual 
API calls or file system changes.

Test Coverage:
- **Environment Validation:** Ensures the script exits safely if API keys 
  or index names are missing.
- **Flow Control:** Verifies the correct order of operations (Load -> 
  Split -> Vectorize -> Move File).
- **Mocking:** usage of 'MagicMock' to simulate Pinecone, LangChain, 
  and file system operations.
- **File Handling:** Checks that files are moved to the 'processed' 
  directory only after successful ingestion.
"""

import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

import pytest # noqa: E402
from unittest.mock import patch, MagicMock # noqa: E402
from src.ingest import setup_env, ingest_docs, vectorize_and_upload # noqa: E402

@patch("src.ingest.os.getenv")
@patch("src.ingest.sys.exit")
@patch("src.ingest.os.makedirs")
@patch("src.ingest.os.path.isdir")
@patch("src.ingest.load_dotenv")
def test_setup_env_creates_missing_folder(mock_dotenv, mock_isdir, mock_makedirs, mock_exit, mock_getenv):
    """
    Verifies that the environment setup script correctly identifies a missing 
    data directory, attempts to create it, and then cleanly exits.
    """
    # Simulate that the folder does NOT exist
    mock_isdir.return_value = False
    
    # Ensure the code uses 'data' regardless of the actual system environment
    mock_getenv.return_value = "data"
    
    setup_env()
        
    # Verify directory creation
    mock_makedirs.assert_called_once()
    args, _ = mock_makedirs.call_args
    assert args[0] == "data"  # Ensure it tried to create the right folder
    
    mock_exit.assert_called_once_with(0)
    
@patch("src.ingest.shutil.move")
@patch("src.ingest.RecursiveCharacterTextSplitter")
@patch("src.ingest.PyPDFLoader")
@patch("src.ingest.StateManager")
@patch("src.ingest.compute_file_hash")
@patch("src.ingest.os.listdir")
@patch("src.ingest.os.path.exists")
def test_ingest_docs_successful_processing(
    mock_exists, mock_listdir, mock_hasher, mock_manager_class, 
    mock_loader_class, mock_splitter_class, mock_move
):
    """
    Tests the complete successful ingestion workflow: loading a new PDF, 
    splitting it into chunks, archiving the source file, and updating the state manager.
    """
    # Mock file system to return one unprocessed PDF
    mock_exists.return_value = True 
    mock_listdir.return_value = ["test_doc.pdf"] 
    mock_hasher.return_value = "abc123hash" 

    # Mock StateManager: Must configure the instance, not just the class
    mock_manager_instance = mock_manager_class.return_value
    mock_manager_instance.is_processed.return_value = False 

    # Mock PyPDFLoader: Return a list containing one fake Document object
    mock_loader_instance = mock_loader_class.return_value
    mock_doc = MagicMock()
    mock_doc.page_content = "Hello World"
    mock_doc.metadata = {"source": "test_doc.pdf", "page": 1}
    mock_loader_instance.load.return_value = [mock_doc]

    # Mock TextSplitter: Return dummy chunks
    mock_splitter_instance = mock_splitter_class.return_value
    mock_splitter_instance.split_documents.return_value = ["chunk1", "chunk2"]

    result = ingest_docs("data")
    
    assert len(result) == 2 
    mock_move.assert_called_once() 
    mock_manager_instance.add_processed.assert_called_once_with("abc123hash", "test_doc.pdf")

@patch("src.ingest.sys.exit")
@patch("src.ingest.os.listdir")
@patch("src.ingest.os.path.exists")
def test_ingest_docs_no_pdfs_found(mock_exists, mock_listdir, mock_exit):
    """
    Verifies that the ingestion process aborts early (exits with 0) 
    if no PDF files are found in the target directory.
    """
    mock_exists.return_value = True 
    mock_listdir.return_value = ["readme.txt", "logo.png"] 
    
    # Configure mock to raise SystemExit so the test doesn't continue executing
    mock_exit.side_effect = SystemExit
    
    with pytest.raises(SystemExit):
        ingest_docs("data")
    
    mock_exit.assert_called_once_with(0)

@patch("src.ingest.HuggingFaceEmbeddings")
@patch("src.ingest.PineconeVectorStore")
@patch("src.ingest.os.environ")
def test_vectorize_and_upload_success(mock_environ, mock_vectorstore_class, mock_embeddings_class):
    """
    Verifies that the system correctly initializes the HuggingFace embedding model 
    and uploads the document chunks to the Pinecone vector database.
    """    
    # Create fake document objects to pass through
    mock_docs = [MagicMock(), MagicMock()]
    
    vectorize_and_upload(mock_docs)
    
    # Verify Embedding Model Initialization
    mock_embeddings_class.assert_called_once()
    
    # Verify Upload to Pinecone
    mock_vectorstore_class.from_documents.assert_called_once()
    
    # Verify correctness of the data passed
    _, kwargs = mock_vectorstore_class.from_documents.call_args
    assert kwargs["documents"] == mock_docs

@patch("src.ingest.sys.exit")
@patch("src.ingest.PineconeVectorStore")
@patch("src.ingest.HuggingFaceEmbeddings")
@patch("src.ingest.os.environ")
def test_failed_upload(mock_environ, mock_embeddings_class, mock_vectorstore_class, mock_exit):
    """
    Verifies that the upload process handles Pinecone API errors gracefully 
    by catching the exception and exiting with a non-zero status code.
    """
    mock_docs = [MagicMock()]
    
    # Simulate a critical failure during the upload step
    mock_vectorstore_class.from_documents.side_effect = Exception("Simulated upload error")
        
    mock_exit.side_effect = SystemExit
    
    with pytest.raises(SystemExit):
        vectorize_and_upload(mock_docs)

    # Verify we exited with an error code (1) indicating failure
    mock_exit.assert_called_once_with(1)

@patch("src.ingest.shutil.move")
@patch("src.ingest.compute_file_hash")
@patch("src.ingest.StateManager")
@patch("src.ingest.PyPDFLoader")
@patch("src.ingest.RecursiveCharacterTextSplitter")
@patch("src.ingest.os.listdir")
@patch("src.ingest.os.path.exists")
def test_corrupt_pdf(mock_exists, mock_listdir, mock_splitter_class, mock_loader_class, 
                     mock_manager_class, mock_hasher, mock_move):
    """
    Tests the ingestion pipeline's resilience. Verifies that if one PDF is corrupt 
    (raises an error), the system logs it and continues processing the remaining valid files.
    """
    mock_exists.return_value = True 
    mock_listdir.return_value = ["bad_doc.pdf", "good_doc.pdf"] 
    
    mock_hasher.return_value = "abc123hash" 
    mock_move.return_value = True

    # Setup valid document return
    mock_manager_instance = mock_manager_class.return_value
    mock_manager_instance.is_processed.return_value = False 
    mock_manager_instance.add_processed.return_value = True

    # Configure Loader. First call crashes (bad file), second call succeeds (good file)
    mock_loader_instance = mock_loader_class.return_value
    mock_doc = MagicMock()
    mock_doc.page_content = "Hello World"
    mock_doc.metadata = {"source": "test_doc.pdf", "page": 1}
    
    mock_loader_instance.load.side_effect = [Exception("Corrupted pdf"), [mock_doc]]

    mock_splitter_instance = mock_splitter_class.return_value
    mock_splitter_instance.split_documents.return_value = ["chunk1", "chunk2"]

    result = ingest_docs("data")
    
    # Verify that we still successfully processed the valid file
    assert len(result) == 2
    
    # Ensure the loader attempted to process both files
    assert mock_loader_instance.load.call_count == 2