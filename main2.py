from dotenv import load_dotenv  # Cargar variables desde archivo .env
from groq import Groq  # Cliente para interactuar con la API de Groq
import streamlit as st  # Crear la interfaz web con Streamlit
import pandas as pd  # Para leer archivos Excel
from pydantic import BaseModel


def extract_text_from_xlsx(xlsx_file):
    """Extrae texto de un archivo Excel (XLSX), concatenando el contenido de todas las celdas"""
    df = pd.read_excel(xlsx_file)
    text = "\n".join(df.astype(str).apply(lambda x: ' '.join(x), axis=1))
    return text

def split_text_into_chunks(text, chunk_size=500, overlap=50):
    """Divide el texto en fragmentos (chunks) con un solapamiento entre ellos"""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
    return chunks

# Cargar variables de entorno
load_dotenv()
qclient = Groq()

# Interfaz de usuario con Streamlit
st.title("Predicción Electoral")

# Subida de archivos con soporte para múltiples formatos
uploaded_file = st.file_uploader("Sube un archivo", type=["xlsx"])

if uploaded_file:
    # Determinar el tipo de archivo y extraer el texto
    if uploaded_file.name.endswith(".xlsx"):
        text = extract_text_from_xlsx(uploaded_file)
    else:
        st.error("Formato no compatible")
        text = ""
    
    # Dividir el texto en fragmentos (chunks)
    chunks = split_text_into_chunks(text)
    st.session_state["document_chunks"] = chunks
    st.success("Documento cargado y procesado correctamente.")

# Generar el chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostrar mensajes previos
for message in st.session_state.messages:
    with st.chat_message(message['role']):
        st.markdown(message['content'])

# Manejar la entrada del usuario en el chat
if prompt := st.chat_input("Haz una pregunta sobre el archivo cargado"):
    with st.chat_message("user"):
        st.markdown(prompt)
    
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        document_chunks = st.session_state.get("document_chunks", [])
        relevant_text = " ".join(document_chunks[:3])  # Tomar los primeros 3 fragmentos para contexto

        stream_response = qclient.chat.completions.create(
            messages=[
                {"role": "system", "content": "Responde basado en el siguiente texto:\n" + relevant_text},
                {"role": "user", "content": prompt},
            ],
            model="llama-3.3-70b-specdec",
            stream=True
        )

        response_text = "".join(chunk.choices[0].delta.content for chunk in stream_response if chunk.choices[0].delta.content)
        st.markdown(response_text)
    
    st.session_state.messages.append({"role": "assistant", "content": response_text})


#llama-3.1-8b-instant