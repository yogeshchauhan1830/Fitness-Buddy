"""
Fitness Buddy — Calculators Routes
BMI, BMR, TDEE, Calorie, Water Intake, Macro Calculator
"""
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required

calculators_bp = Blueprint("calculators", __name__)


@calculators_bp.route("/calculators")
@login_required
def index():
    return render_template("calculators/index.html")


@calculators_bp.route("/calculators/bmi", methods=["POST"])
@login_required
def calc_bmi():
    data       = request.get_json()
    weight_kg  = float(data.get("weight_kg", 0))
    height_cm  = float(data.get("height_cm", 0))
    if not weight_kg or not height_cm:
        return jsonify({"error": "Invalid input"}), 400

    h    = height_cm / 100
    bmi  = round(weight_kg / (h * h), 1)
    if bmi < 18.5:   cat = "Underweight"
    elif bmi < 25.0: cat = "Normal weight"
    elif bmi < 30.0: cat = "Overweight"
    else:            cat = "Obese"

    ideal_low  = round(18.5 * h * h, 1)
    ideal_high = round(24.9 * h * h, 1)
    to_lose    = round(weight_kg - ideal_high, 1) if weight_kg > ideal_high else 0
    to_gain    = round(ideal_low - weight_kg, 1)  if weight_kg < ideal_low  else 0

    return jsonify({
        "bmi": bmi, "category": cat,
        "ideal_low": ideal_low, "ideal_high": ideal_high,
        "to_lose": to_lose, "to_gain": to_gain,
    })


@calculators_bp.route("/calculators/bmr", methods=["POST"])
@login_required
def calc_bmr():
    data      = request.get_json()
    weight_kg = float(data.get("weight_kg", 0))
    height_cm = float(data.get("height_cm", 0))
    age       = int(data.get("age", 0))
    gender    = data.get("gender", "male").lower()
    if not all([weight_kg, height_cm, age]):
        return jsonify({"error": "Invalid input"}), 400

    if gender == "male":
        bmr = round(10 * weight_kg + 6.25 * height_cm - 5 * age + 5)
    else:
        bmr = round(10 * weight_kg + 6.25 * height_cm - 5 * age - 161)

    return jsonify({"bmr": bmr, "formula": "Mifflin-St Jeor"})


@calculators_bp.route("/calculators/tdee", methods=["POST"])
@login_required
def calc_tdee():
    data             = request.get_json()
    bmr              = float(data.get("bmr", 0))
    activity_level   = data.get("activity_level", "lightly")
    multipliers = {
        "sedentary" : 1.2,
        "lightly"   : 1.375,
        "moderately": 1.55,
        "very"      : 1.725,
        "extra"     : 1.9,
    }
    m    = multipliers.get(activity_level, 1.375)
    tdee = round(bmr * m)

    return jsonify({
        "tdee"         : tdee,
        "weight_loss"  : tdee - 500,
        "weight_gain"  : tdee + 300,
        "maintenance"  : tdee,
    })


@calculators_bp.route("/calculators/water", methods=["POST"])
@login_required
def calc_water():
    data      = request.get_json()
    weight_kg = float(data.get("weight_kg", 0))
    activity  = data.get("activity_level", "lightly")
    climate   = data.get("climate", "normal")

    base_ml = weight_kg * 35         # 35 ml per kg body weight
    if activity in ["very", "extra"]:
        base_ml += 500
    elif activity == "moderately":
        base_ml += 250
    if climate == "hot":
        base_ml += 500

    glasses = round(base_ml / 250)

    return jsonify({
        "water_ml"    : round(base_ml),
        "water_liters": round(base_ml / 1000, 1),
        "glasses_250ml": glasses,
    })


@calculators_bp.route("/calculators/macros", methods=["POST"])
@login_required
def calc_macros():
    data    = request.get_json()
    tdee    = float(data.get("tdee", 2000))
    goal    = data.get("goal", "maintenance")
    diet    = data.get("diet", "balanced")

    if goal == "weight_loss":
        calories = tdee - 500
    elif goal == "weight_gain":
        calories = tdee + 300
    else:
        calories = tdee

    # Macronutrient splits
    splits = {
        "balanced"      : {"protein": 0.25, "carbs": 0.50, "fat": 0.25},
        "high_protein"  : {"protein": 0.35, "carbs": 0.40, "fat": 0.25},
        "low_carb"      : {"protein": 0.35, "carbs": 0.25, "fat": 0.40},
        "keto"          : {"protein": 0.25, "carbs": 0.05, "fat": 0.70},
    }
    split = splits.get(diet, splits["balanced"])

    return jsonify({
        "calories"  : round(calories),
        "protein_g" : round((calories * split["protein"]) / 4),
        "carbs_g"   : round((calories * split["carbs"])   / 4),
        "fat_g"     : round((calories * split["fat"])     / 9),
    })
