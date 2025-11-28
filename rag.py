"""
RAG Chatbot Interface

This script runs an interactive command-line interface (CLI) for chatting 
with the ingested document knowledge base. It uses a Retrieval-Augmented 
Generation (RAG) pipeline to answer user questions based strictly on 
the provided context.

Architecture:
- Retriever: Local HuggingFace embeddings search the Pinecone vector store.
- Generator: Google Gemini (LLM) synthesizes the final answer.

Usage:
    python rag.py

Environment Variables:
    GOOGLE_API_KEY: Required. API key for Google Gemini (Generative AI).
    PINECONE_API_KEY: Required. API key for the Pinecone vector database.
    PINECONE_INDEX_NAME: Required. Name of the Pinecone index to query.
"""

import os
import sys
from dotenv import load_dotenv
from langchain_pinecone import PineconeVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.chains import create_retrieval_chain, create_history_aware_retriever
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


def setup_env():
    load_dotenv()
    if not os.getenv("GOOGLE_API_KEY") or not os.getenv("PINECONE_API_KEY"):
        print("Error: Missing API keys in .env")
        sys.exit(1)

def get_rag_chain():
    """
    Creates the RAG chain by combining the Retriever (Pinecone) and Generator (Gemini).
    """
    try:
        PINECONE_INDEX_NAME = os.environ["PINECONE_INDEX_NAME"]
    except Exception as e:
        print(f"Environment variable missing: {e}")
        sys.exit(1)

    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    vector_store = PineconeVectorStore(
        embedding=embeddings,
        index_name=PINECONE_INDEX_NAME)
    
    retriever = vector_store.as_retriever(search_kwargs={"k": 6})

    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
    
    # Instructs the LLM to rephrase the question based on history.
    contextualize_q_system_prompt = """
    Given a chat history and the latest user question which might reference context in the chat history, 
    formulate a standalone question which can be understood without the chat history. 
    Do NOT answer the question, just reformulate it if needed and otherwise return it as is."""
    
    # Build the prompt template that includes the chat history placeholder
    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
        ]
    )

    # It doesn't answer the question; it just finds the right documents.
    history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_q_prompt)
    
    # Instructs the LLM to act as a Q&A assistant using specific context.
    qa_system_prompt = """
    You are an assistant for question-answering tasks. 
    Use the following pieces of retrieved context to answer the question. 
    If you don't know the answer, just say that you don't know. 
    
    {context}"""
    
    # Feeds System Prompt + History + Question to the LLM
    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", qa_system_prompt),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
        ]
    )
    
    # This component puts the retrieved documents into the {context} variable of qa system prompt.
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    
    # This connects the search step (retriever) to the answer step (document chain).
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    return rag_chain

def main():
    setup_env()
    chain = get_rag_chain()
    
    chat_history = []
    
    print("Chat Ready. Type 'exit', 'quit' or 'q' to quit.")
    
    while True:
        query = input("You: ")
        
        if query.lower() in ["exit", "quit", "q"]:
            print("Ending session.")
            sys.exit(0)
            
        if not query.strip():
            continue
        
        print("Thinking...")
        
        try:
            response = chain.invoke({"input": query,
                                     "chat_history": chat_history})
            answer = response["answer"]
            print("\nAnswer:")
            print(answer + "\n")
            chat_history.append(("human", query))
            chat_history.append(("ai", answer))
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()