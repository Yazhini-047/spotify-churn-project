"""
SPOTIFY CHURN PREDICTION - STANDALONE FRONTEND
===============================================
Fully independent Streamlit dashboard.
No FastAPI. No localhost. No backend required.
Run: streamlit run frontend_dashboard.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import uuid
import os
import joblib
from typing import Dict, Any, List, Optional

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="Spotify Churn Prediction",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CUSTOM CSS
# ============================================================================
st.markdown("""
<style>
    .main { padding: 0; }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .risk-high   { color: #ff3333; font-weight: bold; }
    .risk-medium { color: #ff9500; font-weight: bold; }
    .risk-low    { color: #00cc66; font-weight: bold; }
    .header-title {
        color: #1DB954;
        font-size: 2.5em;
        font-weight: bold;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# MODEL LOADING
# ============================================================================
@st.cache_resource
def load_model():
    for path in ["model.joblib", "churn_model.pkl", "model.pkl"]:
        if os.path.exists(path):
            try:
                return joblib.load(path)
            except Exception as e:
                st.warning(f"Found {path} but could not load: {e}")
    return None

@st.cache_resource
def load_explainer(_model):
    if _model is None:
        return None
    try:
        import shap
        return shap.TreeExplainer(_model)
    except Exception:
        try:
            import shap
            return shap.Explainer(_model)
        except Exception:
            return None

# ============================================================================
# FEATURE COLUMNS — update if your model uses different columns
# ============================================================================
FEATURE_COLUMNS = [
    "subscription_type",
    "num_sessions",
    "monthly_stream_hours",
    "account_age_days",
    "playlist_diversity",
]

FEATURE_DISPLAY_NAMES = {
    "subscription_type":    "Subscription Type",
    "num_sessions":         "Monthly Sessions",
    "monthly_stream_hours": "Monthly Stream Hours",
    "account_age_days":     "Account Age (days)",
    "playlist_diversity":   "Playlist Diversity",
}

def build_feature_dataframe(features: Dict[str, Any]) -> pd.DataFrame:
    encoded = features.copy()
    encoded["subscription_type"] = 0 if features["subscription_type"] == "Free" else 1
    df = pd.DataFrame([encoded])
    return df[[c for c in FEATURE_COLUMNS if c in df.columns]]

# ============================================================================
# PREDICTION ENGINE
# ============================================================================
def make_prediction(model, user_id: str, features: Dict[str, Any]) -> Optional[Dict]:
    try:
        df         = build_feature_dataframe(features)
        churn_prob = float(model.predict_proba(df)[0][1])
        label      = int(model.predict(df)[0])
        confidence = max(churn_prob, 1 - churn_prob)
        risk_segment = (
            "low_risk"    if churn_prob < 0.33 else
            "medium_risk" if churn_prob < 0.67 else
            "high_risk"
        )
        return {
            "user_id":           user_id,
            "prediction_id":     str(uuid.uuid4()),
            "churn_probability": churn_prob,
            "risk_segment":      risk_segment,
            "prediction_label":  label,
            "confidence_score":  confidence,
            "timestamp":         datetime.utcnow().isoformat(),
            "model_version":     "1.0",
            "features":          features,
        }
    except Exception as e:
        st.error(f"Prediction error: {e}")
        return None

# ============================================================================
# SHAP EXPLANATION ENGINE
# ============================================================================
def make_explanation(explainer, prediction: Dict) -> Optional[Dict]:
    try:
        import shap
        features  = prediction["features"]
        df        = build_feature_dataframe(features)
        shap_vals = explainer.shap_values(df)
        sv        = shap_vals[1][0] if isinstance(shap_vals, list) else shap_vals[0]

        feature_names = [c for c in FEATURE_COLUMNS if c in df.columns]
        total_abs     = sum(abs(v) for v in sv) or 1.0
        attributions  = []

        for fname, val in zip(feature_names, sv):
            impact_pct = round((val / total_abs) * 100, 1)
            direction  = "increases_churn" if val > 0.01 else "decreases_churn" if val < -0.01 else "neutral"
            display    = FEATURE_DISPLAY_NAMES.get(fname, fname)
            raw_val    = features.get(fname, df[fname].values[0])
            attributions.append({
                "feature_name":      display,
                "feature_value":     raw_val,
                "shap_value":        round(float(val), 4),
                "direction":         direction,
                "impact_percentage": impact_pct,
                "human_readable":    f"{display} = {raw_val} {'increases' if val > 0 else 'decreases'} churn risk by {abs(impact_pct):.1f}%",
            })

        attributions.sort(key=lambda x: abs(x["impact_percentage"]), reverse=True)
        key_drivers = [a["feature_name"] for a in attributions[:3]]
        churn_prob  = prediction["churn_probability"]
        summary     = (
            f"User shows {'high' if churn_prob > 0.67 else 'moderate' if churn_prob > 0.33 else 'low'} "
            f"churn risk ({churn_prob*100:.1f}%). Key factors: {', '.join(key_drivers)}."
        )
        return {
            "summary":              summary,
            "key_drivers":          key_drivers,
            "feature_attributions": attributions,
            "actionable_insights":  _build_insights(attributions, features, prediction["risk_segment"]),
            "explanation_method":   "SHAP TreeExplainer",
        }
    except Exception as e:
        st.error(f"Explanation error: {e}")
        return None

def _build_insights(attributions: List[Dict], features: Dict, risk_segment: str) -> List[str]:
    insights = []
    for attr in attributions[:4]:
        fname, direction = attr["feature_name"], attr["direction"]
        if "Subscription" in fname and direction == "increases_churn":
            insights.append("🎯 Offer a discounted Premium trial — free users churn more.")
        elif "Sessions" in fname and direction == "increases_churn":
            insights.append("📱 Re-engage with push notifications — low session count detected.")
        elif "Stream Hours" in fname and direction == "increases_churn":
            insights.append("🎵 Promote curated playlists to boost listening time.")
        elif "Account Age" in fname and direction == "increases_churn":
            insights.append("🆕 New user — trigger onboarding flow with feature discovery tips.")
        elif "Diversity" in fname and direction == "increases_churn":
            insights.append("🌍 Recommend genre exploration to increase playlist diversity.")
        elif direction == "decreases_churn":
            insights.append(f"✅ {fname} is positively contributing — keep this engagement high.")
    if not insights:
        if risk_segment == "high_risk":
            insights = ["🚨 High churn risk — trigger immediate retention playbook.",
                        "💰 Offer a personalised discount within 24 hours.",
                        "📧 Send a re-engagement email with curated content."]
        elif risk_segment == "medium_risk":
            insights = ["📊 Monitor engagement closely over the next 7 days.",
                        "🎁 Consider a loyalty reward or exclusive content offer."]
        else:
            insights = ["✅ User appears healthy — continue standard engagement.",
                        "📈 Great time to upsell Premium features."]
    return insights

# ============================================================================
# PLAYBOOK ENGINE
# ============================================================================
PLAYBOOKS = {
    "high_risk": [
        {
            "playbook_id": "PB_HIGH_RISK_CONVERT",
            "name":        "High-Risk User Conversion Blitz",
            "priority":    5,
            "description": "Immediate multi-channel intervention for users likely to churn.",
            "actions": [
                {"step": 1, "channel": "Email",  "action": "Send 30-day Premium free trial offer"},
                {"step": 2, "channel": "In-App", "action": "Show personalised discount banner"},
                {"step": 3, "channel": "Push",   "action": "Remind about offline downloads feature"},
            ],
            "estimated_impact": {"conversion_rate_lift": 0.25, "retention_improvement": 0.30, "revenue_impact_per_user": 9.99},
        },
        {
            "playbook_id": "PB_WIN_BACK",
            "name":        "Win-Back Campaign",
            "priority":    4,
            "description": "Re-engage users who have reduced activity significantly.",
            "actions": [
                {"step": 1, "channel": "Email", "action": "Send personalised We miss you email"},
                {"step": 2, "channel": "SMS",   "action": "Send exclusive 50% off offer"},
            ],
            "estimated_impact": {"conversion_rate_lift": 0.18, "retention_improvement": 0.22, "revenue_impact_per_user": 5.99},
        },
    ],
    "medium_risk": [
        {
            "playbook_id": "PB_ENGAGEMENT_BOOST",
            "name":        "Engagement Boost",
            "priority":    3,
            "description": "Increase feature discovery and listening engagement.",
            "actions": [
                {"step": 1, "channel": "In-App", "action": "Recommend 5 new personalised playlists"},
                {"step": 2, "channel": "Email",  "action": "Share weekly listening highlights"},
                {"step": 3, "channel": "Push",   "action": "Notify about new releases in favourite genres"},
            ],
            "estimated_impact": {"conversion_rate_lift": 0.12, "retention_improvement": 0.18, "revenue_impact_per_user": 3.99},
        },
    ],
    "low_risk": [
        {
            "playbook_id": "PB_UPSELL_PREMIUM",
            "name":        "Premium Upsell",
            "priority":    2,
            "description": "Convert satisfied free users to Premium.",
            "actions": [
                {"step": 1, "channel": "In-App", "action": "Highlight Premium-only features"},
                {"step": 2, "channel": "Email",  "action": "Send Upgrade for more offer"},
            ],
            "estimated_impact": {"conversion_rate_lift": 0.08, "retention_improvement": 0.10, "revenue_impact_per_user": 9.99},
        },
    ],
}

def get_playbooks(prediction: Dict) -> Optional[Dict]:
    try:
        pbs = PLAYBOOKS.get(prediction["risk_segment"], PLAYBOOKS["medium_risk"])
        return {
            "recommended_playbooks": pbs,
            "best_playbook_id":      pbs[0]["playbook_id"],
            "estimated_impact":      pbs[0]["estimated_impact"],
        }
    except Exception as e:
        st.error(f"Playbook error: {e}")
        return None

# ============================================================================
# CHAT ENGINE
# ============================================================================
def generate_chat_response(user_message: str, context: Dict) -> Dict:
    msg    = user_message.lower()
    prob   = context.get("churn_probability", 0.5)
    risk   = context.get("risk_segment", "medium_risk")
    prob_s = f"{prob*100:.0f}%"

    if any(w in msg for w in ["why", "churn", "risk", "leave", "cancel"]):
        return {
            "content": f"Your current churn risk is **{prob_s}** ({risk.replace('_',' ').title()}). "
                       "Main factors: subscription type, session frequency, streaming hours. "
                       "Would you like a detailed breakdown or personalised recommendations?",
            "actions": [{"label": "Show detailed explanation"}],
            "offers":  [{"label": "7-day Premium Trial"}],
        }
    elif any(w in msg for w in ["offer", "help", "suggest", "recommend", "what can"]):
        return {
            "content": "Based on your profile I recommend:\n"
                       "1. 🎵 **30-day Premium free trial** — ad-free, offline, HD audio\n"
                       "2. 🎧 **Personalised playlists** built just for you\n"
                       "3. 🌍 Discover new genres with **Genre Mix**\n\nWould you like to activate any?",
            "actions": [{"label": "View all recommendations"}],
            "offers":  [{"label": "1-month Free Trial"}, {"label": "30% off Premium"}],
        }
    elif any(w in msg for w in ["premium", "upgrade", "price", "cost", "plan"]):
        return {
            "content": "**Spotify Premium** at $9.99/month includes:\n"
                       "- ✅ Ad-free listening\n- ✅ Offline downloads\n"
                       "- ✅ High-quality audio\n- ✅ Unlimited skips\n\n"
                       f"Given your {risk.replace('_',' ')} status, we can offer a **30-day free trial**!",
            "actions": [{"label": "Start free trial"}],
            "offers":  [{"label": "30-day Premium Trial"}],
        }
    elif any(w in msg for w in ["explain", "shap", "feature", "factor", "reason"]):
        return {
            "content": "Predictions use **SHAP values** — each feature's contribution to churn risk.\n\n"
                       "🔴 Positive SHAP = increases churn risk\n"
                       "🟢 Negative SHAP = decreases churn risk\n\n"
                       "Run a prediction and click 📖 Show Explanation to see your breakdown.",
            "actions": [], "offers": [],
        }
    elif any(w in msg for w in ["hello", "hi", "hey", "start"]):
        return {
            "content": f"👋 Hello! I am your Spotify Churn Assistant.\n\n"
                       f"Your current churn risk is **{prob_s}**. I can help you:\n"
                       "- 🔍 Understand your churn risk factors\n"
                       "- 🎯 Get personalised retention offers\n"
                       "- 📊 Explain the prediction in plain English",
            "actions": [{"label": "Explain my risk"}, {"label": "Get recommendations"}],
            "offers":  [],
        }
    elif any(w in msg for w in ["thank", "thanks", "yes", "ok", "great", "good"]):
        return {"content": "You are welcome! 😊 Is there anything else I can help you with?",
                "actions": [], "offers": []}
    else:
        return {
            "content": "I am here to help! I can:\n"
                       "- Explain your **churn risk factors**\n"
                       "- Recommend **personalised offers**\n"
                       "- Answer questions about **Spotify Premium**\n\n"
                       "Try: *Why might I churn?* or *What offers do you have?*",
            "actions": [{"label": "Explain my risk"}, {"label": "Get recommendations"}],
            "offers":  [],
        }

# ============================================================================
# CHART HELPERS
# ============================================================================
def create_gauge_chart(value: float, title: str) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta", value=value * 100, title={"text": title},
        domain={"x": [0, 1], "y": [0, 1]},
        gauge={
            "axis":  {"range": [0, 100]},
            "bar":   {"color": "darkblue"},
            "steps": [{"range": [0,  33], "color": "#00cc66"},
                      {"range": [33, 67], "color": "#ff9500"},
                      {"range": [67, 100], "color": "#ff3333"}],
            "threshold": {"line": {"color": "red", "width": 4}, "thickness": 0.75, "value": 90},
        },
    ))
    fig.update_layout(height=300, margin=dict(b=0))
    return fig

def create_feature_importance_chart(attributions: List[Dict]) -> go.Figure:
    if not attributions:
        return None
    df     = pd.DataFrame(attributions).sort_values("impact_percentage", ascending=True)
    colors = ["#ff3333" if x > 0 else "#00cc66" for x in df["impact_percentage"]]
    fig    = go.Figure(data=[go.Bar(
        y=df["feature_name"], x=df["impact_percentage"], orientation="h",
        marker=dict(color=colors), text=df["impact_percentage"].round(1), textposition="auto",
    )])
    fig.update_layout(title="Feature Importance (SHAP Values)",
                      xaxis_title="Impact on Churn (%)", yaxis_title="Features",
                      height=400, margin=dict(l=150), showlegend=False)
    return fig

def create_prediction_history_chart(history: List[Dict]) -> go.Figure:
    if not history:
        return None
    df  = pd.DataFrame(history)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["churn_probability"] * 100,
        mode="lines+markers", name="Churn Probability",
        line=dict(color="#1DB954", width=3), marker=dict(size=8),
    ))
    fig.update_layout(title="Churn Risk Over Time", xaxis_title="Date",
                      yaxis_title="Churn Probability (%)", height=300,
                      hovermode="x unified", template="plotly_white")
    return fig

def get_risk_emoji(risk_segment: str) -> str:
    return {"high_risk": "🔴", "medium_risk": "🟠", "low_risk": "🟢"}.get(risk_segment, "⚪")

# ============================================================================
# PAGE: HOME
# ============================================================================
def page_home(model, explainer):
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown('<div class="header-title">🎵 Spotify Churn Prediction</div>', unsafe_allow_html=True)
    with col2:
        st.success("✅ Model Loaded") if model else st.error("❌ Model Not Found")

    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["🔍 Single Prediction", "👥 Customer Profiles", "📊 Analytics"])

    # ── TAB 1: SINGLE PREDICTION ──────────────────────────────────────────
    with tab1:
        st.subheader("Predict Churn Risk for a User")
        if model is None:
            st.warning("⚠️ No model file found. Place model.joblib in the project folder and restart.")
            return

        col1, col2 = st.columns(2)
        with col1:
            user_id           = st.text_input("User ID", value="user_001")
            subscription_type = st.selectbox("Subscription Type", ["Free", "Premium"])
            num_sessions      = st.slider("Monthly Sessions", 0, 100, 10)
        with col2:
            monthly_stream_hours = st.slider("Monthly Stream Hours", 0.0, 200.0, 5.5, step=0.5)
            account_age_days     = st.slider("Account Age (days)", 0, 1000, 30)
            playlist_diversity   = st.slider("Playlist Diversity", 0.0, 1.0, 0.6, step=0.1)

        if st.button("🔮 Predict Churn Risk", use_container_width=True):
            features = {
                "subscription_type":    subscription_type,
                "num_sessions":         num_sessions,
                "monthly_stream_hours": monthly_stream_hours,
                "account_age_days":     account_age_days,
                "playlist_diversity":   playlist_diversity,
            }
            with st.spinner("Running prediction..."):
                prediction = make_prediction(model, user_id, features)
            if prediction:
                st.session_state.last_prediction = prediction
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric("Churn Risk", f"{prediction['churn_probability']*100:.1f}%",
                              delta=f"Confidence: {prediction['confidence_score']:.0%}")
                with c2:
                    st.metric("Risk Segment",
                              f"{get_risk_emoji(prediction['risk_segment'])} "
                              f"{prediction['risk_segment'].replace('_',' ').title()}")
                with c3:
                    st.metric("Prediction",
                              "⚠️ CHURN" if prediction["prediction_label"] == 1 else "✅ RETAIN")
                st.plotly_chart(
                    create_gauge_chart(prediction["churn_probability"], "Churn Probability"),
                    use_container_width=True)

        if st.session_state.get("last_prediction"):
            prediction = st.session_state.last_prediction

            if st.button("📖 Show Explanation"):
                if explainer is None:
                    st.warning("⚠️ SHAP explainer unavailable. Showing rule-based insights.")
                    churn_prob = prediction["churn_probability"]
                    st.info(f"**Summary:** User shows "
                            f"{'high' if churn_prob > 0.67 else 'moderate' if churn_prob > 0.33 else 'low'} "
                            f"churn risk ({churn_prob*100:.1f}%).")
                    for insight in _build_insights([], prediction["features"], prediction["risk_segment"]):
                        st.success(insight)
                else:
                    with st.spinner("Generating SHAP explanation..."):
                        explanation = make_explanation(explainer, prediction)
                    if explanation:
                        st.info(f"**Summary:** {explanation['summary']}")
                        st.subheader("📍 Key Drivers")
                        for d in explanation["key_drivers"]:
                            st.write(f"• {d}")
                        st.subheader("💡 Feature Impact (SHAP)")
                        fig = create_feature_importance_chart(explanation["feature_attributions"])
                        if fig:
                            st.plotly_chart(fig, use_container_width=True)
                        st.subheader("💬 Actionable Insights")
                        for insight in explanation["actionable_insights"]:
                            st.success(insight)

            if st.button("🎬 Get Playbook Recommendations"):
                with st.spinner("Finding best playbooks..."):
                    playbooks = get_playbooks(prediction)
                if playbooks:
                    st.subheader(f"Best Playbook: {playbooks['best_playbook_id']}")
                    for pb in playbooks["recommended_playbooks"]:
                        with st.expander(f"📋 {pb['name']}", expanded=True):
                            st.write(f"**Description:** {pb['description']}")
                            st.write(f"**Priority:** {pb['priority']}")
                            st.write(f"**Conversion Lift:** {pb['estimated_impact']['conversion_rate_lift']:.0%}")
                            st.write(f"**Retention Improvement:** {pb['estimated_impact']['retention_improvement']:.0%}")
                            st.write("**Actions:**")
                            for action in pb["actions"]:
                                st.write(f"  Step {action['step']} [{action['channel']}]: {action['action']}")

    # ── TAB 2: CUSTOMER PROFILES ──────────────────────────────────────────
    with tab2:
        st.subheader("Customer Profile Explorer")
        col1, col2 = st.columns([2, 1])
        with col1:
            profile_user_id = st.text_input("Enter User ID", value="user_002", key="profile_user")
        with col2:
            if st.button("📋 Load Profile", use_container_width=True):
                st.session_state.show_profile = True

        if st.session_state.get("show_profile", False):
            c1, c2, c3 = st.columns(3)
            with c1: st.metric("Account Age", "45 days")
            with c2: st.metric("Sessions (30d)", 12)
            with c3: st.metric("Stream Hours (30d)", "6.2h")

            st.subheader("Favourite Genres")
            fig = px.bar(pd.DataFrame({"Genre": ["Pop","Hip-Hop","RnB"], "Streams": [15,12,8]}),
                         x="Genre", y="Streams", color="Streams", color_continuous_scale="Viridis")
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("Churn Risk History")
            history = [{"date": (datetime.now()-timedelta(days=i)).strftime("%Y-%m-%d"),
                        "churn_probability": min(0.95, 0.4+i*0.05)} for i in range(30,0,-5)]
            fig = create_prediction_history_chart(history)
            if fig: st.plotly_chart(fig, use_container_width=True)

    # ── TAB 3: ANALYTICS ──────────────────────────────────────────────────
    with tab3:
        st.subheader("Platform Analytics")
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("Total Users Analysed", "15,230")
        with c2: st.metric("High Risk Users", "3,245", "-245")
        with c3: st.metric("Playbooks Executed", "1,892", "+143")
        with c4: st.metric("Avg Churn Risk", "42.3%", "-2.1%")

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Risk Distribution")
            fig = px.pie(pd.DataFrame({"Segment":["Low Risk","Medium Risk","High Risk"],
                                       "Count":[8100,4885,3245]}),
                         values="Count", names="Segment",
                         color_discrete_map={"Low Risk":"#00cc66","Medium Risk":"#ff9500","High Risk":"#ff3333"})
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.subheader("Playbook Success Rate")
            fig = px.bar(pd.DataFrame({"Playbook":["High-Risk Convert","Engagement Boost","Retention Plus"],
                                       "Success Rate":[75,62,58]}),
                         x="Playbook", y="Success Rate",
                         color="Success Rate", color_continuous_scale="RdYlGn")
            st.plotly_chart(fig, use_container_width=True)

    # ── CHAT ASSISTANT ────────────────────────────────────────────────────
    st.markdown("---")
    st.subheader("💬 Chat Assistant")
    with st.container():
        for message in st.session_state.chat_messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])

    user_input = st.chat_input("Ask about churn risk or recommendations...")
    if user_input:
        st.session_state.chat_messages.append({"role": "user", "content": user_input})
        context = {}
        if st.session_state.last_prediction:
            context = {
                "churn_probability": st.session_state.last_prediction.get("churn_probability", 0.5),
                "risk_segment":      st.session_state.last_prediction.get("risk_segment", "medium_risk"),
            }
        with st.spinner("Thinking..."):
            response = generate_chat_response(user_input, context)
        st.session_state.chat_messages.append({"role": "assistant", "content": response["content"]})
        if response.get("suggested_actions"):
            st.info("**Suggested Actions:** " + " | ".join(a["label"] for a in response["suggested_actions"]))
        if response.get("offers"):
            st.success("**Available Offers:** " + " | ".join(o["label"] for o in response["offers"]))
        st.rerun()

# ============================================================================
# PAGE: HELP
# ============================================================================
def page_help():
    st.title("📚 Help & Documentation")
    tab1, tab2, tab3 = st.tabs(["Getting Started", "Model Info", "FAQ"])

    with tab1:
        st.markdown("""
## Getting Started
### 1. Single Prediction
- Enter user details in the Single Prediction tab
- Click **Predict Churn Risk** to get results
- View the risk gauge and confidence score

### 2. View SHAP Explanations
- After a prediction click **Show Explanation**
- See which features drive churn risk up or down
- Get plain-English actionable insights

### 3. Get Playbook Recommendations
- Click **Get Playbook Recommendations**
- View recommended intervention playbooks
- See step-by-step action plans per channel

### 4. Chat with the Assistant
- Type any question in the chat box at the bottom
- Ask about churn risk, offers, or Premium features

### 5. Analytics Dashboard
- View platform-wide insights
- Track playbook success rates
- Monitor risk distribution
        """)

    with tab2:
        st.markdown("""
## Model Information
| Item | Detail |
|------|--------|
| Model file | model.joblib or churn_model.pkl |
| Framework | scikit-learn / XGBoost |
| Explainability | SHAP TreeExplainer |
| Features | subscription_type, num_sessions, monthly_stream_hours, account_age_days, playlist_diversity |

### How It Works
1. User inputs collected from sliders
2. Features encoded and passed directly to the loaded model
3. SHAP values computed locally — no backend required
4. Playbook recommendations are rule-based on risk segment
5. Chat responses are keyword-based
        """)

    with tab3:
        st.markdown("""
## FAQ

**Q: What does the churn probability mean?**
A: The likelihood (0-100%) that a user will cancel their Spotify subscription.

**Q: What are risk segments?**
- 🟢 Low Risk (0-33%) — Likely to stay
- 🟠 Medium Risk (33-67%) — Needs engagement
- 🔴 High Risk (67%+) — Immediate action needed

**Q: What are playbooks?**
A: Structured intervention sequences (emails, in-app messages, offers) to retain at-risk users.

**Q: How do SHAP values work?**
A: SHAP measures how much each feature pushes the prediction up or down.
Red = increases churn risk. Green = decreases churn risk.

**Q: Does this app need a backend server?**
A: No. Everything runs locally — model, SHAP, playbooks, and chat are all self-contained.
        """)

# ============================================================================
# MAIN
# ============================================================================
def main():
    if "page"            not in st.session_state: st.session_state.page = "home"
    if "last_prediction" not in st.session_state: st.session_state.last_prediction = {}
    if "show_profile"    not in st.session_state: st.session_state.show_profile = False
    if "chat_session_id" not in st.session_state: st.session_state.chat_session_id = f"session_{int(time.time())}"
    if "chat_messages"   not in st.session_state: st.session_state.chat_messages = []

    model    = load_model()
    explainer = load_explainer(model) if model else None

    with st.sidebar:
        st.title("🎵 Navigation")
        page = st.radio("Select Page", ["Home", "Help & Docs"], index=0)
        st.session_state.page = "home" if page == "Home" else "help"
        st.markdown("---")
        st.subheader("⚙️ System Status")
        st.success("✅ Model: Loaded")   if model    else st.error("❌ Model: Not Found — add model.joblib to project root")
        st.success("✅ SHAP: Ready")     if explainer else st.warning("⚠️ SHAP: Unavailable")
        st.markdown("---")
        st.markdown("""
### About
**Spotify Churn Prediction**
Version 2.0 — Standalone
No backend required ✅

### Features
- 🔮 Real-time predictions
- 📖 SHAP explanations
- 🎬 Playbook engine
- 💬 Chat assistant
        """)

    if st.session_state.page == "home":
        page_home(model, explainer)
    else:
        page_help()

if __name__ == "__main__":
    main()