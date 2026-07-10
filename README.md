# 🏋️ Fitness Buddy — AI-Powered Indian Fitness Coach

> An intelligent fitness web application powered by **IBM watsonx.ai (Granite)** that provides personalized Indian workout plans, meal plans, BMI/BMR/TDEE calculators, and 24/7 AI coaching.

---

## 📸 Features

| Feature | Description |
|---|---|
| 🤖 AI Fitness Coach | IBM Granite-powered chatbot with ChatGPT-style interface |
| 🏋️ Workout Planner | Home & gym workouts, HIIT, yoga, cardio, stretching |
| 🍛 Indian Meal Plans | Veg, non-veg, vegan, Jain, high-protein, weight-loss |
| 📊 Dashboard | Charts for weight progress, calories, streaks |
| 💧 Water Tracker | Daily intake tracker with animated ring |
| ⚖️ BMI Calculator | With BMI scale and category display |
| 🔥 BMR / TDEE | Mifflin-St Jeor formula + activity multiplier |
| 🥗 Macro Calculator | Protein/carbs/fat with doughnut chart |
| 💊 Water Calculator | Body weight + activity + climate based |
| 🌙 Dark / Light Mode | Smooth theme switching with persistence |
| 📱 Responsive Design | Mobile-first Bootstrap 5 layout |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- IBM Cloud account with watsonx.ai access

### Installation

```bash
# 1. Enter project folder
cd fitness_buddy

# 2. Install dependencies (system Python — no venv needed)
pip install -r requirements.txt

# 3. Configure environment
copy .env.example .env         # Windows
# cp .env.example .env         # macOS / Linux
# Then edit .env with your IBM API key and project ID

# 4. Run the application
python app.py
```

Visit: **http://localhost:5000**

> **Windows PowerShell note:** if you prefer a virtual environment but get a script execution policy error, use one of these alternatives:
> ```powershell
> # Option A — bypass once
> Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
> python -m venv venv
> venv\Scripts\activate
>
> # Option B — use cmd.exe instead of PowerShell
> cmd /c "venv\Scripts\activate && python app.py"
>
> # Option C — skip venv entirely (works fine)
> pip install -r requirements.txt
> python app.py
> ```

---

## 🔑 Environment Configuration

Copy `.env.example` to `.env` and fill in your credentials:

```env
SECRET_KEY=your-super-secret-flask-key
IBM_API_KEY=your-ibm-cloud-api-key
IBM_PROJECT_ID=your-watsonx-project-id
IBM_WATSONX_URL=https://us-south.ml.cloud.ibm.com
IBM_GRANITE_MODEL_ID=ibm/granite-13b-chat-v2
```

### Compatible Python Version

This app requires **Python 3.10 – 3.12**. Python 3.13 may cause build errors with some IBM SDK dependencies. If you have Python 3.13, the core Flask app still works — only the live IBM AI responses require the IBM SDK.

### Getting IBM watsonx.ai Credentials

1. Sign up at [https://cloud.ibm.com](https://cloud.ibm.com)
2. Create a **watsonx.ai** service instance
3. Go to **Manage → Access → API keys** → Create API key
4. Open watsonx.ai Studio → Get your **Project ID** from project settings
5. Paste both values into your `.env` file

---

## 🧠 Customizing the AI Agent

All AI behavior is configured in **`agent_config.py`** — edit ONLY this file:

```python
# Change the AI's name and personality
PERSONA = {
    "name": "FitGuru",
    "tone": "Friendly, encouraging, professional",
}

# Change fitness specializations
SPECIALIZATION = {
    "primary_focus": ["Weight loss", "Muscle building", ...]
}

# Modify Indian food database
DIET_PREFERENCES = {
    "staple_foods": {
        "proteins": ["Dal", "Paneer", "Eggs", ...]
    }
}

# Adjust workout programming
WORKOUT_STYLE = {
    "default_intensity": "Moderate",
    "progression_model": "Progressive overload"
}

# Tune LLM parameters
GENERATION_PARAMS = {
    "temperature": 0.7,
    "max_new_tokens": 2048,
}
```

---

## 📁 Project Structure

```
fitness_buddy/
├── app.py                  # Flask app factory
├── config.py               # Configuration (loads .env)
├── models.py               # SQLAlchemy database models
├── agent_config.py         # ⭐ AI Agent Instructions (customize here!)
├── watsonx_client.py       # IBM watsonx.ai integration
├── requirements.txt
├── .env.example
│
├── routes/
│   ├── auth.py             # Login, Register, Logout
│   ├── dashboard.py        # Dashboard & stats
│   ├── chat.py             # AI chat sessions
│   ├── workout.py          # Workout logging & planner
│   ├── nutrition.py        # Meal tracking
│   ├── calculators.py      # BMI, BMR, TDEE, Water, Macros
│   ├── profile.py          # User profile management
│   └── api.py              # REST API endpoints
│
├── templates/
│   ├── base.html           # Base layout (navbar, sidebar)
│   ├── auth/               # Login & Register pages
│   ├── dashboard/          # Main dashboard with charts
│   ├── chat/               # ChatGPT-style AI interface
│   ├── workout/            # Workout planner & history
│   ├── nutrition/          # Meal tracker
│   ├── calculators/        # All fitness calculators
│   └── profile/            # Profile setup & edit
│
└── static/
    ├── css/style.css       # Custom styles (glassmorphism, dark mode)
    └── js/app.js           # Chat, charts, calculators JS
```

---

## 🗄️ Database Models

| Model | Description |
|---|---|
| `User` | Authentication (username, email, password_hash) |
| `UserProfile` | BMI/BMR, goals, diet, medical conditions |
| `ChatSession` | Groups chat messages into conversations |
| `ChatMessage` | Individual AI/user messages |
| `WorkoutLog` | Logged workout sessions |
| `WorkoutPlan` | AI-generated workout plans |
| `MealLog` | Daily meal tracking with macros |
| `WeightLog` | Body weight history for progress charts |
| `WaterLog` | Daily water intake tracking |

---

## 🌐 API Endpoints

| Method | Route | Description |
|---|---|---|
| `POST` | `/chat/send` | Send message to AI coach |
| `GET` | `/chat/session/<id>` | Load chat history |
| `POST` | `/api/water/add` | Log water intake |
| `GET` | `/api/stats/summary` | Dashboard stats |
| `GET` | `/api/progress/weight` | Weight history |
| `POST` | `/calculators/bmi` | Calculate BMI |
| `POST` | `/calculators/bmr` | Calculate BMR |
| `POST` | `/calculators/tdee` | Calculate TDEE |
| `POST` | `/calculators/water` | Calculate water intake |
| `POST` | `/calculators/macros` | Calculate macronutrients |
| `POST` | `/workout/log` | Log a workout |
| `POST` | `/nutrition/log` | Log a meal |
| `POST` | `/profile/weight/log` | Log body weight |

---

## 🚢 Deployment

### Production with Gunicorn

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app()"
```

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
ENV FLASK_ENV=production
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:create_app()"]
```

```bash
docker build -t fitness-buddy .
docker run -p 8000:8000 --env-file .env fitness-buddy
```

### Environment Variables for Production

```env
FLASK_ENV=production
SECRET_KEY=<long-random-string>
DATABASE_URL=postgresql://user:pass@host/dbname
IBM_API_KEY=<your-key>
IBM_PROJECT_ID=<your-project>
```

---

## 🔒 Security

- Passwords hashed with **bcrypt** (Flask-Bcrypt)
- Sessions secured with **Flask-Login** + secret key
- API keys stored in `.env` — never committed to git
- `.env` is in `.gitignore`
- SQL injection prevented via **SQLAlchemy ORM**
- Input validation on all forms and API endpoints

---

## 🤖 AI Safety

The AI strictly follows these rules (configurable in `agent_config.py`):

✅ Always recommends consulting doctors for medical conditions  
✅ Never diagnoses diseases  
✅ Never prescribes medications or steroids  
✅ Never promotes unsafe weight-loss methods  
✅ Always includes warm-up and cool-down  
✅ Includes medical disclaimer on health advice  

---

## 📝 Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.10+, Flask 3.0 |
| AI | IBM watsonx.ai (Granite 13B Chat) |
| Database | SQLite (dev) / PostgreSQL (prod) |
| ORM | SQLAlchemy + Flask-Migrate |
| Auth | Flask-Login + Flask-Bcrypt |
| Frontend | Bootstrap 5, Chart.js, Marked.js |
| Icons | Font Awesome 6 |
| Fonts | Inter + Poppins (Google Fonts) |

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

*Built with ❤️ for Indian fitness enthusiasts · Powered by IBM Granite AI*
