"""
Fitness Buddy — API Routes (AJAX endpoints)
Progress tracking, water logging, quick stats.
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from datetime import date, timedelta
from models import db, WaterLog, WeightLog, WorkoutLog, MealLog

api_bp = Blueprint("api", __name__)


@api_bp.route("/water/add", methods=["POST"])
@login_required
def add_water():
    data   = request.get_json()
    amount = float(data.get("amount_ml", 250))

    log = WaterLog.query.filter_by(user_id=current_user.id, date=date.today()).first()
    if log:
        log.amount_ml += amount
    else:
        log = WaterLog(user_id=current_user.id, date=date.today(), amount_ml=amount)
        db.session.add(log)
    db.session.commit()

    return jsonify({
        "total_ml"  : log.amount_ml,
        "goal_ml"   : log.goal_ml,
        "percentage": round(min(log.amount_ml / log.goal_ml * 100, 100), 1),
    })


@api_bp.route("/water/goal", methods=["POST"])
@login_required
def set_water_goal():
    data    = request.get_json()
    goal_ml = float(data.get("goal_ml", 2500))
    log = WaterLog.query.filter_by(user_id=current_user.id, date=date.today()).first()
    if not log:
        log = WaterLog(user_id=current_user.id, date=date.today())
        db.session.add(log)
    log.goal_ml = goal_ml
    db.session.commit()
    return jsonify({"goal_ml": goal_ml})


@api_bp.route("/stats/summary")
@login_required
def stats_summary():
    today   = date.today()
    profile = current_user.profile

    # Weight progress
    latest_weight = (
        WeightLog.query
        .filter_by(user_id=current_user.id)
        .order_by(WeightLog.date.desc())
        .first()
    )

    # Monthly workouts
    month_start = today.replace(day=1)
    monthly_workouts = WorkoutLog.query.filter(
        WorkoutLog.user_id  == current_user.id,
        WorkoutLog.date     >= month_start,
        WorkoutLog.completed == True,
    ).count()

    # Today's calories
    today_meals   = MealLog.query.filter_by(user_id=current_user.id, date=today).all()
    today_cals    = sum(m.calories or 0 for m in today_meals)

    return jsonify({
        "bmi"              : profile.bmi if profile else None,
        "bmi_category"     : profile.bmi_category if profile else "Unknown",
        "current_weight"   : latest_weight.weight_kg if latest_weight else (profile.weight_kg if profile else None),
        "target_weight"    : profile.target_weight   if profile else None,
        "monthly_workouts" : monthly_workouts,
        "today_calories"   : round(today_cals),
        "calorie_goal"     : profile.tdee() if profile else 2000,
    })


@api_bp.route("/progress/weight")
@login_required
def weight_progress():
    days   = int(request.args.get("days", 30))
    since  = date.today() - timedelta(days=days)
    logs   = (
        WeightLog.query
        .filter(WeightLog.user_id == current_user.id, WeightLog.date >= since)
        .order_by(WeightLog.date)
        .all()
    )
    return jsonify([
        {"date": str(l.date), "weight": l.weight_kg, "body_fat": l.body_fat_pct}
        for l in logs
    ])
