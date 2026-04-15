from flask import Flask, request, jsonify, render_template
import pandas as pd
import os
import random

# Import modules
from models.db import init_db, save_log
from models.ml_model import predict_safety, get_area_insights

app = Flask(__name__)

# -------------------------------
# INIT DATABASE
# -------------------------------
init_db()

# -------------------------------
# LOAD DATA (for map + heatmap)
# -------------------------------
BASE_DIR = os.getcwd()
crime_df = pd.read_csv(os.path.join(BASE_DIR, "crime_data_latlong.csv"))

crime_df.columns = crime_df.columns.str.strip().str.lower()

# -------------------------------
# FORECAST FUNCTION
# -------------------------------
def generate_forecast(base_score):
    forecast = []

    for i in range(30):
        variation = random.randint(-8, 8)
        score = max(20, min(95, base_score + variation))

        if score > 70:
            status = "Safe"
        elif score > 40:
            status = "Moderate"
        else:
            status = "Risky"

        forecast.append({
            "day": f"Day {i+1}",
            "score": score,
            "status": status
        })

    return forecast

# -------------------------------
# MAP COORDINATES
# -------------------------------
def get_area_coordinates(area):
    row = crime_df[crime_df['area'].str.lower() == str(area).lower()]

    if not row.empty:
        return float(row.iloc[0]['latitude']), float(row.iloc[0]['longitude'])

    return 25.4358, 81.8463

# -------------------------------
# HEATMAP DATA
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
# POLICE STATION
# -------------------------------
def get_nearest_police(area):
    area_data = crime_df[crime_df['area'].str.lower() == area.lower()]

    if not area_data.empty:
        return area_data.iloc[0]['police_station']

    return "Not available"

# -------------------------------
# ROUTES
# -------------------------------
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/predict", methods=["POST"])
def predict():

    try:
        data = request.get_json()

        area = data.get("locality", "")
        gender = data.get("gender", "Male")
        time = data.get("time", "Day")

        # -------------------------------
        # ML PREDICTION (from module)
        # -------------------------------
        safety_score, prob = predict_safety(area, gender, time)

        # -------------------------------
        # MESSAGE
        # -------------------------------
        if safety_score > 70:
            message = "Safe area with low recent crime activity"
        elif safety_score > 40:
            message = "Moderate risk. Stay alert and avoid isolated places"
        else:
            message = "High risk area. Prefer daytime travel and crowded routes"

        # -------------------------------
        # CONFIDENCE
        # -------------------------------
        confidence = round((1 - abs(0.5 - prob)) * 100, 2)

        # -------------------------------
        # EXPLANATION
        # -------------------------------
        reasons = []

        if time.lower() == "night":
            reasons.append("Crime rates are higher during night hours")

        if gender.lower() == "female":
            reasons.append("Historical data shows increased vulnerability for women")

        insights = get_area_insights(area)
        if insights:
            reasons.append(f"Crime pattern: {insights}")

        # -------------------------------
        # SAFETY ADVICE
        # -------------------------------
        advice = []

        if safety_score < 50:
            advice.append("Avoid traveling alone")
            advice.append("Prefer crowded routes")

        if time.lower() == "night":
            advice.append("Avoid late-night travel if possible")

        if gender.lower() == "female":
            advice.append("Share live location with trusted contacts")

        # -------------------------------
        # EXTRA FEATURES
        # -------------------------------
        forecast = generate_forecast(safety_score)
        lat, lon = get_area_coordinates(area)
        heatmap = get_heatmap_data()
        police = get_nearest_police(area)

        # -------------------------------
        # SAVE USER LOG (optional email)
        # -------------------------------
        user_email = data.get("email", "guest")

        save_log(user_email, area, gender, time, safety_score)

        # -------------------------------
        # RESPONSE
        # -------------------------------
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


# -------------------------------
# RUN APP
# -------------------------------
if __name__ == "__main__":
    app.run(debug=True)