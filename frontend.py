import streamlit as st
import requests

# L'URL del backend verrà fornito da ngrok quando esegui il backend su Colab
BACKEND_URL = "https://1c72-34-142-100-87.ngrok-free.app"  # Sostituisci con l'URL effettivo

st.title("RAG Demo con Ollama e Llama 3.1 by Paolo Risso")

user_question = st.text_input("Inserisci la tua domanda:")

if st.button("Invia"):
    if user_question:
        with st.spinner("Elaborazione in corso..."):
            response = requests.post(f"{BACKEND_URL}/query", json={"question": user_question})
            if response.status_code == 200:
                data = response.json()
                st.subheader("Risposta:")
                st.write(data["answer"])
                st.subheader("Fonti:")
                for i, source in enumerate(data["sources"]):
                    st.write(f"Fonte {i+1}: {source}")
            else:
                st.error("Si è verificato un errore nella richiesta al backend.")
    else:
        st.warning("Per favore, inserisci una domanda.")

