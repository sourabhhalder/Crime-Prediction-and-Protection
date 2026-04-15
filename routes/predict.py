from flask import Blueprint, request, jsonify, session
import pandas as pd
import os
import random

from models.ml_model import predict_safety, get_area_insights
from models.db import save_log, get_user_logs

predict_bp = Blueprint("predict", __name__)

# -------------------------------
# LOAD DATA (for map features)
# -------------------------------
BASE_DIR = os.getcwd()
crime_df = pd.read_csv(os.path.join(BASE_DIR, "crime_data_latlong.csv"))

crime_df.columns = crime_df.columns.str.strip().str.lower()

# -------------------------------
# 🔥 IMPROVED FORECAST
# -------------------------------
def generate_forecast(base_score):
    forecast = []

    trend = base_score

    for i in range(30):
        variation = random.randint(-5, 5)

        trend = trend + variation

        # soft bounds (avoid flat lines)
        trend = max(10, min(90, trend))

        status = "Safe" if trend > 70 else "Moderate" if trend > 40 else "Risky"

        forecast.append({
            "day": f"Day {i+1}",
            "score": int(trend),
            "status": status
        })

    return forecast

# -------------------------------
# MAP
# -------------------------------
def get_area_coordinates(area):
    row = crime_df[crime_df['area'].str.lower() == str(area).lower()]

    if not row.empty:
        return float(row.iloc[0]['latitude']), float(row.iloc[0]['longitude'])

    return 25.4358, 81.8463

# -------------------------------
# HEATMAP
# -------------------------------
def get_heatmap_data():
    heat_data = []

    for _, row in crime_df.iterrows():
        try:
            heat_data.append([
                float(row['latitude']),
                float(row['longitude']),
                float(row['crime_count'])
            ])
        except:
            continue

    return heat_data

# -------------------------------
# POLICE
# -------------------------------
def get_nearest_police(area):
    area_data = crime_df[crime_df['area'].str.lower() == area.lower()]

    if not area_data.empty:
        return area_data.iloc[0]['police_station']

    return "Not available"

# -------------------------------
# 🔥 DASHBOARD API (CLEAN)
# -------------------------------
@predict_bp.route("/user_logs", methods=["GET"])
def user_logs():
    try:
        user = session.get("user", "guest")

        logs = get_user_logs(user)

        result = []
        for row in logs:
            result.append({
                "area": row[0],
                "gender": row[1],
                "time": row[2],
                "score": row[3]
            })

        return jsonify(result)

    except Exception as e:
        print("ERROR:", str(e))
        return jsonify([])

# -------------------------------
# PREDICT ROUTE
# -------------------------------
@predict_bp.route("/predict", methods=["POST"])
def predict():

    try:
        data = request.get_json()

        area = data.get("locality", "")
        gender = data.get("gender", "Male")
        time = data.get("time", "Day")

        # ---------------- ML ----------------
        safety_score, prob = predict_safety(area, gender, time)

        # ---------------- MESSAGE ----------------
        if safety_score > 70:
            message = "Safe area with low recent crime activity"
        elif safety_score > 40:
            message = "Moderate risk. Stay alert and aware"
        else:
            message = "High risk area. Avoid traveling alone and prefer safer routes"

        # ---------------- CONFIDENCE ----------------
        confidence = round((1 - abs(0.5 - prob)) * 100, 2)

        # ---------------- REASONS ----------------
        reasons = []

        if time.lower() == "night":
            reasons.append("Higher crime probability at night")

        if gender.lower() == "female":
            reasons.append("Higher vulnerability observed in historical data")

        insights = get_area_insights(area)
        if insights:
            reasons.append(f"Crime pattern: {insights}")

        # ---------------- ADVICE ----------------
        advice = []

        if safety_score < 50:
            advice.append("Avoid isolated or low-visibility areas")
            advice.append("Stay in crowded or well-lit places")

        if time.lower() == "night":
            advice.append("Avoid late-night travel if possible")

        if gender.lower() == "female":
            advice.append("Share live location with trusted contacts")

        # ---------------- EXTRA FEATURES ----------------
        forecast = generate_forecast(safety_score)
        lat, lon = get_area_coordinates(area)
        heatmap = get_heatmap_data()
        police = get_nearest_police(area)

        # ---------------- SAVE LOG ----------------
        user_email = session.get("user", "guest")
        save_log(user_email, area, gender, time, safety_score)

        # ---------------- RESPONSE ----------------
        return jsonify({
            "safety_score": safety_score,
            "message": message,
            "confidence": confidence,
            "reasons": reasons,
            "forecast": forecast,
            "lat": lat,
            "lon": lon,
            "heatmap": heatmap,
            "police_station": police,
            "advice": advice
        })

    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({
            "error": "Backend error",
            "details": str(e)
        }), 500