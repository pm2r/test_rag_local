import streamlit as st
import requests
import logging
import sys
from datetime import datetime
import json

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('frontend.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configurazione Streamlit
st.set_page_config(
    page_title="Business Intelligence Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configurazione backend
BACKEND_URL = st.secrets.get("BACKEND_URL", "https://your-ngrok-url.ngrok-free.app")

# Stili CSS personalizzati
st.markdown("""
    <style>
    .stAlert {
        background-color: #f0f2f6;
        border: 1px solid #e0e2e6;
        padding: 1rem;
        border-radius: 0.5rem;
    }
    .sql-query {
        background-color: #1e1e1e;
        color: #d4d4d4;
        padding: 1rem;
        border-radius: 0.3rem;
        font-family: 'Courier New', monospace;
    }
    .data-table {
        margin-top: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

class AssistantInterface:
    def __init__(self):
        self.initialize_session_state()
        
    def initialize_session_state(self):
        """Inizializza o resetta lo stato della sessione"""
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        if 'current_mode' not in st.session_state:
            st.session_state.current_mode = "hybrid"  # hybrid, rag, sql
        if 'error_count' not in st.session_state:
            st.session_state.error_count = 0

    def add_message(self, role, content, metadata=None):
        """Aggiunge un messaggio alla chat history con metadata opzionale"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        st.session_state.chat_history.append(message)
        logger.info(f"Added message: {role} - {content[:100]}...")

    def send_query(self, question, mode=None):
        """Invia una query al backend con gestione errori avanzata"""
        try:
            mode = mode or st.session_state.current_mode
            chat_history = [
                {"role": msg["role"], "content": msg["content"]}
                for msg in st.session_state.chat_history
                if msg["role"] in ["user", "assistant"]
            ]

            payload = {
                "question": question,
                "chat_history": chat_history,
                "mode": mode
            }

            logger.debug(f"Sending request to backend: {payload}")
            
            response = requests.post(
                f"{BACKEND_URL}/query",
                json=payload,
                timeout=60  # Aumentato timeout per query complesse
            )
            
            if response.status_code != 200:
                logger.error(f"Backend error: {response.status_code} - {response.text}")
                raise Exception(f"Backend returned status code: {response.status_code}")

            result = response.json()
            logger.info("Received successful response from backend")
            st.session_state.error_count = 0  # Reset error count on success
            return result

        except requests.exceptions.Timeout:
            logger.error("Request timeout")
            self.handle_error("Request timed out. Please try again.")
        except requests.exceptions.ConnectionError:
            logger.error("Connection error")
            self.handle_error("Could not connect to backend. Please check connection.")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            self.handle_error(f"An unexpected error occurred: {str(e)}")
        
        return None

    def handle_error(self, error_message):
        """Gestisce gli errori con retry automatico e fallback"""
        st.session_state.error_count += 1
        if st.session_state.error_count >= 3:
            self.add_message("system", "Multiple errors occurred. Switching to fallback mode.")
            # Implementare logica di fallback
        st.error(error_message)

    def reset_conversation(self):
        """Resetta la conversazione e notifica il backend"""
        try:
            response = requests.post(f"{BACKEND_URL}/reset")
            if response.status_code == 200:
                self.initialize_session_state()
                logger.info("Conversation reset successful")
                st.success("Conversation reset successfully")
            else:
                logger.warning("Backend reset failed but proceeding with frontend reset")
                self.initialize_session_state()
        except Exception as e:
            logger.error(f"Error during reset: {str(e)}")
            self.initialize_session_state()
        st.rerun()

    def render_message(self, message):
        """Renderizza un messaggio della chat con formattazione appropriata"""
        role = message["role"]
        content = message["content"]
        metadata = message.get("metadata", {})

        if role == "user":
            st.write(f"👤 **You**: {content}")
        elif role == "assistant":
            st.write(f"🤖 **Assistant**: {content}")
            
            # Visualizza query SQL se presente
            if "sql_query" in metadata:
                with st.expander("Show SQL Query"):
                    st.code(metadata["sql_query"], language="sql")
            
            # Visualizza dati se presenti
            if "data" in metadata:
                with st.expander("Show Data"):
                    st.dataframe(metadata["data"])
            
            # Visualizza fonti RAG se presenti
            if "sources" in metadata:
                with st.expander("Show Sources"):
                    for src in metadata["sources"]:
                        st.markdown(f"**Source**: {src['content']}")
                        if "metadata" in src:
                            st.json(src["metadata"])
        
        elif role == "system":
            st.write(f"ℹ️ **System**: {content}")

    def render_interface(self):
        """Renderizza l'interfaccia utente principale"""
        st.title("🤖 Business Intelligence Assistant")
        
        # Sidebar per configurazioni
        with st.sidebar:
            st.header("Settings")
            mode = st.selectbox(
                "Query Mode",
                ["hybrid", "sql", "rag"],
                index=["hybrid", "sql", "rag"].index(st.session_state.current_mode)
            )
            if mode != st.session_state.current_mode:
                st.session_state.current_mode = mode
                logger.info(f"Mode changed to: {mode}")

        # Display chat history
        for message in st.session_state.chat_history:
            self.render_message(message)

        # Input utente
        user_question = st.text_input("Ask a business question:", key="user_input")

        # Bottoni azione
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Send", type="primary"):
                if user_question:
                    self.add_message("user", user_question)
                    with st.spinner("Processing your question..."):
                        response_data = self.send_query(user_question)
                        if response_data:
                            self.add_message(
                                "assistant",
                                response_data["answer"],
                                metadata={
                                    "sql_query": response_data.get("sql_query"),
                                    "data": response_data.get("data"),
                                    "sources": response_data.get("sources")
                                }
                            )
                    st.rerun()
                else:
                    st.warning("Please enter a question.")

        with col2:
            if st.button("Reset Conversation"):
                self.reset_conversation()

def main():
    try:
        assistant = AssistantInterface()
        assistant.render_interface()
    except Exception as e:
        logger.error(f"Critical error in main: {str(e)}")
        st.error("A critical error occurred. Please refresh the page.")

if __name__ == "__main__":
    main()