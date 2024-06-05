import os
import uuid
import pandas as pd
from flask import Flask, request, jsonify
from langchain_community.llms import Ollama
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_community.document_loaders import PDFPlumberLoader
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain.prompts import PromptTemplate
from pandasai import SmartDataframe
from pandasai.llm.local_llm import LocalLLM

app = Flask(__name__)

pdf_directory = "pdf"
csv_directory = "csv"

cached_llm = Ollama(model="llama3", temperature=0.7)

embedding = FastEmbedEmbeddings()

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1024, chunk_overlap=80, length_function=len, is_separator_regex=False
)

raw_prompt = PromptTemplate.from_template(
    """ 
    <s>[INST] You are a technical assistant good at searching documents. If you do not have an answer from the provided information say so. [/INST] </s>
        {input}
           Context: {context}
           Answer:
"""
)

@app.route("/ai", methods=["POST"])
def aiPost():
    print("Post /ai called")
    json_content = request.json
    query = json_content.get("query")

    print(f"query: {query}")

    response = cached_llm.invoke(query)

    print(response)

    response_answer = {"answer": response}
    return response_answer

@app.route("/ask_pdf", methods=["POST"])
def askPDFPost():
    print("Post /ask_pdf called")
    json_content = request.json
    query = json_content.get("query")

    print(f"query: {query}")

    unique_id = json_content.get("unique_id")
    vector_store_directory = os.path.join("db", unique_id)

    print("Loading vector store")
    vector_store = Chroma(persist_directory=vector_store_directory, embedding_function=embedding)

    print("Creating chain")
    retriever = vector_store.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={
            "k": 20,
            "score_threshold": 0.1,
        },
    )

    document_chain = create_stuff_documents_chain(cached_llm, raw_prompt)
    chain = create_retrieval_chain(retriever, document_chain)

    result = chain.invoke({"input": query})

    print(result)

    sources = []
    for doc in result["context"]:
        sources.append(
            {"source": doc.metadata["source"], "page_content": doc.page_content}
        )

    response_answer = {"answer": result["answer"], "sources": sources}
    return response_answer

@app.route("/ask_csv", methods=["POST"])
def askCSVPost():
    print("Post /ask_csv called")
    json_content = request.json
    query = json_content.get("query")
    unique_id = json_content.get("unique_id")

    print(f"query: {query}")

    # Load the CSV file
    csv_file_path = os.path.join(csv_directory, unique_id + ".csv")
    if not os.path.exists(csv_file_path):
        return jsonify({"error": "CSV file not found"}), 404

    df = pd.read_csv(csv_file_path)

    # Initialize LocalLLM with Meta Llama 3 model
    llm = LocalLLM(
        api_base="http://localhost:11434/v1",
        model="llama3"
    )

    # Initialize SmartDataframe with DataFrame and LLM configuration
    pandas_ai = SmartDataframe(df, config={"llm": llm})

    # Chat with the DataFrame using the provided query
    result = pandas_ai.chat(query)

    response_answer = {"answer": result}
    return response_answer

@app.route("/pdf", methods=["POST"])
def pdfPost():
    file = request.files["file"]
    file_name = file.filename
    save_file = os.path.join(pdf_directory, file_name)

    os.makedirs(pdf_directory, exist_ok=True)
    
    file.save(save_file)
    print(f"filename: {file_name}")

    loader = PDFPlumberLoader(save_file)
    docs = loader.load_and_split()
    print(f"docs len={len(docs)}")

    chunks = text_splitter.split_documents(docs)
    print(f"chunks len={len(chunks)}")

    unique_id = str(uuid.uuid4())
    vector_store_directory = os.path.join("db", unique_id)
    os.makedirs(vector_store_directory, exist_ok=True)

    vector_store = Chroma.from_documents(
        documents=chunks, embedding=embedding, persist_directory=vector_store_directory
    )

    vector_store.persist()

    response = {
        "status": "Successfully Uploaded",
        "filename": file_name,
        "doc_len": len(docs),
        "chunks": len(chunks),
        "unique_id": unique_id
    }
    return response

@app.route("/csv", methods=["POST"])
def csvPost():
    file = request.files["file"]
    file_name = file.filename
    save_file = os.path.join(csv_directory, file_name)

    os.makedirs(csv_directory, exist_ok=True)
    
    file.save(save_file)
    print(f"filename: {file_name}")

    unique_id = str(uuid.uuid4())
    os.rename(save_file, os.path.join(csv_directory, unique_id + ".csv"))

    response = {
        "status": "Successfully Uploaded",
        "filename": file_name,
        "unique_id": unique_id
    }
    return response

def start_app():
    app.run(host="0.0.0.0", port=8080, debug=True)

if __name__ == "__main__":
    start_app()
