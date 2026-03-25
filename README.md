# 🚀 Mentor-Mentee Communication Platform

A full-stack web application designed to streamline communication between mentors and mentees with real-time chat, doubt resolution, and role-based interactions.

---

## 🌟 Features

### 👤 Authentication & Roles
- Secure user authentication (Login/Signup)
- Role-based system:
  - 👨‍🏫 Mentor
  - 🎓 Mentee

### 💬 Real-Time Chat
- One-to-one communication
- Built using **Flask-SocketIO**
- Typing indicator support

### ❓ Doubt System
- Mentees can post doubts
- Mentors can answer them
- Organized and role-controlled interaction

### 🔐 Security
- Protected routes using `login_required`
- User session management

---

## 🛠️ Tech Stack

- **Backend:** Flask, Flask-SocketIO
- **Database:** SQLite (SQLAlchemy ORM)
- **Frontend:** HTML, CSS, JavaScript
- **Other:** Jinja2 Templates

---

## ⚙️ Installation & Setup

### 1️⃣ Clone the repository

```bash
git clone https://github.com/your-username/mentor-mentee-communication.git
cd mentor-mentee-communication
