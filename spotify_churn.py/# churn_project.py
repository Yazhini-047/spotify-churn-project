import pandas as pd

# Load your specific file
df = pd.read_csv('spotify dataset.csv') # Ensure the filename matches yours!

print("--- Column Names ---")
print(df.columns.tolist())

print("\n--- Data Types ---")
print(df.dtypes)

print("\n--- Missing Values ---")
print(df.isnull().sum())
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, ConfusionMatrixDisplay

# 1. LOAD
df = pd.read_csv('spotify dataset.csv')

# 2. PREPROCESS 
# Identify your target column (e.g., 'churn', 'label', or 'is_retired')
# For this example, I'll assume it's called 'target'
target_col = 'is_churned' 

# Convert text columns to numbers (One-Hot Encoding)
df_encoded = pd.get_dummies(df, drop_first=True)

# 3. SPLIT
X = df_encoded.drop(columns=[target_col])
y = df_encoded[target_col]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 4. TRAIN
model = RandomForestClassifier(random_state=42)
model.fit(X_train, y_train)

# 5. EVALUATE & VISUALIZE
print("\nModel Performance:")
print(classification_report(y_test, model.predict(X_test)))

# Show Feature Importance (The "Why")
importances = pd.Series(model.feature_importances_, index=X.columns)
importances.nlargest(10).plot(kind='barh')
plt.title("Top 10 Factors Leading to Churn")
plt.show()
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from imblearn.over_sampling import SMOTE # New import

# 1. Load and Encode
df = pd.read_csv('spotify_data.csv')
# Dropping user_id as it's just a label
df = df.drop(columns=['user_id'])
df_encoded = pd.get_dummies(df, drop_first=True)

# 2. Split
X = df_encoded.drop(columns=['is_churned'])
y = df_encoded['is_churned']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# 3. FIX THE BALANCE (SMOTE)
smote = SMOTE(random_state=42)
X_train_res, y_train_res = smote.fit_resample(X_train, y_train)

# 4. TRAIN with balanced data
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train_res, y_train_res)

# 5. EVALUATE
print("\n--- Improved Model Performance (Balanced) ---")
print(classification_report(y_test, model.predict(X_test)))