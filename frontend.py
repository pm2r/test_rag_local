import streamlit as st
import requests

# L'URL del backend verrà fornito da ngrok quando esegui il backend su Colab
BACKEND_URL = "https://1c72-34-142-100-87.ngrok-free.app"  # Sostituisci con l'URL effettivo

st.title("RAG Demo con Ollama e Llama 3.1 by Paolo Risso")

# Inizializza la chat history nella sessione di Streamlit se non esiste
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Funzione per aggiungere messaggi alla chat history
def add_message(role, content):
    st.session_state.chat_history.append({"role": role, "content": content})

# Funzione per inviare una query al backend
def send_query(question):
    response = requests.post(f"{BACKEND_URL}/query", json={"question": question, "chat_history": st.session_state.chat_history})
    return response.json() if response.status_code == 200 else None

# Funzione per resettare la conversazione
def reset_conversation():
    st.session_state.chat_history = []
    requests.post(f"{BACKEND_URL}/reset")

# Visualizza la chat history
for message in st.session_state.chat_history:
    if message["role"] == "user":
        st.write(f"👤 **Tu**: {message['content']}")
    elif message["role"] == "assistant":
        st.write(f"🤖 **Assistente**: {message['content']}")
    elif message["role"] == "system":
        st.write(f"ℹ️ **Sistema**: {message['content']}")

# Input dell'utente
user_question = st.text_input("Inserisci la tua domanda:")

# Pulsanti per inviare la domanda e resettare la conversazione
col1, col2 = st.columns(2)
with col1:
    if st.button("Invia"):
        if user_question:
            add_message("user", user_question)
            with st.spinner("Elaborazione in corso..."):
                response_data = send_query(user_question)
                if response_data:
                    add_message("assistant", response_data["answer"])
                    # Visualizza le fonti con un font più piccolo
                    with st.expander("Mostra fonti"):
                        for i, source in enumerate(response_data["sources"]):
                            st.markdown(f"<small>Fonte {i+1}: {source}</small>", unsafe_allow_html=True)
                else:
                    add_message("system", "Si è verificato un errore nella richiesta al backend.")
        else:
            st.warning("Per favore, inserisci una domanda.")

with col2:
    if st.button("Reset Conversazione"):
        reset_conversation()
        st.experimental_rerun()

# Scorri automaticamente alla fine della chat
st.markdown('<script>window.scrollTo(0,document.body.scrollHeight);</script>', unsafe_allow_html=True)
