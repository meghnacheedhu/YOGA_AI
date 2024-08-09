from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import pandas as pd
import string
import requests
import openai
import json  # Add this import
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  

# Initialize OpenAI API
openai.api_key = 'sk-proj-8a9w7OBzK7UIcZE2jG0KT3BlbkFJ0GyTixefesS24uAJqpyK'

# Load and process data
url = "https://pocketyoga.com/poses.json"
response = requests.get(url)
if response.status_code == 200:
    data = response.json()
    processed_data = []
    for pose in data:
        pose_data = {
            'Display Name': pose.get('display_name', 'N/A'),
            'Name': pose.get('name', 'N/A'),
            'Category': pose.get('category', 'N/A'),
            'Sub Category': pose.get('subcategory', 'N/A'),
            'Difficulty': pose.get('difficulty', 'N/A'),
            'Benefits': pose.get('benefits', 'N/A'),
            'Description': pose.get('description', 'N/A'),
            'Preferred Side': pose.get('preferred_side', 'N/A'),
        }
        processed_data.append(pose_data)
    df = pd.DataFrame(processed_data)
    df_cleaned = df.dropna()
    keywords = {
        'arms': 'arms',
        'hips': 'hips',
        'legs': 'legs',
        'hip': 'hip',
        'shoulders': 'shoulders',
        'pelvis': 'pelvis',
        'ankles': 'ankles',
        'core': 'core',
        'spine': 'spine',
        'rib cage': 'rib cage',
        'back': 'back',
        'hamstrings': 'hamstrings',
        'knees': 'knees',
        'thighs': 'thighs',
        'chest': 'chest',
        'neck': 'neck',
        'feet': 'feet',
        'calves': 'calves',
        'wrists': 'wrists',
        'hands': 'hands',
        'glutes': 'glutes'
    }
    def extract_keywords(benefits, keywords):
        if benefits is None:
            return None
        found_keywords = [muscle for muscle in keywords if muscle in benefits.lower()]
        return ', '.join(found_keywords) if found_keywords else None

    df_cleaned.loc[:, 'Body Part Strengthened'] = df_cleaned['Benefits'].apply(lambda x: extract_keywords(x, keywords))
    df = df_cleaned.dropna()
    df = df.apply(lambda x: x.str.lower().str.translate(str.maketrans('', '', string.punctuation)) if x.dtype == "object" else x)
else:
    print(f"Failed to retrieve the JSON data. Status code: {response.status_code}")

null_counts = df_cleaned.isnull().sum()
df = df_cleaned.dropna()
df = df.applymap(lambda x: x.lower().translate(str.maketrans('', '', string.punctuation))if isinstance(x, str) else x)

# Outputs the unique values in Category Column
unique_values = df['Category'].unique()

df_seated = df[df['Category'] == 'seated']
df_armlegsupport = df[df['Category'] == 'armlegsupport']
df_supine = df[df['Category'] == 'supine']
df_standing = df[df['Category'] == 'standing']
df_prone = df[df['Category'] == 'prone']
df_armbalanceandinversion = df[df['Category'] == 'armbalanceandinversion']

# Converts dfs into a json file
df_seated.to_json('Seated.json', orient='records', lines=True)
df_armlegsupport.to_json('Armlegsupport.json', orient='records', lines=True)
df_supine.to_json('Supine.json', orient='records', lines=True)
df_standing.to_json('Standing.json', orient='records', lines=True)
df_prone.to_json('Prone.json', orient='records', lines=True)
df_armbalanceandinversion.to_json('Armbalanceandinversion.json', orient='records', lines=True)

# Function to find errors in the JSON file
def inspect_json_file(json_file):
    try:
        with open(json_file, 'r') as file:
            content = file.read()
            print(content)
            data = json.loads(content)  # Parses JSON file
            print(data)
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")

inspect_json_file('Seated.json')
inspect_json_file('Armlegsupport.json')
inspect_json_file('Supine.json')
inspect_json_file('Standing.json')
inspect_json_file('Prone.json')
inspect_json_file('Armbalanceandinversion.json')

# This function converts the JSON file into a readable format for md conversion
def load_multiple_json_objects(file_path):
    with open(file_path, 'r') as file:
        content = file.read()
        json_objects = content.splitlines()
        data = []
        for obj in json_objects:
            if obj.strip():
                try:
                    data.append(json.loads(obj))
                except json.JSONDecodeError as e:
                    print(f"Skipping invalid JSON object: {obj}\nError: {e}")
        return data

# This function converts JSON file into a Markdown file
def json_to_markdown_list(json_file, output_file):
    data = load_multiple_json_objects(json_file)
    base_name = os.path.basename(json_file)
    title = os.path.splitext(base_name)[0]

    with open(output_file, 'w') as file:
        file.write(f"{title} Poses\n\n")
        for item in data:
            file.write(f"Name: {item.get('Name', 'N/A')}\n")
            file.write(f"Category: {item.get('Category', 'N/A')}\n")
            file.write(f"Body Part Strengthened: {item.get('Body Part Strengthened', 'N/A')}\n\n")
            file.write(f"Difficulty: {item.get('Difficulty', 'N/A')}\n\n")
            file.write(f"Benefits: {item.get('Benefits', 'N/A')}\n\n")
            file.write(f"Description: {item.get('Description', 'N/A')}\n\n")
            file.write(f"Next Position: {item.get('Next Position', 'N/A')}\n\n")

# Applies function to 'yoga_poses_cleaned.json' file and outputs as 'yoga_poses_list.md'
json_to_markdown_list('Seated.json', 'df_seated.md')
json_to_markdown_list('Armlegsupport.json', 'df_armlegsupport.md')
json_to_markdown_list('Supine.json', 'df_supine.md')
json_to_markdown_list('Standing.json', 'df_standing.md')
json_to_markdown_list('Prone.json', 'df_prone.md')
json_to_markdown_list('Armbalanceandinversion.json', 'df_armbalanceandinversion.md')

# Fetch data from DataFrame
def fetch_data_from_df(user_input):
    relevant_poses = []
    for _, row in df.iterrows():
        if "beginner" in user_input.lower() and row['Difficulty'].lower() != "beginner":
            continue
        if "intermediate" in user_input.lower() and row['Difficulty'].lower() != "intermediate":
            continue
        if "expert" in user_input.lower() and row['Difficulty'].lower() != "expert":
            continue
        if "flexibility" in user_input.lower() and "flexibility" not in row['Benefits'].lower():
            continue
        relevant_poses.append({'Name': row['Name']})
    return relevant_poses

# Get response from OpenAI API
def get_gpt_response(user_input):
    messages = [
        {"role": "system", "content": "You are a helpful and knowledgeable yoga instructor."},
        {"role": "user", "content": user_input}
    ]
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        print(response)
        return response['choices'][0]['message']['content']
    except Exception as e:
        print(f"Error communicating with OpenAI: {e}")
        return "Sorry, I'm having trouble processing your request right now."

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.get_json().get('user_input', '')
    print(f"User Input: {user_input}")  
    response = get_gpt_response(user_input)
    print(f"Bot Response: {response}")  
    return jsonify({'response': response})

if __name__ == "__main__":
    app.run(debug=True)

