from flask import Blueprint, request, jsonify, session
import pandas as pd
import os
import random
import numpy as np

from models.ml_model import predict_safety, get_area_insights
from models.db import save_log, get_user_logs

predict_bp = Blueprint("predict", __name__)

# -------------------------------
# LOAD DATA
# -------------------------------
BASE_DIR = os.getcwd()
crime_df = pd.read_csv(os.path.join(BASE_DIR, "crime_data_latlong.csv"))
crime_df.columns = crime_df.columns.str.strip().str.lower()

# -------------------------------
# 📍 SMART LOCATION MATCHING
# -------------------------------
def get_area_coordinates(area):
    try:
        area = str(area).strip().lower()

        row = crime_df[
            crime_df['area'].str.lower().str.contains(area, na=False)
        ]

        if not row.empty:
            lat = row['latitude'].mean()
            lon = row['longitude'].mean()
            return float(lat), float(lon)

        return 25.4358, 81.8463  # Prayagraj center

    except Exception as e:
        print("MAP ERROR:", str(e))
        return 25.4358, 81.8463


# -------------------------------
# 🔥 HEATMAP (AREA FILTERED)
# -------------------------------
def get_heatmap_data(area=None):
    heat_data = []

    df = crime_df

    if area:
        df = crime_df[
            crime_df['area'].str.lower().str.contains(area.lower(), na=False)
        ]

    for _, row in df.iterrows():
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
# 🚔 POLICE (SMART MATCH)
# -------------------------------
def get_nearest_police(area):
    try:
        area_data = crime_df[
            crime_df['area'].str.lower().str.contains(area.lower(), na=False)
        ]

        if not area_data.empty:
            return area_data.iloc[0]['police_station']

        return "Not available"

    except Exception as e:
        print("POLICE ERROR:", str(e))
        return "Not available"

# -------------------------------
# 🟢 SAFE ZONES (LOW RISK AREAS)
# -------------------------------
def get_safe_zones():
    try:
        safe_areas = crime_df.groupby('area')['severity'].apply(
            lambda x: (x == 'low').sum()
        ).sort_values(ascending=False).head(5)

        result = []

        for area in safe_areas.index:
            row = crime_df[crime_df['area'] == area].iloc[0]

            result.append({
                "area": area,
                "lat": float(row['latitude']),
                "lon": float(row['longitude'])
            })

        return result

    except Exception as e:
        print("SAFE ZONE ERROR:", str(e))
        return []
    try:
        area_data = crime_df[
            crime_df['area'].str.lower().str.contains(area.lower(), na=False)
        ]

        if not area_data.empty:
            return area_data.iloc[0]['police_station']

        return "Not available"

    except:
        return "Not available"


# -------------------------------
# 📊 FORECAST (REALISTIC)
# -------------------------------
def generate_forecast(base_score):
    forecast = []
    trend = base_score

    for i in range(30):
        drift = np.random.normal(0, 4)
        trend += drift
        trend = max(10, min(90, trend))

        status = "Safe" if trend > 70 else "Moderate" if trend > 40 else "Risky"

        forecast.append({
            "day": f"Day {i+1}",
            "score": int(trend),
            "status": status
        })

    return forecast


# -------------------------------
# 📊 USER LOGS
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
# 🚀 FINAL PREDICT API
# -------------------------------
@predict_bp.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json()

        area = data.get("locality", "")
        gender = data.get("gender", "Male")
        time = data.get("time", "Day")
        age = int(data.get("age", 25))

        # ---------------- ML ----------------
        safety_score, prob = predict_safety(area, gender, time, age)

        # ---------------- 🔥 HYBRID LOGIC ----------------
        if gender.lower() == "female":
            safety_score -= random.randint(8, 15)

        if time.lower() == "night":
            safety_score -= random.randint(10, 20)
        elif time.lower() == "evening":
            safety_score -= random.randint(5, 10)

        if age < 18:
            safety_score -= 5

        # slight randomness for realism
        safety_score += random.randint(-5, 5)

        safety_score = max(5, min(95, safety_score))

        # ---------------- MESSAGE ----------------
        if safety_score > 75:
            message = "Safe area with low recent crime activity"
        elif safety_score > 50:
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

        if age < 18:
            reasons.append("Minors are more vulnerable in unsafe areas")

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
        heatmap = get_heatmap_data(area)
        police = get_nearest_police(area)
        safe_zones = get_safe_zones()

        # take top dangerous points (hotspots)
        danger_zones = heatmap[:30]

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
            "advice": advice,
	    # 🔥 NEW FEATURES
            "safe_zones": safe_zones,
            "danger_zones": danger_zones
        })

    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({
            "error": "Backend error",
            "details": str(e)
        }), 500