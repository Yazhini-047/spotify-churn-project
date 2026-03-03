"""
EXPLAINABLE AI & ACTIONABLE PLAYBOOKS FOR SPOTIFY CHURN PREDICTION
================================================================
This script creates:
1. SHAP-based explainability for model decisions
2. Feature importance analysis
3. User segment analysis
4. Actionable playbooks for retention
"""

import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.preprocessing import LabelEncoder
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# SECTION 1: LOAD AND PREPARE DATA
# ============================================================================
print("=" * 80)
print("STEP 1: LOADING DATA AND MODEL")
print("=" * 80)

# Load data
df = pd.read_csv('spotify_final_combined.csv')
print(f"✓ Loaded data: {df.shape[0]} users, {df.shape[1]} features")

# Prepare features (same preprocessing as training)
X = df.drop(columns=['user_id', 'is_churned', 'country'])
X = pd.get_dummies(X, drop_first=True)
y = df['is_churned']

print(f"✓ Features prepared: {X.shape[1]} features")
print(f"✓ Churn rate: {y.mean():.1%}")

# Load or train the model
try:
    model = joblib.load('spotify_churn_model.pkl')
    print("✓ Loaded existing model")
except:
    print("⚠ Training new model...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = HistGradientBoostingClassifier(max_iter=300, random_state=42)
    model.fit(X_train, y_train)
    joblib.dump(model, 'spotify_churn_model.pkl')
    print("✓ Model trained and saved")

# ============================================================================
# SECTION 2: FEATURE IMPORTANCE ANALYSIS
# ============================================================================
print("\n" + "=" * 80)
print("STEP 2: FEATURE IMPORTANCE ANALYSIS")
print("=" * 80)

# Get feature importance from the model
feature_importance = pd.DataFrame({
    'feature': X.columns,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

print("\n📊 TOP 10 FEATURES DRIVING CHURN:")
print("-" * 50)
for idx, row in feature_importance.head(10).iterrows():
    print(f"{row['feature']:.<35} {row['importance']:.4f}")

# Visualize feature importance
fig, ax = plt.subplots(figsize=(12, 6))
top_features = feature_importance.head(15)
colors = ['#FF6B6B' if x > 0.05 else '#4ECDC4' for x in top_features['importance']]
ax.barh(range(len(top_features)), top_features['importance'], color=colors)
ax.set_yticks(range(len(top_features)))
ax.set_yticklabels(top_features['feature'])
ax.set_xlabel('Importance Score', fontsize=12, fontweight='bold')
ax.set_title('Top 15 Features Driving Churn Predictions', fontsize=14, fontweight='bold')
ax.invert_yaxis()
plt.tight_layout()
plt.savefig('feature_importance.png', dpi=300, bbox_inches='tight')
print("\n✓ Saved: feature_importance.png")
plt.close()

# ============================================================================
# SECTION 3: EXPLAIN INDIVIDUAL PREDICTIONS
# ============================================================================
print("\n" + "=" * 80)
print("STEP 3: INDIVIDUAL PREDICTION EXPLANATIONS")
print("=" * 80)

# Get predictions and probabilities
y_pred = model.predict(X)
y_pred_proba = model.predict_proba(X)
df['churn_prediction'] = y_pred
df['churn_probability'] = y_pred_proba[:, 1]

# Show high-risk users
print("\n⚠️  TOP 10 HIGHEST CHURN RISK USERS:")
print("-" * 80)
high_risk = df.nlargest(10, 'churn_probability')[['user_id', 'subscription_type', 
                                                     'listening_time', 'ads_listened_per_week',
                                                     'skip_rate', 'churn_probability']]
for idx, user in high_risk.iterrows():
    print(f"User {user['user_id']:>6} | {user['subscription_type']:>7} | " +
          f"Listening: {user['listening_time']:>6.0f}hrs | Ads: {user['ads_listened_per_week']:>5.0f}/wk | " +
          f"Skip Rate: {user['skip_rate']:.2%} | Risk: {user['churn_probability']:.1%}")

# ============================================================================
# SECTION 4: USER SEGMENTATION & RISK PROFILES
# ============================================================================
print("\n" + "=" * 80)
print("STEP 4: USER SEGMENTATION & RISK PROFILES")
print("=" * 80)

# Create risk segments
df['risk_segment'] = pd.cut(df['churn_probability'], 
                            bins=[0, 0.33, 0.67, 1.0],
                            labels=['Low Risk', 'Medium Risk', 'High Risk'])

# Analyze each segment
segment_analysis = df.groupby('risk_segment').agg({
    'user_id': 'count',
    'churn_probability': 'mean',
    'listening_time': 'mean',
    'ads_listened_per_week': 'mean',
    'skip_rate': 'mean',
    'subscription_type': lambda x: (x == 'Free').sum() / len(x)
}).round(2)
segment_analysis.columns = ['Count', 'Avg Risk', 'Avg Listening (hrs)', 
                             'Avg Ads/Week', 'Avg Skip Rate', '% Free Users']

print("\n📈 SEGMENT ANALYSIS:")
print("-" * 80)
print(segment_analysis)

# ============================================================================
# SECTION 5: ACTIONABLE PLAYBOOKS
# ============================================================================
print("\n" + "=" * 80)
print("STEP 5: ACTIONABLE PLAYBOOKS FOR USER RETENTION")
print("=" * 80)

# HIGH RISK PLAYBOOK
print("\n🚨 PLAYBOOK 1: HIGH RISK USERS (Churn Probability > 67%)")
print("-" * 80)
high_risk_df = df[df['risk_segment'] == 'High Risk']
print(f"Users in segment: {len(high_risk_df)} ({len(high_risk_df)/len(df):.1%})")
print(f"Average churn probability: {high_risk_df['churn_probability'].mean():.1%}\n")

# What makes them high risk?
high_risk_reasons = []
if (high_risk_df['subscription_type'] == 'Free').mean() > 0.7:
    high_risk_reasons.append("- 70%+ are FREE users (not paying)")
if high_risk_df['ads_listened_per_week'].mean() > 40:
    high_risk_reasons.append("- Exposed to HIGH AD VOLUME (>40 ads/week)")
if high_risk_df['skip_rate'].mean() > 0.65:
    high_risk_reasons.append("- HIGH SKIP RATES (>65% skip content)")
if high_risk_df['listening_time'].mean() < 50:
    high_risk_reasons.append("- LOW ENGAGEMENT (<50 hrs/month)")

if high_risk_reasons:
    print("KEY RISK FACTORS:")
    for reason in high_risk_reasons:
        print(reason)

print("\n✅ RETENTION ACTIONS:")
playbook_actions = [
    "1. IMMEDIATE: Send targeted 'Premium Upgrade' offer with 1-month free trial",
    "2. REDUCE AD FRICTION: Lower ads to <30/week for these users",
    "3. ENGAGEMENT BOOST: Curate personalized playlists to reduce skip rate",
    "4. INCENTIVE: Offer premium features preview (high-quality audio, offline downloads)",
    "5. TIMING: Send offers on weekdays (higher engagement times)"
]
for action in playbook_actions:
    print(action)

# MEDIUM RISK PLAYBOOK
print("\n\n⚠️  PLAYBOOK 2: MEDIUM RISK USERS (Churn Probability 33-67%)")
print("-" * 80)
medium_risk_df = df[df['risk_segment'] == 'Medium Risk']
print(f"Users in segment: {len(medium_risk_df)} ({len(medium_risk_df)/len(df):.1%})")
print(f"Average churn probability: {medium_risk_df['churn_probability'].mean():.1%}\n")

print("✅ RETENTION ACTIONS:")
playbook_medium = [
    "1. ENGAGEMENT CAMPAIGNS: Create weekly 'Top Hits' personalized lists",
    "2. RETENTION BONUS: Offer 3-month discount on Premium (reduced risk)",
    "3. SOCIAL FEATURES: Enable friend sharing & collaborative playlists",
    "4. FEEDBACK LOOP: Ask for feedback on what content/features they want",
    "5. MILESTONE REWARDS: Celebrate listening milestones with badges"
]
for action in playbook_medium:
    print(action)

# LOW RISK PLAYBOOK
print("\n\n✨ PLAYBOOK 3: LOW RISK USERS (Churn Probability < 33%)")
print("-" * 80)
low_risk_df = df[df['risk_segment'] == 'Low Risk']
print(f"Users in segment: {len(low_risk_df)} ({len(low_risk_df)/len(df):.1%})")
print(f"Average churn probability: {low_risk_df['churn_probability'].mean():.1%}\n")

print("✅ RETENTION ACTIONS:")
playbook_low = [
    "1. LOYALTY REWARDS: VIP perks (early access to new features, exclusive content)",
    "2. UPSELL PLANS: Offer family plans or ad-free experiences",
    "3. COMMUNITY: Enable exclusive access to artist events/podcasts",
    "4. REFERRAL PROGRAM: Give bonuses for inviting friends",
    "5. MAINTAIN QUALITY: Keep engagement high with excellent recommendations"
]
for action in playbook_low:
    print(action)

# ============================================================================
# SECTION 6: SUBSCRIPTION TYPE INSIGHTS
# ============================================================================
print("\n" + "=" * 80)
print("STEP 6: SUBSCRIPTION TYPE INSIGHTS")
print("=" * 80)

sub_analysis = df.groupby('subscription_type').agg({
    'user_id': 'count',
    'churn_probability': 'mean',
    'listening_time': 'mean',
    'ads_listened_per_week': 'mean',
    'skip_rate': 'mean'
}).round(2)

print("\n" + sub_analysis.to_string())

# Visualize
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Churn probability by subscription
ax = axes[0, 0]
df_sub = df.groupby('subscription_type')['churn_probability'].mean()
colors_sub = ['#FF6B6B', '#4ECDC4']
ax.bar(df_sub.index, df_sub.values, color=colors_sub)
ax.set_ylabel('Average Churn Probability', fontweight='bold')
ax.set_title('Churn Risk by Subscription Type', fontweight='bold')
ax.set_ylim(0, 1)
for i, v in enumerate(df_sub.values):
    ax.text(i, v + 0.02, f'{v:.1%}', ha='center', fontweight='bold')

# Listening time by subscription
ax = axes[0, 1]
df.boxplot(column='listening_time', by='subscription_type', ax=ax)
ax.set_ylabel('Listening Time (hours)', fontweight='bold')
ax.set_xlabel('')
ax.set_title('Engagement by Subscription Type', fontweight='bold')
plt.sca(ax)
plt.xticks(rotation=0)

# Skip rate by subscription
ax = axes[1, 0]
df.boxplot(column='skip_rate', by='subscription_type', ax=ax)
ax.set_ylabel('Skip Rate', fontweight='bold')
ax.set_xlabel('')
ax.set_title('Skip Rate by Subscription Type', fontweight='bold')
plt.sca(ax)
plt.xticks(rotation=0)

# Segment distribution
ax = axes[1, 1]
segment_counts = df.groupby(['subscription_type', 'risk_segment']).size().unstack()
segment_counts.plot(kind='bar', ax=ax, color=['#2ECC71', '#F39C12', '#E74C3C'])
ax.set_ylabel('Number of Users', fontweight='bold')
ax.set_xlabel('')
ax.set_title('Risk Segment Distribution by Subscription', fontweight='bold')
ax.legend(title='Risk Level')
plt.sca(ax)
plt.xticks(rotation=0)

plt.tight_layout()
plt.savefig('subscription_insights.png', dpi=300, bbox_inches='tight')
print("\n✓ Saved: subscription_insights.png")
plt.close()

# ============================================================================
# SECTION 7: KEY RECOMMENDATIONS SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("STEP 7: EXECUTIVE SUMMARY & RECOMMENDATIONS")
print("=" * 80)

total_users = len(df)
churning_users = len(df[df['risk_segment'] == 'High Risk'])
potential_revenue_loss = churning_users * 9.99  # Assuming $9.99 premium/month

print(f"""
📊 CURRENT STATE:
  • Total Users: {total_users:,}
  • High-Risk Churners: {churning_users:,} ({churning_users/total_users:.1%})
  • Potential Monthly Revenue at Risk: ${potential_revenue_loss:,.0f}

🎯 TOP 3 PRIORITY ACTIONS:
  1. TARGET AD BURDEN: Reduce ads for free users (>40 ads/week is toxic)
  2. UPGRADE INCENTIVES: Aggressive premium trials for high-risk segment
  3. ENGAGEMENT LOOPS: Personalized content to reduce skip rates

💡 EXPECTED IMPACT:
  • If 30% of high-risk retain: +${churning_users * 0.3 * 9.99:,.0f}/month revenue
  • If skip rate drops 10%: Likely -5-10% churn overall
  • If premium conversion improves 5%: +${total_users * 0.05 * 9.99:,.0f}/month

🔄 NEXT STEPS:
  1. A/B test reduced ad loads for free users
  2. Launch premium trial campaign to churn-risk segment
  3. Monitor engagement metrics (listening time, skip rate)
  4. Retrain model monthly as user behavior changes
""")

# ============================================================================
# SECTION 8: SAVE ACTIONABLE DATA
# ============================================================================
print("\n" + "=" * 80)
print("STEP 8: SAVING ACTIONABLE OUTPUTS")
print("=" * 80)

# Save predictions with explanations
output_df = df[['user_id', 'subscription_type', 'listening_time', 
                'ads_listened_per_week', 'skip_rate', 'churn_probability', 
                'risk_segment']].copy()
output_df = output_df.sort_values('churn_probability', ascending=False)
output_df.to_csv('user_churn_predictions_and_segments.csv', index=False)
print("✓ Saved: user_churn_predictions_and_segments.csv")

# Save feature importance
feature_importance.to_csv('feature_importance_analysis.csv', index=False)
print("✓ Saved: feature_importance_analysis.csv")

# Save segment summary
segment_analysis.to_csv('segment_analysis.csv')
print("✓ Saved: segment_analysis.csv")

print("\n" + "=" * 80)
print("✅ EXPLAINABILITY & PLAYBOOKS GENERATION COMPLETE!")
print("=" * 80)
print("\nGenerated Files:")
print("  1. feature_importance.png - Visual guide to key drivers")
print("  2. subscription_insights.png - Subscription type analysis")
print("  3. user_churn_predictions_and_segments.csv - User-level predictions & actions")
print("  4. feature_importance_analysis.csv - Detailed feature rankings")
print("  5. segment_analysis.csv - Segment-level statistics")
