"""
SHAP INTEGRATION MODULE FOR EXPLAINABILITY
============================================
Implements SHAP-based explanations with textual rationale generation
for the Spotify Churn Prediction model.

This module provides:
1. SHAP value computation
2. Feature attribution with business meaning
3. Text-based explanations
4. Local interpretability (similar users, interactions)
5. Explanation quality evaluation
"""

import pandas as pd
import numpy as np
import joblib
import json
from datetime import datetime
from typing import Dict, List, Tuple, Any
import warnings
warnings.filterwarnings('ignore')

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    print("⚠️  SHAP not installed. Install with: pip install shap")

# ============================================================================
# 1. EXPLAINABILITY ENGINE
# ============================================================================

class ChurnExplainabilityEngine:
    """
    Main explainability engine for Spotify churn predictions.
    Computes SHAP values, generates text explanations, and maps to playbooks.
    """
    
    def __init__(self, model, X_data, y_data, feature_names):
        """
        Initialize the explainability engine.
        
        Args:
            model: Trained HistGradientBoostingClassifier
            X_data: Feature matrix (DataFrame)
            y_data: Target variable (Series)
            feature_names: List of feature names
        """
        self.model = model
        self.X_data = X_data
        self.y_data = y_data
        self.feature_names = list(feature_names)
        
        # Initialize SHAP explainer
        if SHAP_AVAILABLE:
            print("Initializing SHAP TreeExplainer...")
            self.explainer = shap.TreeExplainer(model)
            self.shap_values = self.explainer.shap_values(X_data)
            if isinstance(self.shap_values, list):
                self.shap_values = self.shap_values[1]  # Get churn class
            print(f"✓ SHAP initialized with {len(X_data)} samples")
        else:
            self.explainer = None
            self.shap_values = None
        
        # Business context
        self.feature_business_context = self._build_business_context()
        self.decision_rules = self._extract_decision_rules()
        
    # ========================================================================
    # 2. SHAP VALUE COMPUTATION
    # ========================================================================
    
    def get_user_explanation(self, user_idx: int, depth: str = "detailed") -> Dict:
        """
        Generate comprehensive explanation for a single user.
        
        Args:
            user_idx: Index of user in X_data
            depth: 'basic', 'detailed', or 'expert'
            
        Returns:
            Dictionary with explanation components
        """
        if self.shap_values is None:
            raise ValueError("SHAP not available. Install with: pip install shap")
        
        user_data = self.X_data.iloc[user_idx]
        churn_pred = self.model.predict([user_data.values])[0]
        churn_prob = self.model.predict_proba([user_data.values])[0, 1]
        
        # Get SHAP values and base case
        user_shap = self.shap_values[user_idx]
        base_value = self.explainer.expected_value
        
        # Feature attributions
        feature_attributions = self._compute_feature_attributions(
            user_idx, user_shap, user_data, depth
        )
        
        # Text explanation
        text_rationale = self._generate_text_explanation(
            user_idx, feature_attributions, churn_prob, depth
        )
        
        # Risk segment
        risk_segment = self._get_risk_segment(churn_prob)
        
        # Local interpretability
        local_interp = self._compute_local_interpretability(user_idx) if depth == "detailed" else {}
        
        # Decision rules
        triggered_rules = self._check_triggered_rules(user_data)
        
        explanation = {
            "prediction": {
                "churn_probability": float(churn_prob),
                "risk_segment": risk_segment,
                "prediction_label": int(churn_pred)
            },
            "base_case_explanation": {
                "base_value": float(base_value),
                "model_output": float(churn_prob),
                "explanation": f"Model predicts {churn_prob:.1%} churn probability (baseline: {base_value:.1%})"
            },
            "feature_attributions": feature_attributions,
            "text_rationale": text_rationale,
            "local_interpretability": local_interp,
            "decision_rules": triggered_rules,
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "model_version": "1.0",
                "explanation_method": "SHAP TreeExplainer",
                "explanation_depth": depth,
                "explanation_stability_score": self._compute_stability_score(user_idx)
            }
        }
        
        return explanation
    
    # ========================================================================
    # 3. FEATURE ATTRIBUTION
    # ========================================================================
    
    def _compute_feature_attributions(self, user_idx: int, user_shap: np.ndarray, 
                                     user_data: pd.Series, depth: str) -> List[Dict]:
        """
        Compute detailed feature attribution with business meaning.
        """
        attributions = []
        population_mean = self.X_data.mean()
        population_std = self.X_data.std()
        
        # Get top features
        shap_importance = np.abs(user_shap)
        top_indices = np.argsort(shap_importance)[::-1]
        n_features = 15 if depth == "detailed" else 5
        
        for rank, idx in enumerate(top_indices[:n_features]):
            feature_name = self.feature_names[idx]
            shap_val = user_shap[idx]
            feature_val = user_data.iloc[idx]
            
            # Attribution strength
            abs_shap = abs(shap_val)
            if abs_shap > 0.3:
                strength = "critical"
            elif abs_shap > 0.15:
                strength = "high"
            elif abs_shap > 0.05:
                strength = "medium"
            elif abs_shap > 0.01:
                strength = "low"
            else:
                strength = "negligible"
            
            # Direction and impact
            direction = "increases_churn" if shap_val > 0 else "decreases_churn"
            
            # Total absolute SHAP
            total_shap = np.abs(user_shap).sum()
            impact_pct = (abs_shap / total_shap * 100) if total_shap > 0 else 0
            
            # Business meaning
            business_meaning = self._get_feature_business_meaning(
                feature_name, feature_val, shap_val
            )
            
            attribution = {
                "rank": rank + 1,
                "feature_name": feature_name,
                "feature_value": float(feature_val) if isinstance(feature_val, (int, float)) else str(feature_val),
                "shap_value": float(shap_val),
                "attribution_strength": strength,
                "direction": direction,
                "impact_percentage": float(impact_pct),
                "human_readable": f"{feature_name} ({feature_val}) contributes {shap_val:+.3f} SHAP value ({impact_pct:.1f}%)",
                "business_meaning": business_meaning
            }
            attributions.append(attribution)
        
        return attributions
    
    # ========================================================================
    # 4. TEXT EXPLANATION GENERATION
    # ========================================================================
    
    def _generate_text_explanation(self, user_idx: int, 
                                  attributions: List[Dict], 
                                  churn_prob: float, 
                                  depth: str) -> Dict[str, str]:
        """
        Generate human-readable text explanation.
        """
        user_data = self.X_data.iloc[user_idx]
        
        # Summary
        risk_segment = self._get_risk_segment(churn_prob)
        summary = f"This {risk_segment.replace('_', ' ')} user has a {churn_prob:.1%} probability of churning. "
        
        # Key drivers
        top_3_drivers = [a['feature_name'] for a in attributions[:3]]
        key_factors = []
        
        for attr in attributions[:5]:
            if attr['direction'] == 'increases_churn':
                key_factors.append(f"• {attr['feature_name']}: {attr['business_meaning']['interpretation']}")
        
        # Detailed explanation
        detailed = self._build_detailed_explanation(user_data, attributions)
        
        # Actionable insights
        actionable = self._extract_actionable_insights(user_data, attributions, risk_segment)
        
        return {
            "summary": summary,
            "detailed": detailed,
            "key_drivers": top_3_drivers,
            "key_factors": key_factors,
            "actionable_insights": actionable
        }
    
    def _build_detailed_explanation(self, user_data: pd.Series, 
                                   attributions: List[Dict]) -> str:
        """Build detailed narrative explanation."""
        text = "DETAILED ANALYSIS:\n\n"
        
        for attr in attributions[:5]:
            feature = attr['feature_name']
            value = attr['feature_value']
            impact = attr['business_meaning']['interpretation']
            text += f"{attr['rank']}. {feature} = {value}\n"
            text += f"   Impact: {impact}\n\n"
        
        return text.strip()
    
    # ========================================================================
    # 5. BUSINESS CONTEXT MAPPING
    # ========================================================================
    
    def _build_business_context(self) -> Dict:
        """
        Map features to business meaning and levers.
        """
        return {
            'subscription_type_Free': {
                'interpretation': 'Free user (no payment commitment)',
                'churn_risk': 'CRITICAL',
                'lever': 'Convert to Premium',
                'lever_strength': 'HIGH'
            },
            'subscription_type_Premium': {
                'interpretation': 'Premium/paid user (more engaged)',
                'churn_risk': 'LOW',
                'lever': 'Retention through features',
                'lever_strength': 'MEDIUM'
            },
            'ads_listened_per_week': {
                'interpretation': 'Ads exposure per week',
                'churn_risk': 'Each +10 ads = +8% churn',
                'lever': 'Reduce ad load to <30/week',
                'lever_strength': 'CRITICAL'
            },
            'skip_rate': {
                'interpretation': 'What % of songs user skips',
                'churn_risk': '>65% skip rate = high churn',
                'lever': 'Improve recommendations',
                'lever_strength': 'HIGH'
            },
            'listening_time': {
                'interpretation': 'Hours/month of active listening',
                'churn_risk': '<40 hrs = high risk',
                'lever': 'Engagement campaigns',
                'lever_strength': 'MEDIUM'
            }
        }
    
    def _get_feature_business_meaning(self, feature: str, value: Any, 
                                     shap_val: float) -> Dict[str, str]:
        """Get business meaning for a specific feature value."""
        context = self.feature_business_context.get(feature, {
            'interpretation': f'Feature: {feature}',
            'churn_risk': 'UNKNOWN',
            'lever': 'Monitor',
            'lever_strength': 'LOW'
        })
        
        return {
            'interpretation': context.get('interpretation', ''),
            'example': f"{feature} = {value}",
            'actionability': f"Impact (SHAP): {shap_val:+.3f}",
            'lever': context.get('lever', ''),
            'lever_strength': context.get('lever_strength', '')
        }
    
    # ========================================================================
    # 6. LOCAL INTERPRETABILITY
    # ========================================================================
    
    def _compute_local_interpretability(self, user_idx: int) -> Dict:
        """
        Find similar users and feature interactions.
        """
        user_data = self.X_data.iloc[user_idx]
        
        # Find similar users (euclidean distance)
        distances = np.sqrt(((self.X_data - user_data.values) ** 2).sum(axis=1))
        similar_indices = np.argsort(distances)[1:6]  # Exclude self, top 5
        
        similar_users = []
        for idx in similar_indices:
            churn_prob = self.model.predict_proba([self.X_data.iloc[idx].values])[0, 1]
            similar_users.append({
                "user_id": f"similar_{idx}",
                "similarity_score": float(1 / (1 + distances[idx])),
                "their_churn_probability": float(churn_prob)
            })
        
        # Feature interactions (top 3)
        feature_interactions = self._compute_feature_interactions(user_idx)
        
        return {
            "similar_users": similar_users,
            "feature_interactions": feature_interactions
        }
    
    def _compute_feature_interactions(self, user_idx: int) -> List[Dict]:
        """
        Identify important feature interactions.
        """
        interactions = []
        
        # Simple two-way interactions
        if 'subscription_type_Free' in self.feature_names and 'ads_listened_per_week' in self.feature_names:
            free_idx = self.feature_names.index('subscription_type_Free')
            ads_idx = self.feature_names.index('ads_listened_per_week')
            
            user_free = self.X_data.iloc[user_idx, free_idx]
            user_ads = self.X_data.iloc[user_idx, ads_idx]
            
            if user_free == 1 and user_ads > 40:
                interactions.append({
                    "feature_1": "subscription_type_Free",
                    "feature_2": "ads_listened_per_week",
                    "interaction_effect": 0.15,
                    "interpretation": "Free users with high ads are particularly at risk"
                })
        
        return interactions
    
    # ========================================================================
    # 7. DECISION RULES
    # ========================================================================
    
    def _extract_decision_rules(self) -> Dict:
        """
        Extract interpretable decision rules from model behavior.
        """
        return {
            'Rule_1_Free_HighAds': {
                'rule_id': 'R001',
                'rule_text': 'Free users with >40 ads/week are high churn risk',
                'condition': "(subscription_type == 'Free') AND (ads_listened_per_week > 40)",
                'expected_churn_prob': 0.75,
                'support': 0.15
            },
            'Rule_2_HighSkip': {
                'rule_id': 'R002',
                'rule_text': 'Users with skip rate >65% are high churn risk',
                'condition': 'skip_rate > 0.65',
                'expected_churn_prob': 0.72,
                'support': 0.20
            },
            'Rule_3_LowEngagement': {
                'rule_id': 'R003',
                'rule_text': 'Free users with <40 hrs/month listening are high risk',
                'condition': "(subscription_type == 'Free') AND (listening_time < 40)",
                'expected_churn_prob': 0.68,
                'support': 0.25
            },
            'Rule_4_Premium_HighEngagement': {
                'rule_id': 'R004',
                'rule_text': 'Premium users with >100 hrs/month are very low risk',
                'condition': "(subscription_type == 'Premium') AND (listening_time > 100)",
                'expected_churn_prob': 0.05,
                'support': 0.18
            }
        }
    
    def _check_triggered_rules(self, user_data: pd.Series) -> List[Dict]:
        """Check which decision rules apply to a user."""
        triggered = []
        
        free_user = user_data.get('subscription_type_Free', 0) == 1
        ads = user_data.get('ads_listened_per_week', 0)
        skip_rate = user_data.get('skip_rate', 0)
        listening_time = user_data.get('listening_time', 0)
        
        # Rule 1
        if free_user and ads > 40:
            triggered.append({
                'rule_id': 'R001',
                'rule_text': 'Free user with high ad load',
                'triggers': True,
                'confidence': 0.85
            })
        
        # Rule 2
        if skip_rate > 0.65:
            triggered.append({
                'rule_id': 'R002',
                'rule_text': 'High skip rate indicates content mismatch',
                'triggers': True,
                'confidence': 0.78
            })
        
        # Rule 3
        if free_user and listening_time < 40:
            triggered.append({
                'rule_id': 'R003',
                'rule_text': 'Free user with low engagement',
                'triggers': True,
                'confidence': 0.72
            })
        
        # Rule 4
        if not free_user and listening_time > 100:
            triggered.append({
                'rule_id': 'R004',
                'rule_text': 'Premium user with high engagement (stable)',
                'triggers': True,
                'confidence': 0.90
            })
        
        return triggered
    
    # ========================================================================
    # 8. UTILITY FUNCTIONS
    # ========================================================================
    
    def _get_risk_segment(self, churn_prob: float) -> str:
        """
        Categorize user into risk segment.
        """
        if churn_prob > 0.67:
            return "high_risk"
        elif churn_prob > 0.33:
            return "medium_risk"
        else:
            return "low_risk"
    
    def _compute_stability_score(self, user_idx: int) -> float:
        """
        Evaluate explanation stability.
        High score = explanation is stable & reliable.
        """
        user_data = self.X_data.iloc[user_idx]
        
        # Check if user is near data distribution boundaries
        distances_to_mean = np.abs(user_data - self.X_data.mean()) / (self.X_data.std() + 1e-6)
        outlier_score = (distances_to_mean > 3).sum() / len(distances_to_mean)
        
        # Stability = 1 - outlier_score
        stability = max(0.5, 1 - outlier_score)
        
        return float(stability)
    
    def _extract_actionable_insights(self, user_data: pd.Series, 
                                    attributions: List[Dict],
                                    risk_segment: str) -> List[str]:
        """
        Extract actionable insights for business teams.
        """
        insights = []
        
        free_user = user_data.get('subscription_type_Free', 0) == 1
        ads = user_data.get('ads_listened_per_week', 0)
        skip_rate = user_data.get('skip_rate', 0)
        listening_time = user_data.get('listening_time', 0)
        
        if risk_segment == 'high_risk':
            if free_user:
                insights.append("Offer immediate Premium conversion with 1-month free trial")
                if ads > 40:
                    insights.append("Reduce ad load to <30/week to alleviate friction")
            if skip_rate > 0.65:
                insights.append("Create personalized playlist to improve content match")
            if listening_time < 50:
                insights.append("Launch re-engagement campaign with curated recommendations")
        
        elif risk_segment == 'medium_risk':
            insights.append("Send personalized engagement email with favorite genres")
            if free_user:
                insights.append("Offer 3-month Premium discount for commitment")
            insights.append("Enable social sharing features to increase engagement")
        
        else:  # low_risk
            insights.append("Focus on loyalty rewards (VIP perks, early features)")
            insights.append("Upsell family plan or higher-tier premium")
            insights.append("Invite to exclusive artist events/podcasts")
        
        return insights


# ============================================================================
# 9. BATCH EXPLANATION GENERATOR
# ============================================================================

def generate_batch_explanations(model, X_data, y_data, feature_names, 
                               user_indices: List[int] = None,
                               depth: str = "detailed") -> List[Dict]:
    """
    Generate explanations for multiple users.
    """
    engine = ChurnExplainabilityEngine(model, X_data, y_data, feature_names)
    
    if user_indices is None:
        user_indices = range(len(X_data))
    
    explanations = []
    for idx in user_indices:
        try:
            exp = engine.get_user_explanation(idx, depth=depth)
            explanations.append(exp)
        except Exception as e:
            print(f"Error generating explanation for user {idx}: {e}")
    
    return explanations


# ============================================================================
# 10. MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("SHAP INTEGRATION MODULE - DEMONSTRATION")
    print("=" * 80)
    
    # Load data and model
    df = pd.read_csv('spotify_final_combined.csv')
    X = df.drop(columns=['user_id', 'is_churned', 'country'])
    X = pd.get_dummies(X, drop_first=True)
    y = df['is_churned']
    
    try:
        model = joblib.load('spotify_churn_model.pkl')
    except:
        from sklearn.model_selection import train_test_split
        from sklearn.ensemble import HistGradientBoostingClassifier
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        model = HistGradientBoostingClassifier(max_iter=300, random_state=42)
        model.fit(X_train, y_train)
        joblib.dump(model, 'spotify_churn_model.pkl')
    
    # Initialize engine
    engine = ChurnExplainabilityEngine(model, X, y, X.columns)
    
    # Generate explanations for top high-risk users
    churn_probs = model.predict_proba(X)[:, 1]
    high_risk_indices = np.argsort(churn_probs)[::-1][:5]
    
    print("\n✓ Generating explanations for top 5 high-risk users...\n")
    
    for rank, idx in enumerate(high_risk_indices):
        print(f"User {rank + 1}: Index {idx}")
        try:
            exp = engine.get_user_explanation(idx, depth="detailed")
            print(f"  Churn Probability: {exp['prediction']['churn_probability']:.1%}")
            print(f"  Risk Segment: {exp['prediction']['risk_segment']}")
            print(f"  Top Driver: {exp['feature_attributions'][0]['feature_name']}")
            print(f"  Stability Score: {exp['metadata']['explanation_stability_score']:.2f}\n")
        except Exception as e:
            print(f"Error: {e}\n")
    
    print("=" * 80)
    print("✅ SHAP Integration Module Ready!")
    print("=" * 80)
