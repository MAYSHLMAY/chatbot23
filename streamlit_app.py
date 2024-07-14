import streamlit as st
import os
import json
from llamaindex import GPTSimpleVectorIndex

# Set Streamlit page configuration
st.set_page_config(
    page_title="My ChatBot",
    layout="centered",
    initial_sidebar_state="expanded",
)

# Function to clear chat history
def clear_chat_history():
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]
st.button('Clear Chat History', on_click=clear_chat_history)

# JavaScript to handle postMessage events
st.components.v1.html(f"""
  <script>
    window.addEventListener('message', (event) => {{
      console.log('Message received from origin:', event.origin);
      if (event.origin !== 'https://blog-blast.vercel.app') return; // Validate the origin

      const message = event.data;
      if (message.type === 'setUser') {{
        const userName = message.user;
        const params = new URLSearchParams(window.location.search);
        params.set('user', userName);
        const newUrl = `${{window.location.origin}}${{window.location.pathname}}?${{params.toString()}}`;
        window.history.replaceState(null, '', newUrl);
        setTimeout(() => window.location.reload(), 500); // Reload page to reflect changes
      }}
    }});
  </script>
""")

# Load FAQs from faqs.json
faq_file_path = os.path.join(os.path.dirname(__file__), 'faqs.json')

try:
    with open(faq_file_path, 'r') as f:
        faqs = json.load(f)
except FileNotFoundError:
    st.error(f"FAQ file not found at path: {faq_file_path}")
    faqs = {}

# Initialize LlamaIndex
index = GPTSimpleVectorIndex()

# Indexing FAQs into LlamaIndex
for question, answer in faqs.items():
    index.add_example(question, answer)

# Function to get response using LlamaIndex or FAQ
def generate_response(prompt):
    # Use LlamaIndex for dynamic response handling
    keywords = index.query_keyword_extract(prompt)
    expanded_queries = index.query_keyword_in_query(keywords)
    best_match = index.query_compare(expanded_queries)
    response = best_match.response

    # If no response from LlamaIndex, check FAQs
    if not response:
        for question, answer in faqs.items():
            if prompt.lower() in question.lower():
                response = answer
                break

    return response

# Retrieve currentUser data from query params
query_params = st.experimental_get_query_params()
current_user = query_params.get('user', [None])[0]

# Display currentUser greeting or indication if not logged in
if current_user:
    st.write(f"Hello, {current_user}!")
else:
    st.write("User not logged in.")

# Chat interface handling messages
if "messages" not in st.session_state.keys():
    st.session_state.messages = [{"role": "assistant", "content": "How may Blog BLAST assist you today?"}]

# Display or clear chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# User prompt input
if prompt := st.chat_input(disabled=False):
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Generate response
    with st.spinner("Thinking..."):
        response = generate_response(prompt)
        st.session_state.messages.append({"role": "assistant", "content": response})
