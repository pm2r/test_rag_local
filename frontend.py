# frontend.py

import streamlit as st
import requests
import logging
import sys
from datetime import datetime

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

# L'URL del backend fornito da ngrok quando esegui il backend su Colab
BACKEND_URL = st.secrets.get("BACKEND_URL", "https://your-ngrok-url.ngrok-free.app")

# Configurazione pagina
st.set_page_config(
    page_title="Business Intelligence Assistant",
    page_icon="🤖",
    layout="wide"
)

# Stili CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 2rem;
    }
    .model-info {
        font-size: 0.8rem;
        color: #666;
        margin-bottom: 1rem;
    }
    .query-mode {
        margin-top: 1rem;
        padding: 1rem;
        background-color: #f0f2f6;
        border-radius: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

# Inizializzazione stato sessione
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'current_model' not in st.session_state:
    st.session_state.current_model = "llama3:70b"
if 'query_mode' not in st.session_state:
    st.session_state.query_mode = "python"

def add_message(role, content, metadata=None):
    """Aggiunge un messaggio alla chat history"""
    message = {
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat(),
        "metadata": metadata or {}
    }
    st.session_state.chat_history.append(message)
    logger.info(f"Added {role} message: {content[:100]}...")

def send_query(question):
    """Invia una query al backend"""
    try:
        chat_history = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in st.session_state.chat_history
            if msg["role"] in ["user", "assistant"]
        ]
        
        payload = {
            "question": question,
            "chat_history": chat_history,
            "model": st.session_state.current_model,
            "mode": st.session_state.query_mode
        }
        
        logger.debug(f"Sending request to backend: {payload}")
        
        response = requests.post(
            f"{BACKEND_URL}/query",
            json=payload,
            timeout=60
        )
        
        if response.status_code != 200:
            logger.error(f"Backend error: {response.status_code} - {response.text}")
            raise Exception(f"Backend returned status code: {response.status_code}")
            
        return response.json()
    
    except requests.exceptions.Timeout:
        logger.error("Request timeout")
        st.error("Request timed out. Please try again.")
    except requests.exceptions.ConnectionError:
        logger.error("Connection error")
        st.error("Could not connect to backend. Please check connection.")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        st.error(f"An unexpected error occurred: {str(e)}")
    
    return None

def reset_conversation():
    """Resetta la conversazione"""
    try:
        response = requests.post(f"{BACKEND_URL}/reset")
        if response.status_code == 200:
            st.session_state.chat_history = []
            logger.info("Conversation reset successful")
            st.success("Conversation reset successfully")
        else:
            logger.warning("Backend reset failed")
            st.warning("Backend reset failed, but chat history cleared locally")
            st.session_state.chat_history = []
    except Exception as e:
        logger.error(f"Error during reset: {str(e)}")
        st.error(f"Error during reset: {str(e)}")
    st.rerun()

# Sidebar con configurazioni
with st.sidebar:
    st.header("Settings")
    
    # Selezione modello LLM
    selected_model = st.selectbox(
        "Select LLM Model",
        [
            "llama3:70b",
            "mixtral:8x7b",
            "llama3.1:70b",
            "mistral-nemo"
        ],
        index=["llama3:70b", "mixtral:8x7b", "llama3.1:70b", "mistral-nemo"].index(st.session_state.current_model)
    )
    
    # Informazioni sul modello
    model_descriptions = {
        "llama3:70b": "High performance general model",
        "mixtral:8x7b": "Efficient analytical model",
        "llama3.1:70b": "Enhanced reasoning model",
        "mistral-nemo": "Business analytics specialist"
    }
    st.markdown(f"<div class='model-info'>{model_descriptions[selected_model]}</div>", unsafe_allow_html=True)
    
    # Selezione modalità query
    query_mode = st.selectbox(
        "Query Mode",
        ["python", "sql"],
        index=0 if st.session_state.query_mode == "python" else 1
    )
    
    # Applica configurazioni
    if st.button("Apply Settings"):
        if selected_model != st.session_state.current_model or query_mode != st.session_state.query_mode:
            response = requests.post(
                f"{BACKEND_URL}/config",
                json={"model": selected_model, "mode": query_mode}
            )
            if response.status_code == 200:
                st.session_state.current_model = selected_model
                st.session_state.query_mode = query_mode
                st.success("Settings updated successfully")
                logger.info(f"Settings updated - Model: {selected_model}, Mode: {query_mode}")
            else:
                st.error("Failed to update settings")
                logger.error("Failed to update settings")

# Main content
st.markdown("<h1 class='main-header'>Business Intelligence Assistant</h1>", unsafe_allow_html=True)

# Display current settings
st.markdown(f"""
    <div class='query-mode'>
        Current Settings:
        - Model: {st.session_state.current_model}
        - Mode: {st.session_state.query_mode}
    </div>
    """, unsafe_allow_html=True)

# Display chat history
for message in st.session_state.chat_history:
    role = message["role"]
    content = message["content"]
    metadata = message.get("metadata", {})

    if role == "user":
        st.write(f"👤 **You**: {content}")
    elif role == "assistant":
        st.write(f"🤖 **Assistant**: {content}")
        
        if "query" in metadata:
            with st.expander(f"Show {metadata['query_type'].upper()} Query"):
                st.code(metadata["query"], language=metadata["query_type"])
        
        if "data" in metadata:
            with st.expander("Show Data"):
                st.dataframe(metadata["data"])
    
    elif role == "system":
        st.write(f"ℹ️ **System**: {content}")

# Input utente
user_question = st.text_input("Ask your question:", key="user_input")

# Buttons
col1, col2 = st.columns(2)
with col1:
    if st.button("Send", type="primary"):
        if user_question:
            add_message("user", user_question)
            with st.spinner("Processing your question..."):
                response = send_query(user_question)
                if response:
                    add_message(
                        "assistant",
                        response["answer"],
                        metadata=response.get("metadata", {})
                    )
            st.rerun()
        else:
            st.warning("Please enter a question.")

with col2:
    if st.button("Reset Conversation"):
        reset_conversation()

# Footer
st.markdown("---")
st.markdown(
    """<div style='text-align: center; color: #666;'>
    Powered by Ollama LLMs • SQL and Python Analysis
    </div>""",
    unsafe_allow_html=True
)