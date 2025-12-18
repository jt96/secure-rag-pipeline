import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

import pytest # noqa: E402
from unittest.mock import patch, MagicMock # noqa: E402
from rag import setup_env, get_rag_chain, print_citations # noqa: E402

@patch("rag.os.getenv")
@patch("rag.sys.exit")
def test_setup_env_exits_when_missing(mock_exit, mock_getenv):
    """
    Verifies that the environment setup terminates the application if 
    essential API keys (Google or Pinecone) are missing.
    """
    # Test API key missing
    mock_getenv.return_value = None
    setup_env()
    mock_exit.assert_called_once_with(1)
    
    mock_exit.reset_mock()
    
    # Test API key one present, one missing
    mock_getenv.side_effect = ["KEY", None]
    setup_env()
    mock_exit.assert_called_once_with(1)
    
def test_print_citations(capsys):
    """
    Ensures that citations are deduplicated based on source and page number
    before being printed to stdout.
    """
    mock_doc = MagicMock()
    mock_doc.metadata = {"source": "test.pdf", "page": 1}
    
    mock_doc2 = MagicMock()
    mock_doc2.metadata = {"source": "test.pdf", "page": 1}
    
    sources = [mock_doc, mock_doc2]
    
    print_citations(sources)
    
    captured = capsys.readouterr()
    
    # Verify exact counts to confirm deduplication
    assert captured.out.count("test.pdf") == 1
    assert captured.out.count("Page 1") == 1
    
@patch("rag.create_retrieval_chain")
@patch("rag.create_stuff_documents_chain")
@patch("rag.create_history_aware_retriever")
@patch("rag.ChatGoogleGenerativeAI")
@patch("rag.PineconeVectorStore")
@patch("rag.HuggingFaceEmbeddings")
@patch("rag.os.environ")
def test_get_rag_chain_initialization(mock_environ, mock_embeddings_class, mock_vectorstore_class, 
                                      mock_llm_class, mock_history_retriever, mock_stuff_chain, 
                                      mock_retrieval_chain):
    """
    Verifies that the RAG pipeline is initialized with the correct components,
    models, and configuration parameters.
    """
    # Configure dictionary access to return a valid index name
    mock_environ.__getitem__.return_value = "Index Name"
    
    # Mock the return values for the chain components
    mock_vectorstore_instance = mock_vectorstore_class.return_value
    mock_vectorstore_instance.as_retriever.return_value = MagicMock()
    mock_retrieval_chain.return_value = "success"
    
    chain = get_rag_chain()
    
    assert chain == "success"
    
    # Verify specific model configuration
    mock_embeddings_class.assert_called_once_with(model_name="all-MiniLM-L6-v2")
    
    # Verify the correct index name was passed to the VectorStore
    _, kwargs = mock_vectorstore_class.call_args
    assert kwargs["index_name"] == "Index Name"

    # Verify all components were initialized
    mock_llm_class.assert_called_once()
    mock_history_retriever.assert_called_once()
    mock_stuff_chain.assert_called_once()
    mock_retrieval_chain.assert_called_once()
    
@patch("rag.sys.exit")
@patch("rag.os.environ")
def test_get_rag_chain_missing_env(mock_environ, mock_exit):
    """
    Verifies that a missing PINECONE_INDEX_NAME raises a KeyError which is 
    caught and handled by a graceful system exit.
    """
    # Simulate a KeyError when the code tries to access os.environ["ANY_KEY"]
    mock_environ.__getitem__.side_effect = KeyError("PINECONE_INDEX_NAME")
    
    mock_exit.side_effect = SystemExit
    
    with pytest.raises(SystemExit):
        get_rag_chain()
    
    mock_exit.assert_called_once_with(1)