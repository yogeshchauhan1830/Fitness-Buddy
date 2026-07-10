"""
Fitness Buddy — Nutrition Routes
"""
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from datetime import date
from models import db, MealLog
import json

nutrition_bp = Blueprint("nutrition", __name__)


@nutrition_bp.route("/nutrition")
@login_required
def index():
    today_meals = MealLog.query.filter_by(
        user_id=current_user.id, date=date.today()
    ).all()

    total_calories = sum(m.calories or 0 for m in today_meals)
    total_protein  = sum(m.protein_g or 0 for m in today_meals)
    total_carbs    = sum(m.carbs_g   or 0 for m in today_meals)
    total_fat      = sum(m.fat_g     or 0 for m in today_meals)

    profile = current_user.profile
    calorie_goal = profile.tdee() if profile else 2000

    return render_template(
        "nutrition/index.html",
        today_meals    = today_meals,
        total_calories = round(total_calories),
        total_protein  = round(total_protein, 1),
        total_carbs    = round(total_carbs, 1),
        total_fat      = round(total_fat, 1),
        calorie_goal   = calorie_goal,
    )


@nutrition_bp.route("/nutrition/log", methods=["POST"])
@login_required
def log_meal():
    data = request.get_json() or request.form.to_dict()
    log = MealLog(
        user_id   = current_user.id,
        date      = date.today(),
        meal_type = data.get("meal_type", "other"),
        food_items= json.dumps(data.get("food_items", [])),
        calories  = float(data.get("calories", 0)),
        protein_g = float(data.get("protein_g", 0)),
        carbs_g   = float(data.get("carbs_g", 0)),
        fat_g     = float(data.get("fat_g", 0)),
        notes     = data.get("notes", ""),
    )
    db.session.add(log)
    db.session.commit()
    return jsonify({"success": True, "log_id": log.id})
