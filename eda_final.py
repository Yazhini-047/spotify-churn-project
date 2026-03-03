import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 1. SETUP & STYLE
# This ensures the charts look modern and professional
sns.set_theme(style="whitegrid")
plt.rcParams['figure.figsize'] = (10, 6)

# 2. LOAD DATA
try:
    df = pd.read_csv('spotify_final_combined.csv')
    print("Dataset loaded successfully!")
except FileNotFoundError:
    print("Error: 'spotify_final_combined.csv' not found. Please run your data creation script first.")
    exit()

# --- EDA TASK 1: CHURN DISTRIBUTION ---
# This shows if the data is balanced or imbalanced
plt.figure(figsize=(6, 4))
sns.countplot(x='is_churned', data=df, palette='viridis')
plt.title('Figure 1: Distribution of Churn (0=Stay, 1=Leave)', fontsize=14)
plt.savefig('eda_churn_balance.png')
print("Generated: eda_churn_balance.png")

# --- EDA TASK 2: CORRELATION HEATMAP ---
# This shows which features have the strongest link to Churn
plt.figure(figsize=(10, 8))
# Drop non-numeric for correlation
numeric_df = df.select_dtypes(include=['float64', 'int64']).drop(columns=['user_id'], errors='ignore')
correlation = numeric_df.corr()
sns.heatmap(correlation, annot=True, cmap='coolwarm', fmt='.2f', linewidths=0.5)
plt.title('Figure 2: Feature Correlation Heatmap', fontsize=14)
plt.tight_layout()
plt.savefig('eda_heatmap.png')
print("Generated: eda_heatmap.png")

# --- EDA TASK 3: SUBSCRIPTION TYPE VS CHURN ---
# Shows if certain plans are more likely to cancel
plt.figure(figsize=(8, 5))
sns.countplot(x='subscription_type', hue='is_churned', data=df, palette='Set2')
plt.title('Figure 3: Churn Rate by Subscription Type', fontsize=14)
plt.savefig('eda_subscription_analysis.png')
print("Generated: eda_subscription_analysis.png")

# --- EDA TASK 4: SKIP RATE & AD BEHAVIOR ---
# This scatter plot visualizes the 'Churn Zone'
plt.figure(figsize=(8, 6))
sns.scatterplot(x='ads_listened_per_week', y='skip_rate', hue='is_churned', data=df, alpha=0.5)
plt.title('Figure 4: Ads vs Skip Rate (Churn Decision Boundary)', fontsize=14)
plt.savefig('eda_behavior_scatter.png')
print("Generated: eda_behavior_scatter.png")

# --- EDA TASK 5: LISTENING TIME BOXPLOT ---
# Compares the active time of churners vs non-churners
plt.figure(figsize=(6, 5))
sns.boxplot(x='is_churned', y='listening_time', data=df, palette='pastel')
plt.title('Figure 5: Listening Time for Stayed vs Churned Users', fontsize=14)
plt.savefig('eda_listening_boxplot.png')
print("Generated: eda_listening_boxplot.png")

print("\n--- EDA PROCESS COMPLETE ---")
print("All charts have been saved to your folder as .png files.")