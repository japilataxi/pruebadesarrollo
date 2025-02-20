from dotenv import load_dotenv  # Cargar variables desde archivo .env.
from groq import Groq  # Cliente para interactuar con la API de Groq.
import streamlit as st  # Crear la interfaz web interactiva con Streamlit.
import PyPDF2

# Método para cargar las variables del dotenv
load_dotenv()
qclient = Groq()

def extract_text_from_pdf(pdf_file):
    reader = PyPDF2.PdfReader(pdf_file)
    text = "\n".join(page.extract_text() for page in reader.pages if page.extract_text())
    return text

def split_text_into_chunks(text, chunk_size=500, overlap=50):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
    return chunks

st.title("Análisis de Documentos con IA")

uploaded_file = st.file_uploader("Sube un archivo PDF para analizar", type=["pdf"])
if uploaded_file:
    text = extract_text_from_pdf(uploaded_file)
    chunks = split_text_into_chunks(text)
    st.session_state["document_chunks"] = chunks
    st.success("Documento cargado y procesado correctamente.")

# Generar el chat
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message['role']):
        st.markdown(message['content'])

if prompt := st.chat_input("Haz una pregunta sobre el archivo cargado"):
    with st.chat_message("user"):
        st.markdown(prompt)
    
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        document_chunks = st.session_state.get("document_chunks", [])
        relevant_text = " ".join(document_chunks[:3])  # Limitar a los primeros 3 chunks para optimizar la respuesta

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
