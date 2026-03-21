from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from datetime import datetime
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this to a random secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
socketio = SocketIO(app, cors_allowed_origins="*")

# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Forms
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=150)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

# In-memory storage (temporary)
messages = []
doubts = []


@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('Login unsuccessful. Please check username and password.', 'danger')
    return render_template('login.html', form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route("/")
@login_required
def home():
    return render_template("index.html")


# =========================
# CHAT SYSTEM
# =========================

@app.route("/send", methods=["POST"])
@login_required
def send_message():
    data = request.json

    text = data.get("text")

    if not text:
        return jsonify({"error": "Invalid data"}), 400

    message = {
        "sender": current_user.username,
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
@login_required
def raise_doubt():
    data = request.json

    question = data.get("question")

    if not question:
        return jsonify({"error": "Invalid data"}), 400

    doubt = {
        "id": len(doubts) + 1,
        "mentee": current_user.username,
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
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True)