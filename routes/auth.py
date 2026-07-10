"""
Fitness Buddy — Auth Routes
Login, Register, Logout
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, UserProfile

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.home"))
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.home"))

    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember_me"))

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            from datetime import datetime
            user.last_login = datetime.utcnow()
            db.session.commit()
            login_user(user, remember=remember)
            next_page = request.args.get("next")
            flash(f"Welcome back, {user.username}! 💪", "success")
            return redirect(next_page or url_for("dashboard.home"))
        flash("Invalid email or password. Please try again.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.home"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm  = request.form.get("confirm_password", "")

        # Validation
        if not all([username, email, password, confirm]):
            flash("All fields are required.", "danger")
            return render_template("auth/register.html")
        if password != confirm:
            flash("Passwords do not match.", "danger")
            return render_template("auth/register.html")
        if len(password) < 8:
            flash("Password must be at least 8 characters.", "danger")
            return render_template("auth/register.html")
        if User.query.filter_by(email=email).first():
            flash("Email already registered. Please login.", "danger")
            return render_template("auth/register.html")
        if User.query.filter_by(username=username).first():
            flash("Username already taken.", "danger")
            return render_template("auth/register.html")

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        profile = UserProfile(user_id=user.id)
        db.session.add(profile)
        db.session.commit()

        login_user(user)
        flash("Account created! Let's set up your fitness profile. 🎯", "success")
        return redirect(url_for("profile.setup"))

    return render_template("auth/register.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully. Keep up the fitness journey! 💪", "info")
    return redirect(url_for("auth.login"))
