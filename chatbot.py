import streamlit as st
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="Custom ChatGPT", page_icon="🤖")

st.title("Custom ChatGPT")

# API endpoints
upload_pdf_url = "http://localhost:8080/pdf"
upload_csv_url = "http://localhost:8080/csv"
ask_pdf_url = "http://localhost:8080/ask_pdf"
ask_csv_url = "http://localhost:8080/ask_csv"

# Initialize session state to keep track of conversation history and unique ID
if "conversation" not in st.session_state:
    st.session_state.conversation = []
if "unique_id" not in st.session_state:
    st.session_state.unique_id = None
if "file_type" not in st.session_state:
    st.session_state.file_type = "PDF"
if "greeting" not in st.session_state:
    st.session_state.greeting = True

# Sidebar for file upload and conversation history
with st.sidebar:
    st.header("Upload File")
    
    # Dropdown for selecting file type
    file_type = st.selectbox("Choose file type", ["PDF", "CSV"])
    st.session_state.file_type = file_type
    
    # File uploader based on selected file type
    if file_type == "PDF":
        uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
        upload_url = upload_pdf_url
    else:
        uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
        upload_url = upload_csv_url

    if uploaded_file is not None:
        file_type_mime = 'application/pdf' if file_type == "PDF" else 'text/csv'
        files = {'file': (uploaded_file.name, uploaded_file, file_type_mime)}
        response = requests.post(upload_url, files=files)
        if response.status_code == 200:
            result = response.json()
            st.success(f"{file_type} uploaded successfully!")
            st.session_state.unique_id = result["unique_id"]
        else:
            st.error(f"Failed to upload {file_type}.")

    # Organize conversation history
    st.header("Conversation History")
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)

    def categorize_conversations(conversation):
        categorized = {"Today": [], "Yesterday": [], "Previous 7 Days": []}
        for chat in conversation:
            chat_time = chat["timestamp"].date()
            if chat_time == today:
                categorized["Today"].append(chat)
            elif chat_time == yesterday:
                categorized["Yesterday"].append(chat)
            elif today - timedelta(days=7) < chat_time < today:
                categorized["Previous 7 Days"].append(chat)
        return categorized

    categorized_conversation = categorize_conversations(st.session_state.conversation)

    if categorized_conversation["Today"]:
        st.subheader("Today")
        for idx, chat in enumerate(categorized_conversation["Today"]):
            with st.expander(f"Conversation {idx+1}"):
                st.write(f"**Q:** {chat['query']}")
                st.write(f"**A:** {chat['answer']}")
                st.write("---")

    if categorized_conversation["Yesterday"]:
        st.subheader("Yesterday")
        for idx, chat in enumerate(categorized_conversation["Yesterday"]):
            with st.expander(f"Conversation {idx+1}"):
                st.write(f"**Q:** {chat['query']}")
                st.write(f"**A:** {chat['answer']}")
                st.write("---")

    if categorized_conversation["Previous 7 Days"]:
        st.subheader("Previous 7 Days")
        for idx, chat in enumerate(categorized_conversation["Previous 7 Days"]):
            with st.expander(f"Conversation {idx+1}"):
                st.write(f"**Q:** {chat['query']}")
                st.write(f"**A:** {chat['answer']}")
                st.write("---")

# Chat interface
st.header("Ask a Question")

# Display greeting message
if st.session_state.greeting and uploaded_file is not None:
    with st.chat_message("assistant"):
        st.write("Hello! How can I assist you today?")
    st.session_state.greeting = False

# Display conversation history in main chat
for chat in st.session_state.conversation:
    with st.chat_message("user"):
        st.write(chat["query"])
    with st.chat_message("assistant"):
        st.write(chat["answer"])

# Input for user query
if st.session_state.unique_id:
    user_input = st.chat_input("What's your question?")
    if user_input:
        data = {"query": user_input, "unique_id": st.session_state.unique_id}
        ask_url = ask_pdf_url if st.session_state.file_type == "PDF" else ask_csv_url
        with st.spinner("Thinking..."):
            response = requests.post(ask_url, json=data)
            if response.status_code == 200:
                result = response.json()
                answer = result.get("answer", "No answer found.")
                sources = result.get("sources", [])

                # Update conversation history
                st.session_state.conversation.append({
                    "query": user_input,
                    "answer": answer,
                    "sources": sources,
                    "timestamp": datetime.now()
                })

                # Display the new message
                with st.chat_message("user"):
                    st.write(user_input)
                with st.chat_message("assistant"):
                    st.write(answer)
            else:
                st.error("Failed to get an answer.")
else:
    st.warning("Please upload a PDF or CSV first.")
