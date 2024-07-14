import streamlit as st
import os
import json
import replicate

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

# Include the JavaScript code to listen for postMessage events
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

# Load FAQs from JSON file
def load_faqs(file_path):
    try:
        with open(file_path, 'r') as f:
            faqs = json.load(f)
        return faqs
    except FileNotFoundError:
        st.error(f"FAQ file not found at path: {file_path}")
        return {}

# Function to find best matching answer from FAQs
def get_faq_response(prompt):
    for question, answer in faqs.items():
        if prompt.lower() in question.lower():
            return answer
    return None

# Initialize Streamlit session state for chat messages
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "How may Blog BLAST assist you today?"}]

# Display chat messages
for message in st.session_state.messages:
    with st.expander(message["role"]):
        st.write(message["content"])

# User input and response generation
user_input = st.text_input("Ask a question:")

if st.button("Submit") and user_input:
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Check for FAQ response
    faq_response = get_faq_response(user_input)
    if faq_response:
        st.session_state.messages.append({"role": "assistant", "content": faq_response})
    else:
        # Generate response using LLaMA2 model via Replicate API
        with st.spinner("Thinking..."):
            response = replicate.run(
                model="a16z-infra/llama7b-v2-chat:4f0a4744c7295c024a1de15e1a63c880d3da035fa1f49bfd344fe076074c8eea",
                input={"prompt": user_input, "temperature": 0.7, "max_length": 150}
            )
            st.session_state.messages.append({"role": "assistant", "content": response})

# Replicate Credentials setup
with st.sidebar:
    if 'REPLICATE_API_TOKEN' in st.secrets:
        replicate_api = st.secrets['REPLICATE_API_TOKEN']
    else:
        replicate_api = st.text_input('Enter Replicate API token:', type='password')
        if not (replicate_api.startswith('r8_') and len(replicate_api) == 40):
            st.warning('Please enter your credentials!', icon='⚠️')
        else:
            st.success('Proceed to entering your prompt message!', icon='👉')
    os.environ['REPLICATE_API_TOKEN'] = replicate_api

# Load FAQs
file_path = 'faqs.json'
faqs = load_faqs(file_path)

# Display current user greeting or indication
query_params = st.experimental_get_query_params()
current_user = query_params.get('user', [None])[0]
if current_user:
    st.write(f"Hello, {current_user}!")
else:
    st.write("User not logged in.")
