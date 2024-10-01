import streamlit as st
import requests

st.title("Demo RAG con Streamlit e Ollama")

API_ENDPOINT = "https://your-api-gateway-url.com/query"

user_question = st.text_input("Inserisci la tua domanda:")

if st.button("Invia"):
    if user_question:
        with st.spinner("Elaborazione in corso..."):
            response = requests.post(API_ENDPOINT, json={"question": user_question})
            if response.status_code == 200:
                data = response.json()
                st.subheader("Risposta:")
                st.write(data["result"])
                st.subheader("Fonti:")
                for i, source in enumerate(data["sources"]):
                    st.write(f"Fonte {i+1}:")
                    st.write(source)
            else:
                st.error("Si è verificato un errore nella richiesta.")
    else:
        st.warning("Per favore, inserisci una domanda.")
        