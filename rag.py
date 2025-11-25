import os
import sys
from dotenv import load_dotenv
from langchain_pinecone import PineconeVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

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

    template = """
    Answer the user's question based ONLY on the context provided below. 
    If the answer is not in the context, say "I don't know."
    
    Context:
    {context}
    
    Question:
    {input}
    """
    prompt = ChatPromptTemplate.from_template(template)

    document_chain = create_stuff_documents_chain(llm, prompt)
    
    rag_chain = create_retrieval_chain(retriever, document_chain)

    return rag_chain

def main():
    setup_env()
    chain = get_rag_chain()
    
    while True:
        query = input("You: ")
        
        if query.lower() in ["exit", "quit", "q"]:
            print("Ending session.")
            sys.exit(0)
            
        if not query.strip():
            continue
        
        print("Thinking...")
        
        try:
            response = chain.invoke({"input": query})
            print("\nAnswer:")
            print(response["answer"] + "\n")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()