import pandas as pd
import joblib
from sklearn.ensemble import HistGradientBoostingClassifier

# 1. Load your clean data
df = pd.read_csv('spotify_final_combined.csv')

# 2. Prepare features (X) and target (y)
# We drop 'country' and 'user_id' as they aren't used for the math
X = df.drop(columns=['user_id', 'is_churned', 'country'])
X = pd.get_dummies(X, drop_first=True)
y = df['is_churned']

# 3. Train the Final Model
model = HistGradientBoostingClassifier()
model.fit(X, y)

# 4. EXPORT THE ARTIFACTS (This is your key deliverable)
joblib.dump(model, 'final_churn_model.pkl')
joblib.dump(list(X.columns), 'model_features.pkl')

print("Artifacts Created: final_churn_model.pkl and model_features.pkl")