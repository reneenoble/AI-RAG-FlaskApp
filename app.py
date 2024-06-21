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

def get_response(question, message_history=[]):
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
        messages=messages,
    )
    return response.choices[0].message.content, message_history.append({"role": "user", "content": question})


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
    answer, message_history = get_response(question)
    return jsonify({"answer": answer})


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
    message_history = data.get('messages', [])

    answer, message_history = get_response(question, message_history)
    return jsonify({"answer": answer, "messages": message_history})


# create an index route
@app.route('/')
def home():
    return "Hello!"
@app.get('/')
def index():
  return render_template('ask.html')

@app.get('/ask')
def ask():
    # return render_template('hello.html', name=request.args.get('name'))
  return render_template("ask.html")

@app.get('/chat')
def chat():
   return render_template('chat.html')

@app.route('/contextless-message', methods=['GET', 'POST'])
def contextless_message():
    msg = request.json['message']
    return {"resp": f"Contextless reply to {msg}"}


@app.route("/context-message", methods=["GET", "POST"])
def context_message():
    msg = request.json["message"]
    context = request.json["context"]

    reply = f"Context reply to {msg}"
    context.append(reply)
    return {"resp": reply, "context": context}


@app.errorhandler(404)
def handle_404(e):
    return '<h1>404</h1><p>File not found!</p><img src="https://httpcats.com/404.jpg" alt="cat in box" width=400>', 404


if __name__ == '__main__':
  # Run the Flask app
  app.run(host='0.0.0.0', debug=True, port=8080)
