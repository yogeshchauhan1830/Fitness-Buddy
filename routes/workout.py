"""
Fitness Buddy — Workout Routes
"""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import date
from models import db, WorkoutLog, WorkoutPlan
import json

workout_bp = Blueprint("workout", __name__)


@workout_bp.route("/workout")
@login_required
def index():
    plans = WorkoutPlan.query.filter_by(
        user_id=current_user.id, is_active=True
    ).order_by(WorkoutPlan.created_at.desc()).all()

    recent_logs = (
        WorkoutLog.query
        .filter_by(user_id=current_user.id)
        .order_by(WorkoutLog.date.desc())
        .limit(10)
        .all()
    )
    return render_template("workout/index.html", plans=plans, recent_logs=recent_logs)


@workout_bp.route("/workout/log", methods=["POST"])
@login_required
def log_workout():
    data = request.get_json() or request.form.to_dict()
    log = WorkoutLog(
        user_id         = current_user.id,
        date            = date.today(),
        workout_type    = data.get("workout_type", "General"),
        duration_minutes= int(data.get("duration_minutes", 0)),
        calories_burned = float(data.get("calories_burned", 0)),
        exercises       = json.dumps(data.get("exercises", [])),
        notes           = data.get("notes", ""),
        intensity       = data.get("intensity", "moderate"),
        completed       = True,
    )
    db.session.add(log)
    db.session.commit()
    return jsonify({"success": True, "log_id": log.id})


@workout_bp.route("/workout/history")
@login_required
def history():
    logs = (
        WorkoutLog.query
        .filter_by(user_id=current_user.id)
        .order_by(WorkoutLog.date.desc())
        .limit(30)
        .all()
    )
    return render_template("workout/history.html", logs=logs)
