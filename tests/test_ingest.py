import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

import pytest # noqa: E402
from unittest.mock import patch, MagicMock # noqa: E402
from ingest import setup_env, ingest_docs # noqa: E402

@patch("ingest.os.getenv")
@patch("ingest.sys.exit")
@patch("ingest.os.makedirs")
@patch("ingest.os.path.isdir")
@patch("ingest.load_dotenv")
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
    
@patch("ingest.shutil.move")
@patch("ingest.RecursiveCharacterTextSplitter")
@patch("ingest.PyPDFLoader")
@patch("ingest.StateManager")
@patch("ingest.compute_file_hash")
@patch("ingest.os.listdir")
@patch("ingest.os.path.exists")
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
    

@patch("ingest.sys.exit")
@patch("ingest.os.listdir")
@patch("ingest.os.path.exists")
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