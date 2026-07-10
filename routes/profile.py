"""
Fitness Buddy — Profile Routes
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from datetime import date
from models import db, UserProfile, WeightLog

profile_bp = Blueprint("profile", __name__)


@profile_bp.route("/profile")
@login_required
def view():
    return render_template("profile/view.html", profile=current_user.profile)


@profile_bp.route("/profile/setup", methods=["GET", "POST"])
@login_required
def setup():
    profile = current_user.profile or UserProfile(user_id=current_user.id)

    if request.method == "POST":
        _update_profile(profile, request.form)
        if not profile.id:
            db.session.add(profile)
        db.session.commit()
        flash("Profile saved! Let's start your fitness journey. 🎯", "success")
        return redirect(url_for("dashboard.home"))

    return render_template("profile/setup.html", profile=profile)


@profile_bp.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit():
    profile = current_user.profile
    if not profile:
        return redirect(url_for("profile.setup"))

    if request.method == "POST":
        _update_profile(profile, request.form)
        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for("profile.view"))

    return render_template("profile/edit.html", profile=profile)


@profile_bp.route("/profile/weight/log", methods=["POST"])
@login_required
def log_weight():
    data      = request.get_json()
    weight_kg = float(data.get("weight_kg", 0))
    if not weight_kg:
        return jsonify({"error": "Invalid weight"}), 400

    log = WeightLog(
        user_id   = current_user.id,
        date      = date.today(),
        weight_kg = weight_kg,
        body_fat_pct   = data.get("body_fat_pct"),
        muscle_mass_kg = data.get("muscle_mass_kg"),
        notes     = data.get("notes", ""),
    )
    db.session.add(log)

    # Update profile weight
    profile = current_user.profile
    if profile:
        profile.weight_kg = weight_kg
    db.session.commit()

    return jsonify({"success": True, "new_bmi": profile.bmi if profile else None})


def _update_profile(profile: UserProfile, form):
    profile.full_name     = form.get("full_name", "")
    profile.gender        = form.get("gender", "")
    profile.height_cm     = float(form.get("height_cm") or 0) or None
    profile.weight_kg     = float(form.get("weight_kg") or 0) or None
    profile.target_weight = float(form.get("target_weight") or 0) or None
    profile.activity_level= form.get("activity_level", "lightly")
    profile.fitness_goal  = form.get("fitness_goal", "")
    profile.diet_preference = form.get("diet_preference", "")
    profile.experience_level = form.get("experience_level", "beginner")
    profile.medical_conditions  = form.get("medical_conditions", "")
    profile.equipment_available = form.get("equipment_available", "")
    profile.workout_days_per_week = int(form.get("workout_days_per_week") or 3)
    dob_str = form.get("date_of_birth", "")
    if dob_str:
        try:
            from datetime import datetime
            profile.date_of_birth = datetime.strptime(dob_str, "%Y-%m-%d").date()
        except ValueError:
            pass
