import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, ConfusionMatrixDisplay
from imblearn.over_sampling import SMOTE

# 1. Load Data
df = pd.read_csv('spotify_data.csv')

# 2. Preprocess
# Drop ID and handle categorical text data
X = df.drop(columns=['user_id', 'is_churned'])
X = pd.get_dummies(X, drop_first=True)
y = df['is_churned']

# 3. Split & Balance
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

print("Balancing data... please wait.")
smote = SMOTE(random_state=42)
X_res, y_res = smote.fit_resample(X_train, y_train)

# 4. Train
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_res, y_res)

# 5. Evaluate
y_pred = model.predict(X_test)
print("\n--- IMPROVED MODEL RESULTS ---")
print(classification_report(y_test, y_pred))

# 6. Visualize the "Why" (Feature Importance)
feat_importances = pd.Series(model.feature_importances_, index=X.columns)
feat_importances.nlargest(10).plot(kind='barh', color='skyblue')
plt.title('Top Factors Driving Spotify Churn')
plt.show()

import matplotlib.pyplot as plt
import pandas as pd

# 1. Get the importance scores from the model
importances = model.feature_importances_

# 2. Match them with the column names
feature_names = X.columns
feature_importance_df = pd.DataFrame({'Feature': feature_names, 'Importance': importances})

# 3. Sort them so the most important is at the top
feature_importance_df = feature_importance_df.sort_values(by='Importance', ascending=False)

# 4. Create the plot
plt.figure(figsize=(10, 6))
plt.barh(feature_importance_df['Feature'].head(10), feature_importance_df['Importance'].head(10), color='green')
plt.xlabel('Importance Score')
plt.title('Why are users leaving? (Top 10 Features)')
plt.gca().invert_yaxis() # Highest importance on top
plt.show()

import joblib

# Save the model
joblib.dump(model, 'spotify_churn_model.pkl')

# Save the column names (important to ensure new data matches exactly)
model_columns = list(X.columns)
joblib.dump(model_columns, 'model_columns.pkl')

print("✅ Success: Model and Column metadata saved to disk!")