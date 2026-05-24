# 🎓 EduBot AI — Advanced AI Student Mentor Platform

A full-stack Django application with Groq LLM integration for AI-powered academic mentoring, mock interviews, progress tracking, and more.

---

## 🚀 Features

| Feature | Description |
|---|---|
| 🤖 **AI Academic Chatbot** | Groq-powered mentor that answers any academic question |
| 🎤 **Mock Interview** | Avatar-based AI interviewer with camera support + TTS |
| ⭐ **Answer Evaluation** | Scores 0–10 with strengths, weaknesses, tips |
| 📊 **Progress Tracking** | XP system, levels, streaks, skill charts |
| 🔔 **Smart Reminders** | Priority reminders with repeat options |
| 💡 **AI Suggestions** | Personalized study plans & skill recommendations |
| 👨‍💼 **Admin Dashboard** | Manage students, view analytics, post announcements |
| 🏆 **Gamification** | XP, levels (Novice → Master), streaks |

---

## 📋 Requirements

- Python 3.10+
- Django 4.2+
- Groq API Key (free at https://console.groq.com)

---

## ⚡ Quick Setup

### 1. Install dependencies
```bash
pip install django pillow
```

### 2. Set your Groq API Key
Open `ai_mentor/settings.py` and update:
```python
GROQ_API_KEY = 'your-groq-api-key-here'
```
Or set environment variable:
```bash
export GROQ_API_KEY=your-key-here
```

### 3. Run migrations
```bash
cd ai_student_mentor
python manage.py makemigrations core
python manage.py migrate
```

### 4. Create admin superuser
```bash
python manage.py createsuperuser
# Enter: username, email, password
# Then visit /admin-dashboard/ after login to access admin panel
```

### 5. Start the server
```bash
python manage.py runserver
```

### 6. Open browser
- 🌐 Main site: http://127.0.0.1:8000
- 📝 Register as student: http://127.0.0.1:8000/register/
- 🔑 Login: http://127.0.0.1:8000/login/

---

## 🗂️ Project Structure

```
ai_student_mentor/
├── ai_mentor/              # Django project config
│   ├── settings.py         # ← Add your GROQ_API_KEY here
│   ├── urls.py
│   └── wsgi.py
├── core/                   # Main app
│   ├── models.py           # Database models
│   ├── views.py            # All views
│   ├── urls.py             # URL routing
│   ├── ai_services.py      # Groq API integration
│   └── admin.py
├── templates/              # All HTML templates
│   ├── base.html           # Sidebar layout
│   ├── landing.html        # Home page
│   ├── login.html
│   ├── register.html
│   ├── student/
│   │   ├── dashboard.html  # Student dashboard
│   │   ├── profile.html
│   │   └── suggestions.html
│   ├── chatbot/
│   │   └── chat.html       # AI chat interface
│   ├── interview/
│   │   ├── setup.html      # Interview configuration
│   │   ├── session.html    # ← Avatar interview (like screenshots!)
│   │   ├── list.html
│   │   └── result.html
│   ├── reminders/
│   │   └── reminders.html
│   ├── progress/
│   │   └── progress.html
│   └── admin_dash/
│       ├── dashboard.html
│       ├── students.html
│       ├── student_detail.html
│       └── analytics.html
├── manage.py
└── requirements.txt
```

---

## 🎭 Mock Interview — Avatar System

The interview session (`/interview/session/<id>/`) features:
- **SVG AI Avatar** — custom-drawn professional interviewer
- **Web Speech API** — AI reads questions aloud (Text-to-Speech)
- **Camera integration** — enable your webcam for realistic practice
- **Microphone recording** — speak your answers
- **Real-time evaluation** — Groq AI scores each answer instantly
- **7 questions** per interview with animated progress tracker
- **Evaluation modal** — shows score, strengths, weaknesses, tips after each answer

---

## 🔧 Getting Your Groq API Key

1. Visit https://console.groq.com
2. Sign up for free
3. Create an API key
4. Add it to `settings.py`:
   ```python
   GROQ_API_KEY = 'gsk_your_key_here'
   ```

---

## 👤 User Roles

### Student
- Register at `/register/`
- Access full dashboard, chat, interviews, reminders, progress

### Admin
- Create via `python manage.py createsuperuser`
- Set `is_staff=True`
- Access admin dashboard at `/admin-dashboard/`
- View all students, analytics, post announcements

---

## 🎨 Design

- **Dark theme** with purple/teal gradient accents
- **Font Awesome 6.5** icons throughout
- **Space Grotesk** + **Syne** fonts
- **Chart.js** for progress charts
- **CSS animations** for smooth interactions
- Fully responsive design

---

## 📦 Tech Stack

| Technology | Purpose |
|---|---|
| Django 4.2 | Web framework |
| SQLite | Database (can switch to PostgreSQL) |
| Groq (llama3-70b) | AI/LLM backend |
| Chart.js | Analytics charts |
| Font Awesome 6.5 | Icons |
| Web Speech API | Text-to-speech & microphone |
| CSS3 / Vanilla JS | Frontend |

---

## 🚀 Production Tips

1. Change `SECRET_KEY` in settings.py
2. Set `DEBUG = False`
3. Use PostgreSQL instead of SQLite
4. Set `ALLOWED_HOSTS` to your domain
5. Use environment variables for secrets
6. Run `python manage.py collectstatic`

---

*Built with ❤️ using Django + Groq LLM*
