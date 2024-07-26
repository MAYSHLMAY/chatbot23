import streamlit as st
import os
import json
import re
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments, TextDataset, DataCollatorForLanguageModeling

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

# Function to get FAQ response based on prompt
def get_faq_response(prompt):
    if not prompt:
        return None
    
    clean_prompt = re.sub(r'[^\w\s]', '', prompt.strip())

    # First, try to find an exact match
    for question, answer in faqs.items():
        clean_question = re.sub(r'[^\w\s]', '', question.strip())
        if clean_prompt.lower() == clean_question.lower():
            return answer

    # If no exact match, look for keyword-based matching
    for question, answer in faqs.items():
        clean_question = re.sub(r'[^\w\s]', '', question.strip())
        pattern = re.compile(re.escape(clean_prompt), re.IGNORECASE)
        if pattern.search(clean_question):
            return answer
    
    return None

# Prepare training data from FAQs
def prepare_training_data(faqs):
    training_data = ""
    for question, answer in faqs.items():
        training_data += f"User: {question}\nAssistant: {answer}\n"
    with open('training_data.txt', 'w') as f:
        f.write(training_data)

prepare_training_data(faqs)

# Fine-tune the model
model_name = 'facebook/llama-7b'  # Change to the model you want to fine-tune
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

def fine_tune_model():
    training_args = TrainingArguments(
        output_dir='./results',
        overwrite_output_dir=True,
        num_train_epochs=1,  # Increase for better results
        per_device_train_batch_size=2,
        save_steps=10_000,
        save_total_limit=2,
        prediction_loss_only=True,
    )

    train_dataset = TextDataset(
        tokenizer=tokenizer,
        file_path="training_data.txt",
        block_size=128,
    )
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        data_collator=data_collator,
        train_dataset=train_dataset,
    )

    trainer.train()
    trainer.save_model("./fine_tuned_model")
    tokenizer.save_pretrained("./fine_tuned_model")

fine_tune_model()

# Load the fine-tuned model
model = AutoModelForCausalLM.from_pretrained('./fine_tuned_model')
tokenizer = AutoTokenizer.from_pretrained('./fine_tuned_model')

def generate_response(prompt):
    inputs = tokenizer(prompt, return_tensors="pt")
    outputs = model.generate(inputs.input_ids, max_length=150)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

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

# Store LLM generated responses
if "messages" not in st.session_state.keys():
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]

# Display or clear chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

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
                response = faq_response
            else:
                response = generate_response(prompt)
            st.markdown(response)
    message = {"role": "assistant", "content": response}
    st.session_state.messages.append(message)
