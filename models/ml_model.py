import pandas as pd
import os
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import OneHotEncoder

# -------------------------------
# LOAD DATA
# -------------------------------
BASE_DIR = os.getcwd()
crime_df = pd.read_csv(os.path.join(BASE_DIR, "crime_data_latlong.csv"))

crime_df.columns = crime_df.columns.str.strip().str.lower()

# -------------------------------
# CLEANING
# -------------------------------
crime_df['severity'] = crime_df['severity'].astype(str).str.lower().str.strip()

severity_map = {'low': 1, 'medium': 2, 'high': 3}
crime_df['severity_num'] = crime_df['severity'].map(severity_map).fillna(1)

crime_df['age'] = crime_df['age'].fillna(crime_df['age'].median())
crime_df['crime_count'] = crime_df['crime_count'].fillna(1)

# -------------------------------
# 🔥 AREA INTELLIGENCE (KEY FEATURE)
# -------------------------------
area_risk_map = crime_df.groupby('area')['severity_num'].mean().to_dict()

# -------------------------------
# ENCODING
# -------------------------------
encoder = OneHotEncoder(handle_unknown='ignore')

X_cat = encoder.fit_transform(
    crime_df[['area', 'gender', 'time_of_day']]
).toarray()

X_num = crime_df[['age', 'crime_count']].values

X = np.hstack([X_cat, X_num])
y = crime_df['severity_num']

# -------------------------------
# MODEL
# -------------------------------
model = RandomForestClassifier(
    n_estimators=200,
    max_depth=10,
    random_state=42
)

model.fit(X, y)

# -------------------------------
# PREDICTION
# -------------------------------
def predict_safety(area, gender, time, age=25):

    try:
        area = str(area).strip()
        gender = str(gender).strip()
        time = str(time).strip()

        # -------------------------------
        # 🔥 DYNAMIC CRIME INTENSITY
        # -------------------------------
        area_data = crime_df[crime_df['area'].str.lower() == area.lower()]

        if not area_data.empty:
            avg_crime = area_data['crime_count'].mean()
        else:
            avg_crime = crime_df['crime_count'].mean()

        # -------------------------------
        # ENCODING INPUT
        # -------------------------------
        input_df = pd.DataFrame([{
            "area": area,
            "gender": gender,
            "time_of_day": time
        }])

        X_cat = encoder.transform(input_df).toarray()
        X_num = np.array([[age, avg_crime]])

        X_input = np.hstack([X_cat, X_num])

        # -------------------------------
        # MODEL PREDICTION
        # -------------------------------
        proba = model.predict_proba(X_input)[0]

        # risk from model
        risk_model = (proba[1] * 0.5 + proba[2] * 1.0)

        # -------------------------------
        # 🔥 AREA RISK BOOST
        # -------------------------------
        area_risk = area_risk_map.get(area, 2)

        risk = (risk_model * 0.6) + ((area_risk / 3) * 0.4)

        # -------------------------------
        # FINAL SAFETY SCORE
        # -------------------------------
        safety_score = int((1 - risk) * 100)

        # clamp
        safety_score = max(5, min(95, safety_score))

        return safety_score, risk

    except Exception as e:
        print("ML ERROR:", str(e))
        return 50, 0.5


# -------------------------------
# AREA INSIGHTS
# -------------------------------
def get_area_insights(area):

    try:
        area_data = crime_df[crime_df['area'].str.lower() == str(area).lower()]

        if area_data.empty:
            return {}

        return area_data['severity'].value_counts().to_dict()

    except Exception as e:
        print("INSIGHTS ERROR:", str(e))
        return {}