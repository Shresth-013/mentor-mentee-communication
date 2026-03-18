from flask import Flask, render_template, request, jsonify
from datetime import datetime

app = Flask(__name__)

# chat messages
messages = []

# doubts raised by mentees
doubts = []


@app.route("/")
def home():
    return render_template("index.html")


# send normal chat message
@app.route("/send", methods=["POST"])
def send_message():

    data = request.json

    sender = data["sender"]
    text = data["text"]

    message = {
        "sender": sender,
        "text": text,
        "time": datetime.now().strftime("%H:%M:%S")
    }

    messages.append(message)

    return jsonify({"status": "Message Sent"})


# get chat messages
@app.route("/messages")
def get_messages():
    return jsonify(messages)


# clear chat
@app.route("/clear", methods=["POST"])
def clear_chat():

    global messages
    messages = []

    return jsonify({"status": "Chat Cleared"})


# mentee raises doubt
@app.route("/raise_doubt", methods=["POST"])
def raise_doubt():

    data = request.json

    doubt = {
    "id": len(doubts) + 1,
    "mentee": data["mentee"],
    "question": data["question"],
    "answer": None,
    "status": "pending",
    "time": datetime.now().strftime("%H:%M:%S")
}

    doubts.append(doubt)

    return jsonify({"status": "Doubt Submitted"})


# mentor views doubts
@app.route("/doubts")
def get_doubts():
    return jsonify(doubts)


@app.route("/answer_doubt", methods=["POST"])
def answer_doubt():

    data = request.json
    doubt_id = data.get("id")
    answer = data.get("answer")

    for d in doubts:
        if d["id"] == doubt_id:
            d["answer"] = answer
            d["status"] = "answered"
            return jsonify({"status": "Answered"})

    return jsonify({"error": "Doubt not found"}), 404


@app.route("/resolve_doubt", methods=["POST"])
def resolve_doubt():

    data = request.json
    doubt_id = data.get("id")

    for d in doubts:
        if d["id"] == doubt_id:
            d["status"] = "resolved"
            return jsonify({"status": "Resolved"})

    return jsonify({"error": "Doubt not found"}), 404

if __name__ == "__main__":
    app.run(debug=True)