from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from datetime import datetime
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, EqualTo
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
socketio = SocketIO(app, cors_allowed_origins="*")

# =========================
# DATABASE MODEL
# =========================
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(20), default="mentee")  # NEW

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# =========================
# FORMS
# =========================
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=150)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[EqualTo('password')])
    role = SelectField('Role', choices=[('mentee', 'Mentee'), ('mentor', 'Mentor')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

# =========================
# TEMP STORAGE
# =========================
messages = []
doubts = []

# =========================
# AUTH ROUTES
# =========================
@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)

        user = User(
            username=form.username.data,
            password=hashed_password,
            role=form.role.data
        )

        db.session.add(user)
        db.session.commit()

        flash('Account created! Login now.', 'success')
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
            flash('Invalid credentials', 'danger')

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
        return jsonify({"error": "Empty message"}), 400

    msg = {
        "sender": current_user.username,
        "role": current_user.role,
        "text": text,
        "time": datetime.now().strftime("%H:%M")
    }

    messages.append(msg)

    socketio.emit("new_message", msg)
    return jsonify({"status": "sent"})

@app.route("/messages")
@login_required
def get_messages():
    return jsonify(messages)

@app.route("/clear", methods=["POST"])
@login_required
def clear_chat():
    global messages
    messages = []
    return jsonify({"status": "cleared"})

# Typing feature
@socketio.on("typing")
def handle_typing(data):
    emit("typing", data, broadcast=True, include_self=False)

# =========================
# DOUBT SYSTEM
# =========================
@app.route("/raise_doubt", methods=["POST"])
@login_required
def raise_doubt():
    data = request.json

    question = data.get("question")
    title = data.get("title", "General")

    doubt = {
        "id": len(doubts) + 1,
        "mentee": current_user.username,
        "title": title,
        "question": question,
        "answer": None,
        "status": "pending",
        "time": datetime.now().strftime("%H:%M")
    }

    doubts.append(doubt)
    return jsonify({"status": "submitted"})

@app.route("/doubts")
@login_required
def get_doubts():
    return jsonify(doubts)

@app.route("/answer_doubt", methods=["POST"])
@login_required
def answer_doubt():
    if current_user.role != "mentor":
        return jsonify({"error": "Only mentors can answer"}), 403

    data = request.json
    id = data.get("id")
    answer = data.get("answer")

    for d in doubts:
        if d["id"] == id:
            d["answer"] = answer
            d["status"] = "answered"
            return jsonify({"status": "answered"})

    return jsonify({"error": "not found"}), 404

@app.route("/resolve_doubt", methods=["POST"])
@login_required
def resolve_doubt():
    data = request.json
    id = data.get("id")

    for d in doubts:
        if d["id"] == id:
            d["status"] = "resolved"
            return jsonify({"status": "resolved"})

    return jsonify({"error": "not found"}), 404

# =========================
# RUN
# =========================
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True)