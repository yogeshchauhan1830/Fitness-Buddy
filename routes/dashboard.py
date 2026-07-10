"""
Fitness Buddy — Dashboard Routes
"""
from datetime import date, timedelta, datetime
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import db, WorkoutLog, MealLog, WeightLog, WaterLog

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
@login_required
def home():
    profile  = current_user.profile
    today    = date.today()
    week_ago = today - timedelta(days=7)

    # ── Today's summary ────────────────────────────────────────
    today_workouts = WorkoutLog.query.filter_by(
        user_id=current_user.id, date=today
    ).all()
    today_meals = MealLog.query.filter_by(
        user_id=current_user.id, date=today
    ).all()
    today_water = WaterLog.query.filter_by(
        user_id=current_user.id, date=today
    ).first()

    calories_burned  = sum(w.calories_burned or 0 for w in today_workouts)
    calories_consumed = sum(m.calories or 0 for m in today_meals)
    water_ml          = today_water.amount_ml if today_water else 0
    water_goal        = today_water.goal_ml   if today_water else 2500

    # ── Weekly workout streak ──────────────────────────────────
    streak = _calculate_streak(current_user.id)

    # ── Weight history (last 30 days) ─────────────────────────
    weight_history = (
        WeightLog.query
        .filter(WeightLog.user_id == current_user.id, WeightLog.date >= today - timedelta(days=30))
        .order_by(WeightLog.date)
        .all()
    )
    weight_labels = [str(w.date) for w in weight_history]
    weight_data   = [w.weight_kg for w in weight_history]

    # ── Weekly calories ────────────────────────────────────────
    weekly_cal_data = []
    weekly_cal_labels = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        meals = MealLog.query.filter_by(user_id=current_user.id, date=d).all()
        weekly_cal_labels.append(d.strftime("%a"))
        weekly_cal_data.append(round(sum(m.calories or 0 for m in meals)))

    return render_template(
        "dashboard/home.html",
        profile          = profile,
        calories_burned  = round(calories_burned),
        calories_consumed= round(calories_consumed),
        water_ml         = round(water_ml),
        water_goal       = water_goal,
        streak           = streak,
        weight_labels    = weight_labels,
        weight_data      = weight_data,
        weekly_cal_labels= weekly_cal_labels,
        weekly_cal_data  = weekly_cal_data,
        today_workouts   = today_workouts,
        today_meals      = today_meals,
        now_hour         = datetime.now().hour,
    )


def _calculate_streak(user_id: int) -> int:
    today    = date.today()
    streak   = 0
    check_date = today
    for _ in range(365):
        has_workout = WorkoutLog.query.filter_by(
            user_id=user_id, date=check_date, completed=True
        ).first()
        if has_workout:
            streak   += 1
            check_date = check_date - timedelta(days=1)
        elif check_date == today:
            check_date = check_date - timedelta(days=1)
        else:
            break
    return streak
