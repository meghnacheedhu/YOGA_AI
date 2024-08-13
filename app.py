from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import pandas as pd
import string
import requests
import openai
from openai import OpenAI
import json  # Add this import
import os
from langchain.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain.chains import (
    ConversationalRetrievalChain
)
from langchain_core.runnables.history import RunnableWithMessageHistory
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

# PROMPT = PromptTemplate(
#     template=template, input_variables=["context", "question", "history"]
# )

conversation = [
    {
        "role": "system",
        "content": "You are a helpful and knowledgeable yoga instructor."
    }
]

index_name = 'yogi-index'
store = {}

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
def get_gpt_response_finetuned(user_input):
    prompt = "you are a yoga instructor. use these 5 yoga poses to create a yoga flow "
    fake_user_input = prompt +  "1. child pose 2. downward dog 3. warrior 1 4. warrior 2 5. warrior 3 "

    message = {
        "role": "user",
        "content": fake_user_input
    }
    
    conversation.append(message)
    
    response = openai.chat.completions.create(
        messages=conversation,
        model="ft:gpt-3.5-turbo-1106:personal:yogabot:9sCLNZ7V",
        #model="gpt-3.5-turbo",
    )
    
    conversation.append(response.choices[0].message)
    
    return response.choices[0].message.content

def get_final_response(user_input):
    global allMessages
    allMessages.pop(0)
    message = {
        "role":"user",
        "content": user_input,
    }
    allMessages.append(message)
    allMessages.append({"role":"system", "content":"you are yoga instructor. Create a list of 5 yoga poses that will help the user with their physical pains and aches. the format should be 1. 'pose 1' 2. 'pose 2' ... Only provide a list of yoga poses."})

    response = openai.chat.completions.create(
        messages=allMessages,
        model="gpt-4",
    )
    output = response.choices[0].message
    allMessages.append(output)
    print('*' * 50)
    print(output.content)

    return get_gpt_response_finetuned(output.content)

# def get_final_response(user_input):
#     allMessages.pop(0)
#     chat_history = allMessages
#     question = user_input
#     system_template = """Use the following pieces of context to create a list of 5 yoga poses that will help the user in the format 1. 'pose' 2. 'pose 2' ...
#         ----------------
#         {context}
#         {question}
#         {chat_history}
#           """
#     messages = []
#     #convert all messages to the correct format
#     messages.append(SystemMessagePromptTemplate.from_template(system_template))
#     messages.append(HumanMessagePromptTemplate.from_template(user_input))
#     qa_prompt = ChatPromptTemplate.from_messages(messages)
#     try:
#         qa = ConversationalRetrievalChain.from_llm(


#             llm=llm, 
#             chain_type="stuff",
#             retriever=vectorstore.as_retriever(),
#             combine_docs_chain_kwargs={"prompt": qa_prompt}
#         )
#     except Exception as e:
#         print(f"Error creating LLM: {e}")
#         return "Sorry, I'm having trouble processing your request right now."   
#     print('****************')
#     print(qa)
#     pinecone_result = qa.invoke(user_input)['result'] 
#     print(pinecone_result)
#     return get_gpt_response_faizaan(pinecone_result)


def get_gpt_response_chat(user_input):
    global allMessages
    print(allMessages)
    message = {
        "role":"user",
        "content": user_input,
    }
    allMessages.append(message)
    response = openai.chat.completions.create(
        messages=allMessages,
        model="gpt-4",
    )
    output = response.choices[0].message
    allMessages.append(output)
    print(output.content)

    return output.content

##Below is the endpoints
@app.route('/')
def home():
    return render_template('index.html')

allMessages = []
allMessages.append({"role":"system", "content":"using information from the chat and from the user try to ask 1 question to get an idea of what type of physical pains and aches a user has. we want to create a list of yoga poses"})
count = 0

@app.route('/chat', methods=['POST'])
def chat():
    global count
    count = count + 1
    print(count)
    user_input = request.get_json().get('user_input', '')
    print(f"User Input: {user_input}")  
    if count < 3:
        response = get_gpt_response_chat(user_input)
    else:
        response = get_final_response(user_input)
        print(response)
    print(f"Bot Response: {response}")  
    return jsonify({'response': response})

if __name__ == "__main__":
    app.run(debug=True)

