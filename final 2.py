import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import HistGradientBoostingClassifier 
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, accuracy_score
from sklearn.utils.class_weight import compute_sample_weight

# 1. LOAD DATA
print("--- STEP 1: LOADING DATA ---")
df = pd.read_csv('spotify dataset.csv')

# 2. FEATURE ENGINEERING
# We create new metrics to help the model find patterns
df['ad_stress'] = df['ads_listened_per_week'] / (df['listening_time'] + 1)
df['skip_intensity'] = df['skip_rate'] / (df['songs_played_per_day'] + 1)

# 3. PREPROCESS
# Removing country and user_id because they add random noise
X = df.drop(columns=['user_id', 'is_churned', 'country'])
X = pd.get_dummies(X, drop_first=True)
y = df['is_churned']

# 4. SPLIT
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# 5. SCALE
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# 6. TRAIN (HistGradientBoosting is powerful and built-in)
print("--- STEP 2: TRAINING MODEL ---")

# We use balanced weights to help the model identify churners better
weights = compute_sample_weight(class_weight='balanced', y=y_train)

model = HistGradientBoostingClassifier(
    max_iter=1000, 
    learning_rate=0.01, 
    max_depth=10, 
    random_state=42
)

model.fit(X_train_scaled, y_train, sample_weight=weights)

# 7. EVALUATE
y_pred = model.predict(X_test_scaled)
acc = accuracy_score(y_test, y_pred)

print("\n--- FINAL RESULTS ---")
print(f"Accuracy Score: {acc:.2%}")
print("\nDetailed Report:")
print(classification_report(y_test, y_pred))

# 8. SAVE
joblib.dump(model, 'spotify_churn_model.pkl')
joblib.dump(scaler, 'scaler.pkl')
joblib.dump(list(X.columns), 'model_columns.pkl')

print("\nDONE: Model saved to disk.")
