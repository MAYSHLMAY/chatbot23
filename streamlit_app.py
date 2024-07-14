import streamlit as st
import replicate
import os
import json
import re

# Set page configuration
st.set_page_config(
    page_title="My ChatBot",
    layout="centered",
    initial_sidebar_state="expanded",
)

# Function to clear chat history
def clear_chat_history():
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]
st.button('Clear Chat History', on_click=clear_chat_history)

# Include JavaScript code to listen for postMessage events
st.components.v1.html(f"""
  <script>
    console.log("received")
    console.log(window.parent.localStorage.getItem("currentUser"))
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

# Retrieve the currentUser data from query params
query_params = st.experimental_get_query_params()
current_user = query_params.get('user', [None])[0]

# Display greeting based on user login status
if current_user:
    st.write(f"Hello, {current_user}!")
else:
    st.write("User not logged in.")

# Load FAQs from JSON file
faq_file_path = os.path.join(os.path.dirname(__file__), 'faqs.json')

try:
    with open(faq_file_path, 'r') as f:
        faqs = json.load(f)
except FileNotFoundError:
    st.error(f"FAQ file not found at path: {faq_file_path}")
    faqs = {}

# Function to get FAQ response based on prompt
def get_faq_response(prompt):
    for question, answer in faqs.items():
        # Using regex to match variations of the question
        pattern = re.compile(re.escape(prompt), re.IGNORECASE)
        if pattern.search(question):
            return answer
    return None

# Function to generate response using Replicate model
def generate_llama2_response(prompt_input):
    # Replace with your code to interact with the Replicate model
    # This is a placeholder
    return ["Generated response from Replicate model"]

# Store LLM generated responses in session state
if "messages" not in st.session_state.keys():
    st.session_state.messages = [{"role": "assistant", "content": "How may Blog BLAST assist you today?"}]

# Display or clear chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# User-provided prompt
prompt = st.text_input("Enter your query:")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})

# Generate a new response if last message is not from assistant
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # Check if prompt matches any FAQ
            faq_response = get_faq_response(prompt)
            if faq_response:
                response = [faq_response]
            else:
                response = generate_llama2_response(prompt)
            
            # Display the response in the chat interface
            placeholder = st.empty()
            full_response = ''
            for item in response:
                full_response += item
                placeholder.markdown(full_response)
            placeholder.markdown(full_response)

    # Append the assistant's response to session state
    message = {"role": "assistant", "content": full_response}
    st.session_state.messages.append(message)
