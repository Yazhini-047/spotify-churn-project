import pandas as pd
import joblib
from sklearn.metrics import accuracy_score

# Load data
df = pd.read_csv('spotify_final_combined.csv')

# Feature engineering as in final 2.py
df['ad_stress'] = df['ads_listened_per_week'] / (df['listening_time'] + 1)
df['skip_intensity'] = df['skip_rate'] / (df['songs_played_per_day'] + 1)

X = df.drop(columns=['user_id', 'is_churned', 'country'])
X = pd.get_dummies(X, drop_first=True)
y = df['is_churned']

# Load model
model = joblib.load('spotify_churn_model.pkl')

# Predict
y_pred = model.predict(X)

# Accuracy
acc = accuracy_score(y, y_pred)
print(f"Model Accuracy: {acc:.2%}")