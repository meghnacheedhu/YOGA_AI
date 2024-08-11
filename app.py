from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import pandas as pd
import string
import requests
import openai
from openai import OpenAI
import json  # Add this import
import os
from langchain_openai import ChatOpenAI    
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate



app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  

# Initialize OpenAI API
openai.api_key = 'sk-proj-8a9w7OBzK7UIcZE2jG0KT3BlbkFJ0GyTixefesS24uAJqpyK'

## code carried over from chat project

template = open("prompt.txt", "r").read()
# final_template = open("final_prompt.txt", "r").read()

openai = OpenAI(api_key="sk-proj-nr7QgNS49pB81YgvSFQ2T3BlbkFJaKl0ZVAgZVBF6w1sJk1U")

PROMPT = PromptTemplate(
    template=template, input_variables=["context", "question", "history"]
)

conversation = [
    {
        "role": "system",
        "content": "You are a helpful and knowledgeable yoga instructor."
    }
]

index_name = 'yogi-index'

# os.environ['OPENAI_API_KEY'] = 'sk-proj-8a9w7OBzK7UIcZE2jG0KT3BlbkFJ0GyTixefesS24uAJqpyK'
os.environ['OPENAI_API_KEY'] = 'sk-proj-nr7QgNS49pB81YgvSFQ2T3BlbkFJaKl0ZVAgZVBF6w1sJk1U' #faizaasn
os.environ['PINECONE_API_KEY'] = 'afbc2bbb-86df-4e62-8e56-4fc2e2a5d765'

vectorstore = PineconeVectorStore.from_existing_index(
    index_name, 
    embedding=OpenAIEmbeddings()
)

llm = ChatOpenAI(
    model='gpt-4',
    temperature=0
)

llm_finetuning = ChatOpenAI(
    model='ft:gpt-3.5-turbo-1106:personal:yogabot:9sCLNZ7V',
    temperature=0
)
allMessages = []
allUserMessages = []

# openai = OpenAI(
#     api_key = 'sk-proj-8a9w7OBzK7UIcZE2jG0KT3BlbkFJ0GyTixefesS24uAJqpyK'
# )

def get_finetuning_response(user_input):
    message = {
        "role": "user",
        "content": user_input
    }
    
    conversation.append(message)
    
    response = openai.chat.completions.create(
        messages=conversation,
        model="ft:gpt-3.5-turbo-1106:personal:yogabot:9sCLNZ7V",
    )
    
    response_text = response.choices[0].message.content
    conversation.append({"role": "assistant", "content": response_text})
    
    # Delete the previous audio file if it exists
    audio_file = "output.mp3"
    if os.path.exists(audio_file):
        os.remove(audio_file)
    
    # Convert the response text to speech using OpenAI TTS
    tts_response = openai.audio.speech.create(
        model="tts-1",
        voice="shimmer",
        input=response_text,
    )
    
    # Stream the response to a file
    with open(audio_file, "wb") as f:
        f.write(tts_response.content)
    
    return response_text

# def get_final_response(user_input):
#     qa = RetrievalQA.from_chain_type(
#         llm=llm_finetuning, 
#         chain_type="stuff",
#         retriever=vectorstore.as_retriever(),
#         chain_type_kwargs={"prompt": PROMPT} 
#     )
#     return qa.invoke(user_input)['result'] 

def get_gpt_response(user_input):
    try:
        qa = RetrievalQA.from_chain_type(
            llm=llm, 
            chain_type="stuff",
            retriever=vectorstore.as_retriever(),
            chain_type_kwargs={"prompt": PROMPT} 
        )
    except Exception as e:
        print(f"Error creating LLM: {e}")
        return "Sorry, I'm having trouble processing your request right now."   
    return qa.invoke(user_input)['result'] 


##Below is the endpoints
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    print('it works here')
    user_input = request.get_json().get('user_input', '')
    print(f"User Input: {user_input}")  
    response = get_gpt_response(user_input)
    print(f"Bot Response: {response}")  
    return jsonify({'response': response})

if __name__ == "__main__":
    app.run(debug=True)

