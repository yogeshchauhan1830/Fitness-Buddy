"""
Fitness Buddy — Database Models
SQLAlchemy ORM models for all application data.
"""
from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_bcrypt import Bcrypt

db    = SQLAlchemy()
bcrypt = Bcrypt()


# ─────────────────────────────────────────────────────────────────────────────
# User Model
# ─────────────────────────────────────────────────────────────────────────────
class User(db.Model, UserMixin):
    __tablename__ = "users"

    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80),  unique=True, nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    last_login    = db.Column(db.DateTime)
    is_active     = db.Column(db.Boolean, default=True)

    # Relationships
    profile        = db.relationship("UserProfile",    back_populates="user", uselist=False, cascade="all, delete-orphan")
    chat_sessions  = db.relationship("ChatSession",    back_populates="user", cascade="all, delete-orphan")
    workout_logs   = db.relationship("WorkoutLog",     back_populates="user", cascade="all, delete-orphan")
    meal_logs      = db.relationship("MealLog",        back_populates="user", cascade="all, delete-orphan")
    weight_logs    = db.relationship("WeightLog",      back_populates="user", cascade="all, delete-orphan")
    water_logs     = db.relationship("WaterLog",       back_populates="user", cascade="all, delete-orphan")
    workout_plans  = db.relationship("WorkoutPlan",    back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"


# ─────────────────────────────────────────────────────────────────────────────
# User Profile
# ─────────────────────────────────────────────────────────────────────────────
class UserProfile(db.Model):
    __tablename__ = "user_profiles"

    id              = db.Column(db.Integer, primary_key=True)
    user_id         = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True)
    full_name       = db.Column(db.String(120))
    date_of_birth   = db.Column(db.Date)
    gender          = db.Column(db.String(20))           # male / female / other
    height_cm       = db.Column(db.Float)
    weight_kg       = db.Column(db.Float)
    target_weight   = db.Column(db.Float)
    activity_level  = db.Column(db.String(50))           # sedentary/lightly/moderately/very/extra
    fitness_goal    = db.Column(db.String(100))          # weight loss / muscle gain / maintenance
    diet_preference = db.Column(db.String(50))           # vegetarian / vegan / non-veg / jain
    experience_level= db.Column(db.String(30))           # beginner / intermediate / advanced
    medical_conditions = db.Column(db.Text)
    equipment_available = db.Column(db.Text)
    workout_days_per_week = db.Column(db.Integer, default=3)
    avatar_url      = db.Column(db.String(255))
    updated_at      = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship("User", back_populates="profile")

    @property
    def age(self):
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None

    @property
    def bmi(self):
        if self.height_cm and self.weight_kg:
            h = self.height_cm / 100
            return round(self.weight_kg / (h * h), 1)
        return None

    @property
    def bmi_category(self):
        bmi = self.bmi
        if bmi is None:
            return "Unknown"
        if bmi < 18.5:  return "Underweight"
        if bmi < 25.0:  return "Normal weight"
        if bmi < 30.0:  return "Overweight"
        return "Obese"

    def bmr(self):
        """Mifflin-St Jeor BMR equation."""
        if not all([self.weight_kg, self.height_cm, self.age, self.gender]):
            return None
        if self.gender == "male":
            return round(10 * self.weight_kg + 6.25 * self.height_cm - 5 * self.age + 5)
        return round(10 * self.weight_kg + 6.25 * self.height_cm - 5 * self.age - 161)

    def tdee(self):
        """Total Daily Energy Expenditure."""
        activity_multipliers = {
            "sedentary"  : 1.2,
            "lightly"    : 1.375,
            "moderately" : 1.55,
            "very"       : 1.725,
            "extra"      : 1.9,
        }
        bmr = self.bmr()
        if bmr is None:
            return None
        m = activity_multipliers.get(self.activity_level, 1.375)
        return round(bmr * m)

    def __repr__(self):
        return f"<UserProfile {self.user_id}>"


# ─────────────────────────────────────────────────────────────────────────────
# Chat Models
# ─────────────────────────────────────────────────────────────────────────────
class ChatSession(db.Model):
    __tablename__ = "chat_sessions"

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("users.id"))
    title      = db.Column(db.String(200), default="New Chat")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user     = db.relationship("User",        back_populates="chat_sessions")
    messages = db.relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.created_at")

    def __repr__(self):
        return f"<ChatSession {self.id}>"


class ChatMessage(db.Model):
    __tablename__ = "chat_messages"

    id         = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("chat_sessions.id"))
    role       = db.Column(db.String(20))   # "user" or "assistant"
    content    = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    session = db.relationship("ChatSession", back_populates="messages")


# ─────────────────────────────────────────────────────────────────────────────
# Workout Models
# ─────────────────────────────────────────────────────────────────────────────
class WorkoutPlan(db.Model):
    __tablename__ = "workout_plans"

    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("users.id"))
    name        = db.Column(db.String(200))
    description = db.Column(db.Text)
    plan_type   = db.Column(db.String(50))    # weight_loss / muscle_gain / maintenance
    duration_weeks = db.Column(db.Integer)
    content     = db.Column(db.Text)          # JSON or markdown content
    is_active   = db.Column(db.Boolean, default=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="workout_plans")


class WorkoutLog(db.Model):
    __tablename__ = "workout_logs"

    id               = db.Column(db.Integer, primary_key=True)
    user_id          = db.Column(db.Integer, db.ForeignKey("users.id"))
    date             = db.Column(db.Date, default=date.today)
    workout_type     = db.Column(db.String(100))
    duration_minutes = db.Column(db.Integer)
    calories_burned  = db.Column(db.Float)
    exercises        = db.Column(db.Text)    # JSON list
    notes            = db.Column(db.Text)
    intensity        = db.Column(db.String(20))   # low / moderate / high
    completed        = db.Column(db.Boolean, default=True)
    created_at       = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="workout_logs")


# ─────────────────────────────────────────────────────────────────────────────
# Nutrition Models
# ─────────────────────────────────────────────────────────────────────────────
class MealLog(db.Model):
    __tablename__ = "meal_logs"

    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey("users.id"))
    date         = db.Column(db.Date, default=date.today)
    meal_type    = db.Column(db.String(30))     # breakfast / lunch / dinner / snack
    food_items   = db.Column(db.Text)           # JSON list
    calories     = db.Column(db.Float)
    protein_g    = db.Column(db.Float)
    carbs_g      = db.Column(db.Float)
    fat_g        = db.Column(db.Float)
    notes        = db.Column(db.Text)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="meal_logs")


# ─────────────────────────────────────────────────────────────────────────────
# Progress Models
# ─────────────────────────────────────────────────────────────────────────────
class WeightLog(db.Model):
    __tablename__ = "weight_logs"

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("users.id"))
    date       = db.Column(db.Date, default=date.today)
    weight_kg  = db.Column(db.Float, nullable=False)
    body_fat_pct = db.Column(db.Float)
    muscle_mass_kg = db.Column(db.Float)
    notes      = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="weight_logs")


class WaterLog(db.Model):
    __tablename__ = "water_logs"

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("users.id"))
    date       = db.Column(db.Date, default=date.today)
    amount_ml  = db.Column(db.Float, default=0)
    goal_ml    = db.Column(db.Float, default=2500)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="water_logs")
