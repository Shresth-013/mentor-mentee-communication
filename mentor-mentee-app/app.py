from flask import Flask, render_template, request, jsonify
from datetime import datetime
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# In-memory storage (temporary)
messages = []
doubts = []


@app.route("/")
def home():
    return render_template("index.html")


# =========================
# CHAT SYSTEM
# =========================

@app.route("/send", methods=["POST"])
def send_message():
    data = request.json

    sender = data.get("sender")
    text = data.get("text")

    if not sender or not text:
        return jsonify({"error": "Invalid data"}), 400

    message = {
        "sender": sender,
        "text": text,
        "time": datetime.now().strftime("%H:%M:%S")
    }

    messages.append(message)

    # Emit real-time message
    socketio.emit("new_message", message)

    return jsonify({"status": "Message Sent"})


@socketio.on("connect")
def handle_connect():
    print("User connected")


@app.route("/messages")
def get_messages():
    return jsonify(messages)


@app.route("/clear", methods=["POST"])
def clear_chat():
    global messages
    messages = []

    return jsonify({"status": "Chat Cleared"})


# =========================
# DOUBT SYSTEM
# =========================

@app.route("/raise_doubt", methods=["POST"])
def raise_doubt():
    data = request.json

    mentee = data.get("mentee")
    question = data.get("question")

    if not mentee or not question:
        return jsonify({"error": "Invalid data"}), 400

    doubt = {
        "id": len(doubts) + 1,
        "mentee": mentee,
        "question": question,
        "answer": None,
        "status": "pending",
        "time": datetime.now().strftime("%H:%M:%S")
    }

    doubts.append(doubt)

    return jsonify({"status": "Doubt Submitted"})


@app.route("/doubts")
def get_doubts():
    return jsonify(doubts)


@app.route("/answer_doubt", methods=["POST"])
def answer_doubt():
    data = request.json

    doubt_id = data.get("id")
    answer = data.get("answer")

    if not doubt_id or not answer:
        return jsonify({"error": "Invalid data"}), 400

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

    if not doubt_id:
        return jsonify({"error": "Invalid data"}), 400

    for d in doubts:
        if d["id"] == doubt_id:
            d["status"] = "resolved"
            return jsonify({"status": "Resolved"})

    return jsonify({"error": "Doubt not found"}), 404


# =========================
# RUN APP
# =========================

if __name__ == "__main__":
    socketio.run(app, debug=True)