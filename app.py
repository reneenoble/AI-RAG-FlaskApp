from flask import Flask, render_template, request, jsonify
from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
import json


# Create a flask app
app = Flask(
  __name__,
  template_folder='templates',
  static_folder='static'
)

# Set up the client for AI Chat
client = AzureOpenAI(
    api_key=AOAI_KEY,
    api_version="2024-05-01-preview",
    azure_endpoint=AOAI_ENDPOINT,
)
# Set up clients for Cognitive Search and Storage
search_client = SearchClient(
    # endpoint=f"https://{AZURE_SEARCH_SERVICE}.search.windows.net",
    endpoint=AOAI_ENDPOINT,
    index_name=AZURE_SEARCH_INDEX,
    credential=AzureKeyCredential(AZURE_SEARCH_KEY),
)

def get_response(question, message_history[]):
    search_results = search_client.search(search_text=question)
    search_summary = " ".join(result["content"] for result in search_results)
    print(search_summary)
    SYSTEM_MESSAGE = "You're a helpful assistant that must use provided sources"

    # Create a new message history if there isn't one
    if not message_history:
        messages=[
            {"role": "system", "content": SYSTEM_MESSAGE},
            {"role": "user", "content": question + "\nSources: " + search_summary},
        ]
    # Otherwise, append the user's question to the message history
    else:
        messages = message_history + [
            {"role": "user", "content": question + "\nSources: " + search_summary},
        ]

    response = client.chat.completions.create(
        model=MODEL_NAME,
        temperature=0.7,
        n=1,
        messages=[
            {"role": "system", "content": SYSTEM_MESSAGE},
            {"role": "user", "content": question + "\nSources: " + search_summary},
        ],
    )
    return response.choices[0].message.content, messages


@app.route("/ask", methods=['GET'])
def ask():
    return """
    <h1>ASK AI A question!</h1>
    <form method="post" action="/ask">
        <textarea name="question" placeholder="Ask a question"></textarea>
        <button type="submit">Ask</button>
    </form>
    """


@app.route("/ask", methods=["POST"])
def ask_response():
    # Get the question out of the json object
    data = request.get_json()
    # Extract the 'messages' value from the JSON data
    question = data.get('question', "No question provided")
    response = get_response(question)
    return jsonify({"answer": response})


@app.route("/chat", methods=['GET'])
def chat():
    return """
    <h1>Chat with the AI</h1>
    <form method="post" action="/chat">
        <textarea name="question" placeholder="Ask a question"></textarea>
        <button type="submit">Ask</button>
    </form>
    """


@app.route("/chat", methods=["POST"])
def chat_response():
    # Get the question out of the json object
    data = request.get_json()
    # Extract the 'messages' value from the JSON data
    question = data.get('question', "No question provided")
    messages = data.get('messages', [])

    response = get_response(question, message_history=messages)
    return jsonify({"answer": response})


# create an index route
@app.route('/')
def home():
    return "Hello!"


@app.errorhandler(404)
def handle_404(e):
    return '<h1>404</h1><p>File not found!</p><img src="https://httpcats.com/404.jpg" alt="cat in box" width=400>', 404


if __name__ == '__main__':
  # Run the Flask app
  app.run(host='0.0.0.0', debug=True, port=8080)