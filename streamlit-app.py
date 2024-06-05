import streamlit as st
import requests

st.title("Document Query Assistant")

# API endpoints
upload_pdf_url = "http://localhost:8080/pdf"
ask_pdf_url = "http://localhost:8080/ask_pdf"

# File upload section
st.header("Upload PDF")
uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

if uploaded_file is not None:
    files = {'file': (uploaded_file.name, uploaded_file, 'application/pdf')}
    response = requests.post(upload_pdf_url, files=files)
    if response.status_code == 200:
        st.success("PDF uploaded successfully!")
    else:
        st.error("Failed to upload PDF.")

# Query section
st.header("Ask a Question")
query = st.text_input("Enter your question:")

if st.button("Submit"):
    if query:
        data = {"query": query}
        response = requests.post(ask_pdf_url, json=data)
        if response.status_code == 200:
            result = response.json()
            answer = result.get("answer", "No answer found.")
            sources = result.get("sources", [])

            st.subheader("Answer")
            st.write(answer)

            # if sources:
            #     st.subheader("Sources")
            #     for source in sources:
            #         st.write(f"Source: {source['source']}")
            #         st.write(f"Content: {source['page_content']}")
        else:
            st.error("Failed to get an answer.")
    else:
        st.warning("Please enter a query.")
