# frontend.py

import streamlit as st
import requests
import logging
import sys
from datetime import datetime

# -----------------------------------------------------------------------------
# Configurazione Base Logging
# -----------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('frontend.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Configurazione Connessione Backend
# -----------------------------------------------------------------------------
# Sostituire con il tuo URL ngrok
BACKEND_URL = st.secrets.get("BACKEND_URL", "https://af27-34-147-36-231.ngrok-free.app" )

# -----------------------------------------------------------------------------
# Configurazione Pagina e Stile
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="CRM GPT by Paolo",
    page_icon="🏦",
    layout="wide"
)

# Stili CSS - Personalizzabili per il brand
# Modificare i colori qui per adattarli al proprio brand
st.markdown("""
    <style>
    /* Colori principali - Modificare questi valori per cambiare il tema */
    :root {
        --primary-color: #25367b;        /* Colore principale */
        --primary-light: #3e4d96;        /* Variante chiara del principale */
        --background-light: #f5f6f8;     /* Sfondo chiaro */
        --text-primary: #333333;         /* Testo principale */
        --text-light: #ffffff;           /* Testo chiaro */
        --border-color: #e6e6e6;         /* Colore bordi */
    }

    /* Header principale */
    .main-header {
        background-color: var(--primary-color);
        color: var(--text-light);
        padding: 2rem;
        border-radius: 0;
        margin: -1rem -1rem 2rem -1rem;
        text-align: center;
    }

    .main-title {
        font-size: 2.5rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }

    .subtitle {
        font-size: 1.2rem;
        opacity: 0.9;
    }

    /* Personalizzazione sidebar */
    .css-1d391kg {
        background-color: var(--background-light);
    }

    /* Stile pulsanti */
    .stButton>button {
        background-color: var(--primary-color);
        color: var(--text-light);
        border-radius: 20px;
        padding: 0.5rem 2rem;
        border: none;
        font-weight: 500;
        transition: background-color 0.3s ease;
    }

    .stButton>button:hover {
        background-color: var(--primary-light);
    }

    /* Container messaggi chat */
    .chat-message {
        padding: 1rem;
        border-radius: 5px;
        margin-bottom: 1rem;
        border-left: 4px solid var(--primary-color);
    }

    .user-message {
        background-color: var(--background-light);
    }

    .assistant-message {
        background-color: var(--text-light);
        border: 1px solid var(--border-color);
    }

    /* Pannello impostazioni */
    .settings-panel {
        background-color: var(--text-light);
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    /* Footer */
    .footer {
        text-align: center;
        padding: 2rem;
        color: var(--text-primary);
        border-top: 1px solid var(--border-color);
        margin-top: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Gestione Stato Applicazione
# -----------------------------------------------------------------------------
# Inizializzazione stati se non esistono
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'current_model' not in st.session_state:
    st.session_state.current_model = "llama3:70b"
if 'query_mode' not in st.session_state:
    st.session_state.query_mode = "python"

# -----------------------------------------------------------------------------
# Funzioni Utility
# -----------------------------------------------------------------------------
def add_message(role, content, metadata=None):
    """Aggiunge un messaggio alla cronologia della chat"""
    message = {
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat(),
        "metadata": metadata or {}
    }
    st.session_state.chat_history.append(message)
    logger.info(f"Added {role} message: {content[:100]}...")

def send_query(question):
    """Gestisce l'invio delle query al backend"""
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
            raise Exception(f"Backend returned status code: {response.status_code}")
            
        return response.json()
    
    except Exception as e:
        logger.error(f"Query error: {str(e)}")
        st.error(f"Error processing query: {str(e)}")
        return None

def reset_conversation():
    """Resetta la conversazione e pulisce la cronologia"""
    try:
        response = requests.post(f"{BACKEND_URL}/reset")
        st.session_state.chat_history = []
        logger.info("Conversation reset successful")
        st.success("Conversation reset complete")
    except Exception as e:
        logger.error(f"Reset error: {str(e)}")
        st.error(f"Error during reset: {str(e)}")
    st.rerun()

# -----------------------------------------------------------------------------
# Interfaccia Utente
# -----------------------------------------------------------------------------
# Header principale
st.markdown("""
    <div class="main-header">
        <div class="main-title">CRM GPT by Paolo</div>
        <div class="subtitle">Intelligent Marketing Assistant</div>
    </div>
""", unsafe_allow_html=True)

# Sidebar per configurazioni
with st.sidebar:
    st.header("Settings")
    
    # Configurazione modelli - Personalizzabile
    models_info = {
        "llama3:70b": "High performance general model",
        "mixtral:8x7b": "Efficient analytical model",
        "llama3.1:70b": "Enhanced reasoning model",
        "mistral-nemo": "Business analytics specialist"
    }
    
    selected_model = st.selectbox(
        "Select AI Model",
        list(models_info.keys()),
        index=list(models_info.keys()).index(st.session_state.current_model)
    )
    
    st.info(models_info[selected_model])
    
    # Modalità query
    query_mode = st.selectbox(
        "Analysis Mode",
        ["python", "sql"],
        index=0 if st.session_state.query_mode == "python" else 1
    )
    
    if st.button("Apply Settings"):
        try:
            response = requests.post(
                f"{BACKEND_URL}/config",
                json={"model": selected_model, "mode": query_mode}
            )
            if response.status_code == 200:
                st.session_state.current_model = selected_model
                st.session_state.query_mode = query_mode
                st.success("Settings updated")
                logger.info(f"Settings updated - Model: {selected_model}, Mode: {query_mode}")
            else:
                st.error("Settings update failed")
        except Exception as e:
            st.error(f"Error updating settings: {str(e)}")

# Area principale
# Mostra impostazioni correnti
st.markdown(f"""
    <div class="settings-panel">
        <strong>Current Configuration:</strong><br>
        Model: {st.session_state.current_model}<br>
        Mode: {st.session_state.query_mode}
    </div>
""", unsafe_allow_html=True)

# Visualizzazione cronologia chat
for message in st.session_state.chat_history:
    css_class = "user-message" if message["role"] == "user" else "assistant-message"
    
    st.markdown(f"""
        <div class="chat-message {css_class}">
            <strong>{'👤 You' if message["role"] == "user" else '🤖 Assistant'}</strong><br>
            {message["content"]}
        </div>
    """, unsafe_allow_html=True)
    
    # Mostra metadati se presenti
    if message["role"] == "assistant" and "metadata" in message:
        metadata = message["metadata"]
        if "query" in metadata:
            with st.expander(f"Show {metadata['query_type'].upper()} Details"):
                st.code(metadata["query"], language=metadata["query_type"])
        if "data" in metadata:
            with st.expander("Show Data"):
                st.dataframe(metadata["data"])

# Input utente
user_input = st.text_input("Ask your question:", key="user_input")

# Pulsanti azione
col1, col2 = st.columns(2)
with col1:
    if st.button("Send", type="primary"):
        if user_input:
            add_message("user", user_input)
            with st.spinner("Processing..."):
                response = send_query(user_input)
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
st.markdown("""
    <div class="footer">
        <p>Powered by Advanced AI • by Paolo</p>
    </div>
""", unsafe_allow_html=True)

if __name__ == "__main__":
    logger.info("Frontend application started")
