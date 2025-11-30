import streamlit as st
from rag import get_rag_chain, setup_env

def setup_chat():
    st.set_page_config(page_title="SecureGov RAG", page_icon="🛡️")
    st.title("SecureGov RAG Agent")

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

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask about your documents..."):
        if prompt.lower() in ["exit", "quit", "q"]:
            st.warning("Ending session... Refresh the page to start over.")
            st.stop()
                
        with st.chat_message("user"):
            st.markdown(prompt)
            
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("Thinking...")
            
            try:
                chat_history = []
                for msg in st.session_state.messages[:-1]:
                    role = "human" if msg["role"] == "user" else "ai"
                    chat_history.append((role, msg["content"]))
                response = st.session_state.chain.invoke({"input": prompt,
                                                          "chat_history": chat_history})
                answer = response["answer"]
                sources = response["context"]
                
                message_placeholder.markdown(answer)
                
                if sources:
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