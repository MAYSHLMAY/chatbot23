import streamlit as st
import replicate
import os

st.set_page_config(
    page_title="Blog Generator",
    layout="centered",
    initial_sidebar_state="expanded",
)

# Clear API token from environment
def clear_api_token():
    st.session_state.replicate_api_token = ""

st.sidebar.button('Clear API Token', on_click=clear_api_token)

st.markdown("<h3 style='text-align: center; font-size: 3em;'>Blog Generator</h3>", unsafe_allow_html=True)

# Sidebar for Replicate credentials and model settings
with st.sidebar:
    if 'REPLICATE_API_TOKEN' in st.secrets:
        replicate_api_token = st.secrets['REPLICATE_API_TOKEN']
    else:
        replicate_api_token = st.text_input('Enter Replicate API token:', type='password')
        if not (replicate_api_token.startswith('r8_') and len(replicate_api_token) == 40):
            st.warning('Please enter a valid Replicate API token!', icon='⚠️')
        else:
            st.success('API token set. Enter your blog prompt below!', icon='👉')

    os.environ['REPLICATE_API_TOKEN'] = replicate_api_token

    # Model selection and parameters
    selected_model = st.selectbox('Select Model', ['Llama2-7B', 'Llama2-13B'])
    if selected_model == 'Llama2-7B':
        llm = 'a16z-infra/llama7b-v2-chat:4f0a4744c7295c024a1de15e1a63c880d3da035fa1f49bfd344fe076074c8eea'
    elif selected_model == 'Llama2-13B':
        llm = 'a16z-infra/llama13b-v2-chat:df7690f1994d94e96ad9d568eac121aecf50684a0b0963b25a41cc40061269e5'
    
    temperature = st.slider('Temperature', 0.0, 1.0, 0.7, 0.1)
    top_p = st.slider('Top P', 0.0, 1.0, 0.9, 0.1)
    max_length = st.slider('Max Length', 50, 1000, 300, 50)

# Function to generate blog post
def generate_blog_post(prompt_input):
    try:
        output = ""
        for event in replicate.stream(
            llm,
            input={
                "prompt": prompt_input,
                "temperature": temperature,
                "top_p": top_p,
                "max_length": max_length,
                "min_new_tokens": -1
            },
        ):
            output += str(event)
        
        return output.strip()
    
    except Exception as e:
        st.error(f"Error: {e}")
        return None

# User-provided prompt
user_prompt = st.text_area("Enter the prompt for the blog post:", "Write a blog post about the impact of AI on modern education.")

if st.button("Generate Blog Post"):
    if replicate_api_token:
        with st.spinner("Generating blog post..."):
            blog_post = generate_blog_post(user_prompt)
            if blog_post:
                st.subheader("Generated Blog Post:")
                st.write(blog_post)
            else:
                st.error("Failed to generate blog post.")
    else:
        st.error("Please enter a valid Replicate API token in the sidebar.")
