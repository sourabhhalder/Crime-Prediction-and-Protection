import pandas as pd
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

# -------------------------------
# LOAD DATA
# -------------------------------
BASE_DIR = os.getcwd()
crime_df = pd.read_csv(os.path.join(BASE_DIR, "crime_data_latlong.csv"))

crime_df.columns = crime_df.columns.str.strip().str.lower()

# -------------------------------
# ENCODERS
# -------------------------------
le_area = LabelEncoder()
le_gender = LabelEncoder()
le_time = LabelEncoder()

crime_df['area_enc'] = le_area.fit_transform(crime_df['area'])
crime_df['gender_enc'] = le_gender.fit_transform(crime_df['gender'])
crime_df['time_enc'] = le_time.fit_transform(crime_df['time_of_day'])

# -------------------------------
# TARGET VARIABLE
# -------------------------------
crime_df['risk'] = crime_df['severity'].map({
    'low': 0,
    'medium': 1,
    'high': 1
}).fillna(0)

# -------------------------------
# FEATURES
# -------------------------------
X = crime_df[['area_enc', 'gender_enc', 'time_enc']]
y = crime_df['risk']

# -------------------------------
# MODEL TRAINING
# -------------------------------
model = RandomForestClassifier(n_estimators=100)
model.fit(X, y)

# -------------------------------
# PREDICTION FUNCTION
# -------------------------------
def predict_safety(area, gender, time):

    try:
        area_val = le_area.transform([area])[0]
    except:
        area_val = 0

    try:
        gender_val = le_gender.transform([gender])[0]
    except:
        gender_val = 0

    try:
        time_val = le_time.transform([time])[0]
    except:
        time_val = 0

    proba = model.predict_proba([[area_val, gender_val, time_val]])

    # Handle single-class issue
    if proba.shape[1] == 2:
        prob = proba[0][1]
    else:
        prob = proba[0][0]

    # Smooth values
    prob = max(0.1, min(0.9, prob))

    safety_score = int((1 - prob) * 100)

    return safety_score, prob

# -------------------------------
# EXPLAINABILITY
# -------------------------------
def get_area_insights(area):

    area_data = crime_df[crime_df['area'].str.lower() == area.lower()]

    if area_data.empty:
        return {}

    return area_data['severity'].value_counts().to_dict()