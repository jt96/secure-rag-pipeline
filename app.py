"""
Streamlit Web Interface for Hybrid RAG Infrastructure

This script launches a web-based chat interface that allows users to interact 
with the RAG pipeline in a user-friendly environment. It manages the user session, 
visualizes chat history, and renders source citations for transparency.

Features:
- **Persistent Session:** Caches the RAG chain and chat history across re-runs.
- **Interactive Chat:** Renders user and AI messages using Streamlit's chat components.
- **Advanced Citations:** Displays deduplicated source documents in an expandable section.
  - Handles "Unknown" source files gracefully.
  - Deduplicates by Page Number (if known) or Content Hash (if metadata is missing).
  - Cleans up snippet text for readability.
- **Graceful Exit:** Handles "exit/quit" commands by stopping script execution safely.

Usage:
    streamlit run app.py
    # OR via Docker
    docker compose run --service-ports hybrid-rag-app
"""

import streamlit as st
from rag import get_rag_chain, setup_env

def setup_chat():
    """
    Main application logic. 
    Initializes the UI, manages session state, and handles the chat event loop.
    """
    st.set_page_config(page_title="Hybrid RAG Agent", page_icon="🤖")
    st.title("Hybrid RAG Agent")

    # Streamlit re-runs this script on every interaction. We check session_state
    # to ensure we only load the heavy RAG models once.
    if "chain" not in st.session_state:
        with st.spinner("Loading RAG Pipeline..."):
            try:
                setup_env()
                st.session_state.chain = get_rag_chain()
                st.success("System ready.")
            except Exception as e:
                st.error(f"Failed to load RAG chain: {e}")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Re-draw all previous messages because Streamlit resets the interface on every run.
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if (prompt := st.chat_input("Ask about your documents...")) and prompt.strip():
        if prompt.lower() in ["exit", "quit", "q"]:
            st.session_state.messages = []
            st.warning("Session Reset. Type a new question or refresh the page to start over.")
            st.stop()
                
        # Render User Message
        with st.chat_message("user"):
            st.markdown(prompt)
            
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Generate AI Response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("Thinking...")
            
            try:
                # Convert Streamlit's JSON format [{"role": "user"}] to LangChain's 
                # Tuple format [("human", "content")] so the RAG chain can read the history.
                chat_history = []
                for msg in st.session_state.messages[:-1]:
                    role = "human" if msg["role"] == "user" else "ai"
                    chat_history.append((role, msg["content"]))
                response = st.session_state.chain.invoke({"input": prompt,
                                                          "chat_history": chat_history})
                answer = response["answer"]
                sources = response["context"]
                
                message_placeholder.markdown(answer)
                
                # Only show source citations if the user asks a substantive question.
                # Hiding sources for "Hi/Thanks" keeps the interface clean.
                keywords = ["thank", "thanks", "goodbye", "bye", "hello", "hi"]
                is_conversational = len(prompt.split()) < 4 or any(word in prompt.lower() for word in keywords)
                
                if sources and not is_conversational:
                    with st.expander("Click to view sources."):
                        unique_sources = set()
                        for document in sources:
                            file_source = document.metadata.get("source", "Unknown").replace("\\", "/")
                            raw_page = document.metadata.get("page", "Unknown")
                            page_num = int(raw_page) if isinstance(raw_page, (int, float)) else raw_page
                            
                            # Handles edge case where file name is unknown but page number is the same and vice versa.
                            if file_source != "Unknown" and page_num != "Unknown":
                                source_key = (file_source, page_num)
                            else:
                                source_key = (file_source, page_num, document.page_content[:50])
                                
                            if source_key not in unique_sources:
                                unique_sources.add(source_key)
                                
                                snippet = document.page_content[:200].replace("\n", " ") + "..."
                            
                                st.markdown(f"Source: {file_source} (Page {page_num})")
                                st.caption(f"\"{snippet}\"")
                
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as e:
                message_placeholder.error(f"Error {e}")

def main():
    setup_chat()

if __name__ == "__main__":
    main()