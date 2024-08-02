import streamlit as st
import replicate
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os
import json
import re

st.set_page_config(
    page_title="BlogBLAST Chatbot",
    layout="centered",
    initial_sidebar_state="expanded",
)

def clear_chat_history():
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]
st.button('Clear Chat History', on_click=clear_chat_history)

st.markdown("<h3 style='text-align: center; font-size: 3em;'>Blog BLAST Chat Bot</h3>", unsafe_allow_html=True)

# Load FAQs
faq_file_path = os.path.join(os.path.dirname(__file__), 'faqs.json')

try:
    with open(faq_file_path, 'r') as f:
        faqs = json.load(f)
except FileNotFoundError:
    st.error(f"FAQ file not found at path: {faq_file_path}")
    faqs = {}

# Prepare FAQ data
questions = list(faqs.keys())
answers = list(faqs.values())

# Initialize TF-IDF Vectorizer
vectorizer = TfidfVectorizer()

# Fit the vectorizer on the FAQ questions
tfidf_matrix = vectorizer.fit_transform(questions)

# Function to get FAQ response based on prompt
def get_faq_response(prompt):
    if not prompt:
        return None

    # Clean the prompt
    clean_prompt = re.sub(r'[^\w\s]', '', prompt.strip())
    
    # Transform the prompt into TF-IDF vector
    prompt_vector = vectorizer.transform([clean_prompt])

    # Compute cosine similarity between the prompt and FAQ questions
    similarities = cosine_similarity(prompt_vector, tfidf_matrix).flatten()

    # Get the index of the most similar FAQ question
    max_index = similarities.argmax()

    # If the similarity score is high enough, return the corresponding answer
    if similarities[max_index] > 0.1:  # Adjust the threshold as needed
        return answers[max_index]

    return None

# Replicate Credentials
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

    selected_model = 'Llama2-7B'
    if selected_model == 'Llama2-7B':
        llm = 'a16z-infra/llama7b-v2-chat:4f0a4744c7295c024a1de15e1a63c880d3da035fa1f49bfd344fe076074c8eea'
    elif selected_model == 'Llama2-13B':
        llm = 'a16z-infra/llama13b-v2-chat:df7690f1994d94e96ad9d568eac121aecf50684a0b0963b25a41cc40061269e5'
    temperature = 0.1
    top_p = 0.9
    max_length = 120

# Store LLM generated responses
if "messages" not in st.session_state.keys():
    st.session_state.messages = [{"role": "assistant", "content": "How Blog BLAST assist you today?"}]

# Display or clear chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Function for generating LLaMA2 response
def generate_llama2_response(prompt_input):
    string_dialogue = "You are a helpful assistant. You do not respond as 'User' or pretend to be 'User'. You only respond once as 'Assistant'."
    for dict_message in st.session_state.messages:
        if dict_message["role"] == "user":
            string_dialogue += "User: " + dict_message["content"] + "\n\n"
        else:
            string_dialogue += "Assistant: " + dict_message["content"] + "\n\n"
    output = replicate.run(llm, 
                           input={"prompt": f"{string_dialogue} {prompt_input} Assistant: ",
                                  "temperature":temperature, "top_p":top_p, "max_length":max_length, "repetition_penalty":1})
    return output

# User-provided prompt
if prompt := st.chat_input(disabled=not replicate_api):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

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
            placeholder = st.empty()
            full_response = ''
            for item in response:
                full_response += item
                placeholder.markdown(full_response)
            placeholder.markdown(full_response)
    message = {"role": "assistant", "content": full_response}
    st.session_state.messages.append(message)
