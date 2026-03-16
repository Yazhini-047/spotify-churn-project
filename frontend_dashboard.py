"""
SPOTIFY CHURN PREDICTION - STANDALONE FRONTEND
===============================================
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
import warnings
import logging

# Suppress ALL warnings and logs before anything else
warnings.filterwarnings("ignore")
logging.getLogger().setLevel(logging.CRITICAL)
logging.disable(logging.CRITICAL)
os.environ["PYTHONWARNINGS"] = "ignore"

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="Spotify Churn Guard",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Hide ALL error details and tracebacks from the UI
st.set_option("client.showErrorDetails", False)

# ============================================================================
# SPOTIFY DARK THEME CSS
# ============================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"], .stApp {
    font-family: 'DM Sans', sans-serif !important;
    background-color: #0a0a0a !important;
    color: #e0e0e0 !important;
}
.main .block-container {
    padding: 1.5rem 2.5rem !important;
    max-width: 1300px !important;
    background-color: #0a0a0a !important;
}

/* ── NUCLEAR: Kill ALL debug/traceback/code blocks everywhere ── */
.stException                                    { display:none!important; }
.stException *                                  { display:none!important; }
[data-testid="stNotificationContentError"] pre  { display:none!important; }
[data-testid="stNotificationContentWarning"] pre{ display:none!important; }
[data-testid="stSidebar"] pre                   { display:none!important; }
[data-testid="stSidebar"] code                  { display:none!important; }
[data-testid="stSidebar"] .stException          { display:none!important; }
[data-testid="stSidebar"] .element-container:has(pre) { display:none!important; }
[data-testid="stSidebar"] .element-container:has(code){ display:none!important; }
.main pre                                        { display:none!important; }
.main code                                       { display:none!important; }
div:has(> pre)                                   { display:none!important; }
div:has(> code)                                  { display:none!important; }
.element-container:has(pre)                      { display:none!important; }
.element-container:has(code)                     { display:none!important; }
[data-testid="stAlert"] pre                      { display:none!important; }
[data-testid="stAlert"] code                     { display:none!important; }
/* Hide the specific white box with monospaced debug text */
[data-testid="stSidebar"] div[style*="background"] { 
    background: transparent!important; 
    border: none!important; 
}
.sidebar-content pre, .sidebar-content code      { display:none!important; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #111111 0%, #0d0d0d 100%) !important;
    border-right: 2px solid #1DB954 !important;
}
[data-testid="stSidebar"] * { color: #e0e0e0 !important; }

/* Hero */
.hero-header {
    background: linear-gradient(135deg, #1DB954 0%, #158a3e 60%, #0a5c2a 100%);
    border-radius: 20px;
    padding: 2.2rem 2.8rem;
    margin-bottom: 2rem;
    box-shadow: 0 8px 40px rgba(29,185,84,0.4);
    position: relative;
    overflow: hidden;
}
.hero-header::before {
    content: '';
    position: absolute;
    top: -60px; right: -40px;
    width: 280px; height: 280px;
    background: rgba(255,255,255,0.06);
    border-radius: 50%;
}
.hero-header::after {
    content: '';
    position: absolute;
    bottom: -80px; right: 120px;
    width: 200px; height: 200px;
    background: rgba(255,255,255,0.04);
    border-radius: 50%;
}
.hero-title {
    font-size: 2.4rem; font-weight: 700;
    color: #ffffff; margin: 0;
    letter-spacing: -0.8px;
    position: relative; z-index: 1;
}
.hero-subtitle {
    font-size: 1.05rem;
    color: rgba(255,255,255,0.82);
    margin-top: 0.5rem;
    position: relative; z-index: 1;
}
.hero-tags {
    margin-top: 1rem;
    position: relative; z-index: 1;
}
.hero-tag {
    display: inline-block;
    background: rgba(0,0,0,0.2);
    border: 1px solid rgba(255,255,255,0.25);
    border-radius: 20px;
    padding: 3px 14px;
    font-size: 0.78rem;
    color: #fff;
    margin-right: 8px;
}

/* Section titles */
.section-title {
    font-size: 0.78rem;
    font-weight: 700;
    color: #1DB954;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #1DB95430;
}

/* Metric cards */
[data-testid="stMetric"] {
    background: #141414 !important;
    border: 1px solid #222222 !important;
    border-radius: 14px !important;
    padding: 1.2rem 1.5rem !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.4) !important;
    transition: all 0.25s ease !important;
}
[data-testid="stMetric"]:hover {
    border-color: #1DB954 !important;
    transform: translateY(-3px) !important;
    box-shadow: 0 8px 28px rgba(29,185,84,0.2) !important;
}
[data-testid="stMetricLabel"] {
    color: #777777 !important;
    font-size: 0.72rem !important;
    text-transform: uppercase !important;
    letter-spacing: 1.5px !important;
    font-weight: 600 !important;
}
[data-testid="stMetricValue"] {
    color: #ffffff !important;
    font-size: 1.85rem !important;
    font-weight: 700 !important;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #1DB954, #158a3e) !important;
    color: #000 !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 50px !important;
    padding: 0.65rem 2rem !important;
    font-size: 0.92rem !important;
    transition: all 0.25s ease !important;
    box-shadow: 0 4px 18px rgba(29,185,84,0.35) !important;
    font-family: 'DM Sans', sans-serif !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 28px rgba(29,185,84,0.55) !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: #141414 !important;
    border-radius: 14px !important;
    padding: 5px !important;
    gap: 4px !important;
    border: 1px solid #222 !important;
    margin-bottom: 1.5rem !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border-radius: 10px !important;
    color: #777 !important;
    font-weight: 500 !important;
    padding: 0.5rem 1.4rem !important;
    border: none !important;
    transition: all 0.2s !important;
}
.stTabs [aria-selected="true"] {
    background: #1DB954 !important;
    color: #000000 !important;
    font-weight: 700 !important;
}

/* Inputs */
.stTextInput > div > div > input,
.stNumberInput > div > div > input {
    background: #141414 !important;
    border: 1px solid #252525 !important;
    border-radius: 10px !important;
    color: #e0e0e0 !important;
    font-family: 'DM Sans', sans-serif !important;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus {
    border-color: #1DB954 !important;
    box-shadow: 0 0 0 2px rgba(29,185,84,0.25) !important;
}
.stSelectbox > div > div {
    background: #141414 !important;
    border: 1px solid #252525 !important;
    border-radius: 10px !important;
    color: #e0e0e0 !important;
}
.stSlider > div > div > div > div { background: #1DB954 !important; }
[data-testid="stSliderThumb"] { background: #1DB954 !important; }

/* Alerts */
.stSuccess {
    background: rgba(29,185,84,0.1) !important;
    border: 1px solid rgba(29,185,84,0.35) !important;
    border-radius: 10px !important;
    color: #1DB954 !important;
}
.stWarning {
    background: rgba(255,149,0,0.1) !important;
    border: 1px solid rgba(255,149,0,0.35) !important;
    border-radius: 10px !important;
}
.stError {
    background: rgba(255,51,51,0.1) !important;
    border: 1px solid rgba(255,51,51,0.35) !important;
    border-radius: 10px !important;
}
.stInfo {
    background: rgba(29,185,84,0.08) !important;
    border: 1px solid rgba(29,185,84,0.25) !important;
    border-radius: 10px !important;
    color: #cccccc !important;
}

/* Expander */
.streamlit-expanderHeader {
    background: #141414 !important;
    border: 1px solid #222 !important;
    border-radius: 10px !important;
    color: #e0e0e0 !important;
    font-weight: 600 !important;
}
.streamlit-expanderContent {
    background: #0e0e0e !important;
    border: 1px solid #222 !important;
    border-top: none !important;
    border-radius: 0 0 10px 10px !important;
}

/* Chat */
[data-testid="stChatMessage"] {
    background: #141414 !important;
    border: 1px solid #222 !important;
    border-radius: 14px !important;
    margin-bottom: 0.6rem !important;
}
[data-testid="stChatInputContainer"] {
    background: #141414 !important;
    border: 1px solid #252525 !important;
    border-radius: 50px !important;
}

/* Risk badges */
.badge {
    display: inline-block;
    padding: 5px 16px;
    border-radius: 20px;
    font-weight: 700;
    font-size: 0.82rem;
    letter-spacing: 0.5px;
}
.badge-high   { background:#ff333318; color:#ff5555; border:1px solid #ff333355; }
.badge-medium { background:#ff950018; color:#ffaa44; border:1px solid #ff950055; }
.badge-low    { background:#1DB95418; color:#1DB954; border:1px solid #1DB95455; }

/* Result card */
.result-card {
    background: linear-gradient(135deg, #141414, #1a1a1a);
    border: 1px solid #252525;
    border-radius: 16px;
    padding: 1.8rem;
    margin: 1rem 0;
    box-shadow: 0 4px 24px rgba(0,0,0,0.4);
}

/* Divider */
hr { border-color: #1e1e1e !important; margin: 1.5rem 0 !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: #111; }
::-webkit-scrollbar-thumb { background: #1DB954; border-radius: 3px; }

/* Hide streamlit chrome */
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
header    { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# PLOTLY DARK THEME
# ============================================================================
PLOTLY = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#111111",
    font=dict(color="#cccccc", family="DM Sans"),
    xaxis=dict(gridcolor="#1e1e1e", linecolor="#1e1e1e", zerolinecolor="#1e1e1e"),
    yaxis=dict(gridcolor="#1e1e1e", linecolor="#1e1e1e", zerolinecolor="#1e1e1e"),
    margin=dict(t=50, b=30, l=20, r=20),
)

# ============================================================================
# MODEL LOADING
# ============================================================================
@st.cache_resource
def load_model():
    for path in ["spotify_churn_model.pkl", "final_churn_model.pkl",
                 "perfect_model.pkl", "model.joblib", "model.pkl"]:
        if os.path.exists(path):
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    return joblib.load(path)
            except Exception:
                pass
    return None

@st.cache_resource
def load_scaler():
    if os.path.exists("scaler.pkl"):
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                return joblib.load("scaler.pkl")
        except Exception:
            pass
    return None

@st.cache_resource
def load_explainer(_model):
    if _model is None:
        return None
    try:
        import shap
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return shap.TreeExplainer(_model)
    except Exception:
        try:
            import shap
            return shap.Explainer(_model)
        except Exception:
            return None

@st.cache_data
def load_dataset():
    """
    Load all 8000 real users from the CSV dataset.
    Cached so it only reads once — fast for all users.
    """
    csv_paths = ["spotify dataset.csv", "spotify_dataset.csv", "data.csv"]
    for path in csv_paths:
        if os.path.exists(path):
            try:
                df = pd.read_csv(path)
                # Ensure user_id is string for display
                df["user_id"] = df["user_id"].astype(str)
                return df
            except Exception:
                pass
    return None

# ============================================================================
# EXACT 15 FEATURE COLUMNS FROM model_columns.pkl
# ============================================================================
FEATURE_COLUMNS = [
    'age', 'listening_time', 'songs_played_per_day', 'skip_rate',
    'ads_listened_per_week', 'offline_listening', 'ad_stress',
    'skip_intensity', 'gender_Male', 'gender_Other',
    'subscription_type_Free', 'subscription_type_Premium',
    'subscription_type_Student', 'device_type_Mobile', 'device_type_Web'
]

NUMERIC_FEATURES = [
    'age', 'listening_time', 'songs_played_per_day', 'skip_rate',
    'ads_listened_per_week', 'offline_listening', 'ad_stress', 'skip_intensity'
]

DISPLAY_NAMES = {
    'age':                   'Age',
    'listening_time':        'Listening Time (hrs/day)',
    'songs_played_per_day':  'Songs Per Day',
    'skip_rate':             'Skip Rate (0-1)',
    'ads_listened_per_week': 'Ads Per Week',
    'offline_listening':     'Offline Listening (hrs)',
    'ad_stress':             'Ad Stress Score',
    'skip_intensity':        'Skip Intensity',
    'gender_Male':           'Gender: Male',
    'gender_Other':          'Gender: Other',
    'subscription_type_Free':     'Sub: Free',
    'subscription_type_Premium':  'Sub: Premium',
    'subscription_type_Student':  'Sub: Student',
    'device_type_Mobile':    'Device: Mobile',
    'device_type_Web':       'Device: Web',
}

def build_features(inputs: dict) -> pd.DataFrame:
    """
    Convert UI inputs into the exact 15-column DataFrame the model expects.
    Handles one-hot encoding for gender, subscription_type, device_type.
    Computes derived features: ad_stress and skip_intensity.
    """
    row = {}

    # Numeric features
    row['age']                   = inputs['age']
    row['listening_time']        = inputs['listening_time']
    row['songs_played_per_day']  = inputs['songs_played_per_day']
    row['skip_rate']             = inputs['skip_rate']
    row['ads_listened_per_week'] = inputs['ads_listened_per_week']
    row['offline_listening']     = inputs['offline_listening']

    # Derived features
    row['ad_stress']      = inputs['ads_listened_per_week'] * inputs['skip_rate']
    row['skip_intensity'] = inputs['skip_rate'] * inputs['songs_played_per_day']

    # Gender one-hot (baseline = Female)
    row['gender_Male']  = 1 if inputs['gender'] == 'Male'  else 0
    row['gender_Other'] = 1 if inputs['gender'] == 'Other' else 0

    # Subscription one-hot (all three columns needed)
    row['subscription_type_Free']    = 1 if inputs['subscription_type'] == 'Free'    else 0
    row['subscription_type_Premium'] = 1 if inputs['subscription_type'] == 'Premium' else 0
    row['subscription_type_Student'] = 1 if inputs['subscription_type'] == 'Student' else 0

    # Device one-hot (baseline = Desktop/Tablet)
    row['device_type_Mobile'] = 1 if inputs['device_type'] == 'Mobile' else 0
    row['device_type_Web']    = 1 if inputs['device_type'] == 'Web'    else 0

    df = pd.DataFrame([row])[FEATURE_COLUMNS]
    return df

# ============================================================================
# PREDICTION ENGINE
# ============================================================================
def make_prediction(model, scaler, user_id: str, inputs: dict) -> dict:
    try:
        df = build_features(inputs)

        # Apply scaler only to numeric columns if scaler is available
        if scaler is not None:
            try:
                df_scaled = df.copy()
                df_scaled[NUMERIC_FEATURES] = scaler.transform(df[NUMERIC_FEATURES])
                churn_prob = float(model.predict_proba(df_scaled)[0][1])
                label      = int(model.predict(df_scaled)[0])
            except Exception:
                churn_prob = float(model.predict_proba(df)[0][1])
                label      = int(model.predict(df)[0])
        else:
            churn_prob = float(model.predict_proba(df)[0][1])
            label      = int(model.predict(df)[0])

        confidence   = max(churn_prob, 1 - churn_prob)
        risk_segment = ("low_risk"    if churn_prob < 0.33 else
                        "medium_risk" if churn_prob < 0.67 else
                        "high_risk")

        return {
            "user_id":           user_id,
            "prediction_id":     str(uuid.uuid4()),
            "churn_probability": churn_prob,
            "risk_segment":      risk_segment,
            "prediction_label":  label,
            "confidence_score":  confidence,
            "timestamp":         datetime.utcnow().isoformat(),
            "inputs":            inputs,
            "df":                df,
        }
    except Exception as e:
        st.error(f"Prediction error: {e}")
        return None

# ============================================================================
# SHAP EXPLANATION
# ============================================================================
def make_explanation(explainer, prediction: dict) -> dict:
    try:
        import shap
        df        = prediction["df"]
        shap_vals = explainer.shap_values(df)
        sv        = shap_vals[1][0] if isinstance(shap_vals, list) else shap_vals[0]
        total_abs = sum(abs(v) for v in sv) or 1.0
        attributions = []
        for fname, val in zip(FEATURE_COLUMNS, sv):
            impact_pct = round((val / total_abs) * 100, 1)
            direction  = ("increases_churn" if val > 0.01 else
                          "decreases_churn" if val < -0.01 else "neutral")
            display = DISPLAY_NAMES.get(fname, fname)
            attributions.append({
                "feature_name":      display,
                "shap_value":        round(float(val), 4),
                "direction":         direction,
                "impact_percentage": impact_pct,
            })
        attributions.sort(key=lambda x: abs(x["impact_percentage"]), reverse=True)
        key_drivers = [a["feature_name"] for a in attributions[:3]]
        prob        = prediction["churn_probability"]
        summary     = (
            f"User shows {'high' if prob>0.67 else 'moderate' if prob>0.33 else 'low'} "
            f"churn risk ({prob*100:.1f}%). "
            f"Key factors: {', '.join(key_drivers)}."
        )
        return {
            "summary":              summary,
            "key_drivers":          key_drivers,
            "feature_attributions": attributions,
            "actionable_insights":  _build_insights(attributions, prediction["risk_segment"]),
        }
    except Exception as e:
        st.error(f"Explanation error: {e}")
        return None

def _build_insights(attributions: list, risk_segment: str) -> list:
    insights = []
    for attr in attributions[:5]:
        fname, direction = attr["feature_name"], attr["direction"]
        if direction != "increases_churn":
            continue
        if "Skip Rate" in fname or "Skip Intensity" in fname:
            insights.append("⏭️ High skip rate detected — improve music recommendation quality.")
        elif "Ads" in fname or "Ad Stress" in fname:
            insights.append("📢 User is ad-fatigued — offer Premium trial to reduce ad exposure.")
        elif "Listening Time" in fname:
            insights.append("🎵 Low listening time — send curated playlist to re-engage.")
        elif "Songs" in fname:
            insights.append("📉 Low songs played — suggest Discover Weekly or Daily Mix.")
        elif "Offline" in fname:
            insights.append("📶 Low offline usage — highlight offline download feature.")
        elif "Free" in fname:
            insights.append("🎯 Free user — offer discounted Premium or Student plan.")
        elif "Age" in fname:
            insights.append("👤 Age is a churn factor — tailor content to user demographic.")
    if not insights:
        if risk_segment == "high_risk":
            insights = [
                "🚨 High churn risk — trigger immediate retention playbook.",
                "💰 Offer a personalised discount within 24 hours.",
                "📧 Send re-engagement email with curated content.",
            ]
        elif risk_segment == "medium_risk":
            insights = [
                "📊 Monitor engagement over the next 7 days.",
                "🎁 Consider a loyalty reward or exclusive content offer.",
            ]
        else:
            insights = [
                "✅ User appears healthy — continue standard engagement.",
                "📈 Great time to upsell Premium features.",
            ]
    return insights[:4]

# ============================================================================
# PLAYBOOK ENGINE
# ============================================================================
PLAYBOOKS = {
    "high_risk": [
        {"playbook_id":"PB_HIGH_RISK_CONVERT","name":"High-Risk Conversion Blitz","priority":5,
         "description":"Immediate multi-channel intervention for users very likely to churn.",
         "actions":[{"step":1,"channel":"Email","action":"Send 30-day Premium free trial offer"},
                    {"step":2,"channel":"In-App","action":"Show personalised discount banner"},
                    {"step":3,"channel":"Push","action":"Highlight offline downloads & HD audio"}],
         "estimated_impact":{"conversion_rate_lift":0.25,"retention_improvement":0.30,"revenue":9.99}},
        {"playbook_id":"PB_WIN_BACK","name":"Win-Back Campaign","priority":4,
         "description":"Re-engage users with significantly reduced activity.",
         "actions":[{"step":1,"channel":"Email","action":"Send personalised 'We miss you' email"},
                    {"step":2,"channel":"SMS","action":"Send exclusive 50% off limited offer"}],
         "estimated_impact":{"conversion_rate_lift":0.18,"retention_improvement":0.22,"revenue":5.99}},
    ],
    "medium_risk": [
        {"playbook_id":"PB_ENGAGEMENT_BOOST","name":"Engagement Boost","priority":3,
         "description":"Increase feature discovery and listening engagement.",
         "actions":[{"step":1,"channel":"In-App","action":"Recommend 5 new personalised playlists"},
                    {"step":2,"channel":"Email","action":"Share weekly listening highlights"},
                    {"step":3,"channel":"Push","action":"Notify about new releases in favourite genres"}],
         "estimated_impact":{"conversion_rate_lift":0.12,"retention_improvement":0.18,"revenue":3.99}},
    ],
    "low_risk": [
        {"playbook_id":"PB_UPSELL_PREMIUM","name":"Premium Upsell","priority":2,
         "description":"Convert satisfied free users to Premium subscribers.",
         "actions":[{"step":1,"channel":"In-App","action":"Highlight Premium-only features"},
                    {"step":2,"channel":"Email","action":"Send targeted upgrade offer"}],
         "estimated_impact":{"conversion_rate_lift":0.08,"retention_improvement":0.10,"revenue":9.99}},
    ],
}

def get_playbooks(prediction: dict) -> dict:
    pbs = PLAYBOOKS.get(prediction["risk_segment"], PLAYBOOKS["medium_risk"])
    return {"recommended_playbooks": pbs,
            "best_playbook_id": pbs[0]["playbook_id"],
            "estimated_impact": pbs[0]["estimated_impact"]}

# ============================================================================
# CHAT ENGINE
# ============================================================================
def chat_response(msg: str, context: dict) -> str:
    m      = msg.lower()
    prob   = context.get("churn_probability", 0.5)
    risk   = context.get("risk_segment", "medium_risk")
    prob_s = f"{prob*100:.0f}%"

    if any(w in m for w in ["why","churn","risk","leave","cancel"]):
        return (f"Your churn risk is **{prob_s}** ({risk.replace('_',' ').title()}). "
                "Key factors include skip rate, ad exposure, and listening time. "
                "Would you like a detailed SHAP breakdown?")
    elif any(w in m for w in ["offer","help","suggest","recommend"]):
        return ("Based on your profile:\n"
                "1. 🎵 **30-day Premium free trial** — ad-free, offline, HD audio\n"
                "2. 🎧 **Personalised playlists** curated for you\n"
                "3. 🌍 **Genre Mix** to discover new music\n\nWould you like to activate any?")
    elif any(w in m for w in ["premium","upgrade","price","cost","plan","student"]):
        return ("**Spotify Plans:**\n"
                "- 🟢 **Premium** — $9.99/month · Ad-free · Offline · HD audio\n"
                "- 🎓 **Student** — $4.99/month · Same benefits at half price\n"
                "- 🆓 **Free** — Ads · Limited skips · Online only\n\n"
                f"Given your {risk.replace('_',' ')} status, a **free trial** is available!")
    elif any(w in m for w in ["skip","ads","listen","song","offline"]):
        return ("Your **skip rate** and **ad exposure** are strong churn indicators. "
                "Users with high skip rates often churn because recommendations don't match their taste. "
                "Upgrading to Premium removes ads and enables better personalisation.")
    elif any(w in m for w in ["hello","hi","hey","start"]):
        return (f"👋 Hello! I'm your Spotify Churn Assistant.\n\n"
                f"Your current risk: **{prob_s}** ({risk.replace('_',' ').title()})\n\n"
                "I can help you:\n"
                "- 🔍 Understand your churn risk factors\n"
                "- 🎯 Get personalised retention offers\n"
                "- 📊 Explain the SHAP prediction breakdown")
    elif any(w in m for w in ["thank","thanks","ok","great","good"]):
        return "You're welcome! 😊 Is there anything else I can help with?"
    else:
        return ("I can help with:\n"
                "- **Churn risk** explanation\n"
                "- **Personalised offers** and recommendations\n"
                "- **Premium & Student** plan questions\n\n"
                "Try: *Why might I churn?* or *What offers do you have?*")

# ============================================================================
# CHART HELPERS
# ============================================================================
def gauge_chart(value: float) -> go.Figure:
    color = "#ff4444" if value > 0.67 else "#ff9500" if value > 0.33 else "#1DB954"
    fig   = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value * 100,
        number={"suffix": "%", "font": {"color": "#ffffff", "size": 44, "family": "DM Sans"}},
        domain={"x": [0, 1], "y": [0, 1]},
        gauge={
            "axis":    {"range": [0, 100], "tickcolor": "#444", "tickfont": {"color":"#666","size":11}},
            "bar":     {"color": color, "thickness": 0.28},
            "bgcolor": "#141414",
            "borderwidth": 0,
            "steps":   [{"range": [0,  33], "color": "#0d1f14"},
                        {"range": [33, 67], "color": "#1f1500"},
                        {"range": [67, 100], "color": "#1f0505"}],
            "threshold": {"line": {"color": color, "width": 3},
                          "thickness": 0.85, "value": value * 100},
        },
    ))
    fig.update_layout(height=260, paper_bgcolor="rgba(0,0,0,0)",
                      margin=dict(t=20, b=10, l=30, r=30))
    return fig

def shap_chart(attributions: list) -> go.Figure:
    top = sorted(attributions, key=lambda x: abs(x["impact_percentage"]), reverse=True)[:8]
    top = sorted(top, key=lambda x: x["impact_percentage"])
    colors = ["#ff4444" if x["impact_percentage"] > 0 else "#1DB954" for x in top]
    fig = go.Figure(data=[go.Bar(
        y=[a["feature_name"] for a in top],
        x=[a["impact_percentage"] for a in top],
        orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=[f"{v['impact_percentage']:+.1f}%" for v in top],
        textposition="auto",
        textfont=dict(color="#fff", size=11),
    )])
    fig.update_layout(
        title=dict(text="SHAP Feature Attribution", font=dict(color="#1DB954", size=13)),
        height=320,
        margin=dict(l=170, r=30, t=50, b=30),
        showlegend=False,
        **{k: v for k, v in PLOTLY.items() if k != "margin"},
    )
    return fig

def history_chart(history: list) -> go.Figure:
    df  = pd.DataFrame(history)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["churn_probability"] * 100,
        mode="lines+markers", name="Churn Risk",
        line=dict(color="#1DB954", width=2.5, shape="spline"),
        marker=dict(size=7, color="#1DB954", line=dict(color="#0a0a0a", width=2)),
        fill="tozeroy", fillcolor="rgba(29,185,84,0.07)",
    ))
    fig.update_layout(
        title=dict(text="Churn Risk Trend", font=dict(color="#1DB954", size=13)),
        xaxis_title="Date", yaxis_title="Churn %",
        height=260, **PLOTLY,
    )
    return fig

def get_risk_emoji(r): return {"high_risk":"🔴","medium_risk":"🟠","low_risk":"🟢"}.get(r,"⚪")
def get_risk_badge(r):
    labels = {"high_risk":("HIGH RISK","high"),"medium_risk":("MEDIUM RISK","medium"),"low_risk":("LOW RISK","low")}
    label, cls = labels.get(r, ("UNKNOWN","low"))
    return f'<span class="badge badge-{cls}">{label}</span>'

# ============================================================================
# HELPER: get customer dict from real dataset row
# ============================================================================
def get_customer(df, user_id: str) -> dict:
    """Get a single customer's data from the real dataset by user_id."""
    row = df[df["user_id"] == user_id].iloc[0]
    return {
        "age":                   int(row["age"]),
        "listening_time":        float(row["listening_time"]),
        "songs_played_per_day":  int(row["songs_played_per_day"]),
        "skip_rate":             float(row["skip_rate"]),
        "ads_listened_per_week": int(row["ads_listened_per_week"]),
        "offline_listening":     float(row["offline_listening"]),
        "gender":                str(row["gender"]),
        "subscription_type":     str(row["subscription_type"]),
        "device_type":           str(row["device_type"]),
        "country":               str(row.get("country", "N/A")),
        "is_churned":            int(row.get("is_churned", -1)),
    }

# ============================================================================
# PAGE: HOME
# ============================================================================
def page_home(model, scaler, explainer, df):

    # ── Hero ──────────────────────────────────────────────────────────────
    model_badge = "✅ Model Active" if model else "❌ Model Missing"
    st.markdown(f"""
    <div class="hero-header">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;">
            <div>
                <div class="hero-title">🎵 Spotify Churn Guard</div>
                <div class="hero-subtitle">
                    Spotify Customer Churn Prediction with XAI and Actionable Playbooks
                </div>
            </div>
            <div style="text-align:right;color:rgba(255,255,255,0.85);font-size:0.85rem;margin-top:0.3rem;">
                {model_badge}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🔍  Predict & Explain", "👥  Customer Profile", "📊  Analytics"])

    # ── TAB 1: PREDICT ────────────────────────────────────────────────────
    with tab1:
        if model is None:
            st.markdown('<div style="background:#ff333318;border:1px solid #ff3333;border-radius:12px;padding:1rem 1.5rem;color:#ff5555;">⚠️ No model file found. Add spotify_churn_model.pkl to your project folder and redeploy.</div>', unsafe_allow_html=True)
        elif df is None:
            st.markdown('<div style="background:#ff333318;border:1px solid #ff3333;border-radius:12px;padding:1rem 1.5rem;color:#ff5555;">⚠️ Dataset not found. Add spotify dataset.csv to project folder.</div>', unsafe_allow_html=True)
        else:

            all_ids = df["user_id"].tolist()
            col_sel, col_btn = st.columns([3, 1])
            with col_sel:
                selected_uid = st.selectbox(
                    "Customer ID", all_ids,
                    key="tab1_uid", label_visibility="collapsed"
                )
            with col_btn:
                predict_clicked = st.button("🔮 Predict", use_container_width=True, key="tab1_predict")

            # Auto-predict when selection changes OR button clicked
            if predict_clicked or st.session_state.get("tab1_last_uid") != str(selected_uid):
                st.session_state.tab1_last_uid = str(selected_uid)
                customer = get_customer(df, str(selected_uid))
                inputs = {k: v for k, v in customer.items()
                          if k not in ["country", "is_churned"]}
                with st.spinner(f"Analysing user {selected_uid}..."):
                    prediction = make_prediction(model, scaler, str(selected_uid), inputs)
                if prediction:
                    st.session_state.last_prediction = prediction

            st.markdown("---")
            customer = get_customer(df, str(selected_uid))

            col_form, col_result = st.columns([1, 1], gap="large")

            with col_form:
                st.markdown('<div class="section-title">🎯 Churn-Related Features</div>', unsafe_allow_html=True)
                # Show only churn-relevant fields as clean display cards
                churn_fields = [
                    ("⏭️ Skip Rate",          f"{customer['skip_rate']*100:.0f}%",
                     "High skip = poor recommendations"),
                    ("📢 Ads Per Week",        str(customer["ads_listened_per_week"]),
                     "More ads = higher frustration"),
                    ("⏱️ Listen Time/day",    f"{customer['listening_time']} hrs",
                     "Low listening = disengagement"),
                    ("🎶 Songs Per Day",       str(customer["songs_played_per_day"]),
                     "Low songs = low engagement"),
                    ("📶 Offline Hours",       f"{customer['offline_listening']} hrs",
                     "Low offline = less Premium value"),
                    ("🎵 Subscription",        customer["subscription_type"],
                     "Free users churn more often"),
                ]
                rows = [churn_fields[i:i+2] for i in range(0, len(churn_fields), 2)]
                for row in rows:
                    cols = st.columns(2)
                    for col, (label, value, hint) in zip(cols, row):
                        with col:
                            st.markdown(f"""
                            <div style="background:#141414;border:1px solid #252525;
                                        border-radius:10px;padding:0.9rem 1rem;margin-bottom:0.6rem;">
                                <div style="color:#1DB954;font-size:0.7rem;font-weight:700;
                                            text-transform:uppercase;letter-spacing:1px;">
                                    {label}
                                </div>
                                <div style="color:#ffffff;font-size:1.3rem;font-weight:700;
                                            margin-top:0.3rem;">{value}</div>
                                <div style="color:#555;font-size:0.75rem;margin-top:0.3rem;">
                                    {hint}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

            with col_result:
                st.markdown('<div class="section-title">🎯 Prediction Result</div>', unsafe_allow_html=True)

                if st.session_state.get("last_prediction"):
                    pred  = st.session_state.last_prediction
                    prob  = pred["churn_probability"]
                    risk  = pred["risk_segment"]
                    label = pred["prediction_label"]
                    risk_color = "#ff4444" if risk=="high_risk" else "#ff9500" if risk=="medium_risk" else "#1DB954"
                    verdict    = "⚠️ Will Churn"  if label==1 else "✅ Will Retain"

                    # 3 metric cards with full text visible
                    st.markdown(f"""
                    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-bottom:1rem;">
                        <div style="background:#141414;border:1px solid #252525;border-radius:12px;
                                    padding:1rem;text-align:center;">
                            <div style="color:#888;font-size:0.7rem;text-transform:uppercase;
                                        letter-spacing:1px;font-weight:600;">Churn Risk</div>
                            <div style="color:{risk_color};font-size:1.8rem;font-weight:700;
                                        margin-top:0.3rem;">{prob*100:.1f}%</div>
                        </div>
                        <div style="background:#141414;border:1px solid #252525;border-radius:12px;
                                    padding:1rem;text-align:center;">
                            <div style="color:#888;font-size:0.7rem;text-transform:uppercase;
                                        letter-spacing:1px;font-weight:600;">Confidence</div>
                            <div style="color:#ffffff;font-size:1.8rem;font-weight:700;
                                        margin-top:0.3rem;">{pred['confidence_score']*100:.0f}%</div>
                        </div>
                        <div style="background:#141414;border:1px solid {risk_color}55;border-radius:12px;
                                    padding:1rem;text-align:center;">
                            <div style="color:#888;font-size:0.7rem;text-transform:uppercase;
                                        letter-spacing:1px;font-weight:600;">Verdict</div>
                            <div style="color:{risk_color};font-size:1rem;font-weight:700;
                                        margin-top:0.3rem;">{verdict}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown(
                        f"**Risk Level:** {get_risk_badge(risk)}&nbsp;&nbsp;"
                        f"**{get_risk_emoji(risk)} {risk.replace('_',' ').title()}**",
                        unsafe_allow_html=True
                    )
                    st.plotly_chart(gauge_chart(prob), use_container_width=True)
                else:
                    st.markdown("""
                    <div style="background:#141414;border:1px dashed #333;border-radius:16px;
                                 padding:3rem;text-align:center;">
                        <div style="font-size:3rem;margin-bottom:1rem;">🎯</div>
                        <div style="font-size:1rem;color:#888;">Select a customer above to see prediction</div>
                    </div>
                    """, unsafe_allow_html=True)

            # ── EXPLANATION & PLAYBOOKS ───────────────────────────────────────
            if st.session_state.get("last_prediction"):
                pred = st.session_state.last_prediction
                st.markdown("---")
                col_exp, col_pb = st.columns(2, gap="large")

                with col_exp:
                    st.markdown('<div class="section-title">📖 XAI — SHAP Explanation</div>', unsafe_allow_html=True)
                    if st.button("Generate SHAP Explanation", use_container_width=True, key="explain_btn"):
                        if explainer is None:
                            st.warning("⚠️ SHAP unavailable for this model type. Showing rule-based insights.")
                            for i in _build_insights([], pred["risk_segment"]):
                                st.success(i)
                        else:
                            with st.spinner("Computing SHAP values..."):
                                explanation = make_explanation(explainer, pred)
                            if explanation:
                                st.info(f"**Summary:** {explanation['summary']}")
                                fig = shap_chart(explanation["feature_attributions"])
                                st.plotly_chart(fig, use_container_width=True)
                                st.markdown("**🔑 Key Drivers:**")
                                for d in explanation["key_drivers"]:
                                    st.markdown(f"&nbsp;&nbsp;&nbsp;• {d}")
                                st.markdown("**💡 Actionable Insights:**")
                                for i in explanation["actionable_insights"]:
                                    st.success(i)

                with col_pb:
                    st.markdown('<div class="section-title">🎬 Playbook Recommendations</div>', unsafe_allow_html=True)
                    if st.button("Get Playbook Recommendations", use_container_width=True, key="playbook_btn"):
                        pb = get_playbooks(pred)
                        st.success(f"✅ Best Match: **{pb['best_playbook_id']}**")
                        for p in pb["recommended_playbooks"]:
                            with st.expander(f"📋 {p['name']}  ·  Priority {p['priority']}", expanded=True):
                                st.caption(p["description"])
                                c1, c2, c3 = st.columns(3)
                                st.markdown(f"""
                                <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin:0.8rem 0;">
                                    <div style="background:#0d1f14;border:1px solid #1DB95444;border-radius:10px;
                                                padding:0.8rem;text-align:center;">
                                        <div style="color:#1DB954;font-size:0.7rem;font-weight:700;
                                                    text-transform:uppercase;letter-spacing:1px;">Conversion Lift</div>
                                        <div style="color:#ffffff;font-size:1.4rem;font-weight:700;margin-top:0.3rem;">
                                            {p['estimated_impact']['conversion_rate_lift']:.0%}
                                        </div>
                                    </div>
                                    <div style="background:#1a1000;border:1px solid #ff950044;border-radius:10px;
                                                padding:0.8rem;text-align:center;">
                                        <div style="color:#ff9500;font-size:0.7rem;font-weight:700;
                                                    text-transform:uppercase;letter-spacing:1px;">Retention Boost</div>
                                        <div style="color:#ffffff;font-size:1.4rem;font-weight:700;margin-top:0.3rem;">
                                            {p['estimated_impact']['retention_improvement']:.0%}
                                        </div>
                                    </div>
                                    <div style="background:#0a0a1f;border:1px solid #4a9eff44;border-radius:10px;
                                                padding:0.8rem;text-align:center;">
                                        <div style="color:#4a9eff;font-size:0.7rem;font-weight:700;
                                                    text-transform:uppercase;letter-spacing:1px;">Revenue/User</div>
                                        <div style="color:#ffffff;font-size:1.4rem;font-weight:700;margin-top:0.3rem;">
                                            ${p['estimated_impact']['revenue']:.2f}
                                        </div>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                                for a in p["actions"]:
                                    st.markdown(f"**Step {a['step']}** `{a['channel']}` — {a['action']}")

    # ── TAB 2: CUSTOMER PROFILE ───────────────────────────────────────────
    with tab2:
        st.markdown('<div class="section-title">Customer Profile Explorer</div>', unsafe_allow_html=True)

        if df is None:
            st.markdown('<div style="background:#ff333318;border:1px solid #ff3333;border-radius:12px;padding:1rem 1.5rem;color:#ff5555;">⚠️ Dataset not found. Add spotify dataset.csv to project folder.</div>', unsafe_allow_html=True)
        else:
            all_ids = df["user_id"].tolist()
            profile_uid = st.selectbox(
                "Select Customer ID", all_ids,
                key="profile_uid", label_visibility="collapsed"
            )
            customer = get_customer(df, str(profile_uid))

            # ── Top info banner ──
            sub_color = "#1DB954" if customer["subscription_type"]=="Premium" else \
                        "#4a9eff" if customer["subscription_type"]=="Student" else "#ff9500"
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#141414,#1c1c1c);
                        border:1px solid #252525;border-radius:16px;
                        padding:1.5rem 2rem;margin:1rem 0;">
                <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:1rem;">
                    <div>
                        <div style="color:#1DB954;font-size:0.75rem;font-weight:700;
                                    text-transform:uppercase;letter-spacing:2px;">Customer ID</div>
                        <div style="color:#ffffff;font-size:1.8rem;font-weight:700;margin-top:0.2rem;">
                            {profile_uid}
                        </div>
                    </div>
                    <div style="display:flex;gap:1.5rem;flex-wrap:wrap;">
                        <div style="text-align:center;">
                            <div style="color:#888;font-size:0.7rem;text-transform:uppercase;letter-spacing:1px;">Age</div>
                            <div style="color:#fff;font-size:1.4rem;font-weight:700;">{customer['age']}</div>
                        </div>
                        <div style="text-align:center;">
                            <div style="color:#888;font-size:0.7rem;text-transform:uppercase;letter-spacing:1px;">Gender</div>
                            <div style="color:#fff;font-size:1.4rem;font-weight:700;">{customer['gender']}</div>
                        </div>
                        <div style="text-align:center;">
                            <div style="color:#888;font-size:0.7rem;text-transform:uppercase;letter-spacing:1px;">Country</div>
                            <div style="color:#fff;font-size:1.4rem;font-weight:700;">{customer['country']}</div>
                        </div>
                        <div style="text-align:center;">
                            <div style="color:#888;font-size:0.7rem;text-transform:uppercase;letter-spacing:1px;">Device</div>
                            <div style="color:#fff;font-size:1.4rem;font-weight:700;">{customer['device_type']}</div>
                        </div>
                        <div style="text-align:center;">
                            <div style="color:#888;font-size:0.7rem;text-transform:uppercase;letter-spacing:1px;">Plan</div>
                            <div style="color:{sub_color};font-size:1.4rem;font-weight:700;">{customer['subscription_type']}</div>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # ── All detail metric cards ──
            st.markdown('<div class="section-title">📊 Full Activity Details</div>', unsafe_allow_html=True)
            c1, c2, c3, c4, c5, c6 = st.columns(6)
            with c1: st.metric("Age",              customer["age"])
            with c2: st.metric("Listen Time/day",  f"{customer['listening_time']} hrs")
            with c3: st.metric("Songs/day",         customer["songs_played_per_day"])
            with c4: st.metric("Skip Rate",         f"{customer['skip_rate']*100:.0f}%")
            with c5: st.metric("Ads/week",          customer["ads_listened_per_week"])
            with c6: st.metric("Offline Hours",     f"{customer['offline_listening']} hrs")

            st.markdown("<br>", unsafe_allow_html=True)

            # ── Charts row ──
            col1, col2, col3 = st.columns(3, gap="medium")

            with col1:
                st.markdown('<div class="section-title">⏱️ Time Breakdown</div>', unsafe_allow_html=True)
                idle = max(0, 5 - customer["listening_time"] - customer["offline_listening"])
                fig = px.pie(
                    pd.DataFrame({
                        "Activity": ["Listening","Offline","Idle"],
                        "Hours":    [customer["listening_time"], customer["offline_listening"], idle]
                    }),
                    values="Hours", names="Activity", hole=0.5,
                    color_discrete_map={"Listening":"#1DB954","Offline":"#4a9eff","Idle":"#222222"})
                fig.update_layout(**PLOTLY, height=260,
                    annotations=[dict(text="Time",x=0.5,y=0.5,
                                      font_size=12,font_color="#ccc",showarrow=False)])
                fig.update_traces(textfont=dict(color="#fff",size=12),
                                  textinfo="label+percent")
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.markdown('<div class="section-title">📢 Engagement Metrics</div>', unsafe_allow_html=True)
                eng_labels = ["Listen\nTime","Songs\n/day","Skip\nRate","Ads\n/week","Offline"]
                eng_values = [
                    min(100, customer["listening_time"]/24*100),
                    min(100, customer["songs_played_per_day"]/100*100),
                    customer["skip_rate"]*100,
                    min(100, customer["ads_listened_per_week"]/50*100),
                    min(100, customer["offline_listening"]/10*100),
                ]
                colors = ["#1DB954","#1DB954","#ff4444","#ff9500","#4a9eff"]
                fig = go.Figure(data=[go.Bar(
                    x=eng_labels, y=eng_values,
                    marker=dict(color=colors, line=dict(width=0)),
                    text=[f"{v:.0f}%" for v in eng_values],
                    textposition="auto", textfont=dict(color="#fff", size=11),
                )])
                fig.update_layout(**PLOTLY, height=260, showlegend=False,
                                  yaxis=dict(range=[0,110], gridcolor="#1e1e1e"))
                st.plotly_chart(fig, use_container_width=True)

            with col3:
                st.markdown('<div class="section-title">📱 Activity Profile</div>', unsafe_allow_html=True)
                act_labels = ["Songs/day","Ads/week","Offline hrs","Listen hrs"]
                act_values = [
                    customer["songs_played_per_day"],
                    customer["ads_listened_per_week"],
                    customer["offline_listening"],
                    customer["listening_time"],
                ]
                fig = go.Figure(data=[go.Bar(
                    y=act_labels, x=act_values, orientation="h",
                    marker=dict(
                        color=["#1DB954","#ff9500","#4a9eff","#1DB954"],
                        line=dict(width=0)),
                    text=[str(v) for v in act_values],
                    textposition="auto", textfont=dict(color="#fff", size=11),
                )])
                fig.update_layout(**PLOTLY, height=260, showlegend=False,
                                  margin=dict(l=90,r=20,t=30,b=20))
                st.plotly_chart(fig, use_container_width=True)

            # ── Full feature table ──
            st.markdown('<div class="section-title">📋 Complete Feature Profile</div>', unsafe_allow_html=True)
            all_fields = [
                {"Feature": "Customer ID",       "Value": str(profile_uid),                        "Category": "Identity"},
                {"Feature": "Age",               "Value": str(customer["age"]),                    "Category": "Demographics"},
                {"Feature": "Gender",            "Value": customer["gender"],                      "Category": "Demographics"},
                {"Feature": "Country",           "Value": customer["country"],                     "Category": "Demographics"},
                {"Feature": "Subscription",      "Value": customer["subscription_type"],           "Category": "Account"},
                {"Feature": "Device",            "Value": customer["device_type"],                 "Category": "Account"},
                {"Feature": "Listen Time/day",   "Value": f"{customer['listening_time']} hrs",     "Category": "Engagement"},
                {"Feature": "Songs Per Day",     "Value": str(customer["songs_played_per_day"]),   "Category": "Engagement"},
                {"Feature": "Offline Hours",     "Value": f"{customer['offline_listening']} hrs",  "Category": "Engagement"},
                {"Feature": "Skip Rate",         "Value": f"{customer['skip_rate']*100:.0f}%",     "Category": "Behaviour"},
                {"Feature": "Ads Per Week",      "Value": str(customer["ads_listened_per_week"]),  "Category": "Behaviour"},
                {"Feature": "Churned",           "Value": "Yes" if customer["is_churned"]==1 else "No", "Category": "Status"},
            ]
            st.dataframe(
                pd.DataFrame(all_fields),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Feature":  st.column_config.TextColumn("Feature",  width="medium"),
                    "Value":    st.column_config.TextColumn("Value",    width="medium"),
                    "Category": st.column_config.TextColumn("Category", width="small"),
                }
            )

    # ── TAB 3: ANALYTICS ─────────────────────────────────────────────────
    with tab3:
        st.markdown('<div class="section-title">📊 Platform Analytics</div>', unsafe_allow_html=True)
        if df is None:
            st.markdown("**⚠️ Dataset not found**")
        else:
            total   = len(df)
            churned = int(df["is_churned"].sum())
            rate    = churned / total * 100
            skip    = df["skip_rate"].mean() * 100
            listen  = df["listening_time"].mean()

            kpi_html = (
                '<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin-bottom:1.5rem;">'
                '<div style="background:#141414;border:1px solid #1DB95433;border-radius:12px;padding:1rem;text-align:center;">'
                '<div style="color:#888;font-size:0.7rem;text-transform:uppercase;">Total Users</div>'
                f'<div style="color:#1DB954;font-size:1.8rem;font-weight:700;">{total:,}</div></div>'
                '<div style="background:#141414;border:1px solid #ff333333;border-radius:12px;padding:1rem;text-align:center;">'
                '<div style="color:#888;font-size:0.7rem;text-transform:uppercase;">Churned</div>'
                f'<div style="color:#ff4444;font-size:1.8rem;font-weight:700;">{churned:,}</div></div>'
                '<div style="background:#141414;border:1px solid #ff950033;border-radius:12px;padding:1rem;text-align:center;">'
                '<div style="color:#888;font-size:0.7rem;text-transform:uppercase;">Churn Rate</div>'
                f'<div style="color:#ff9500;font-size:1.8rem;font-weight:700;">{rate:.1f}%</div></div>'
                '<div style="background:#141414;border:1px solid #25252555;border-radius:12px;padding:1rem;text-align:center;">'
                '<div style="color:#888;font-size:0.7rem;text-transform:uppercase;">Avg Skip</div>'
                f'<div style="color:#fff;font-size:1.8rem;font-weight:700;">{skip:.1f}%</div></div>'
                '<div style="background:#141414;border:1px solid #4a9eff33;border-radius:12px;padding:1rem;text-align:center;">'
                '<div style="color:#888;font-size:0.7rem;text-transform:uppercase;">Avg Listen</div>'
                f'<div style="color:#4a9eff;font-size:1.8rem;font-weight:700;">{listen:.1f}h</div></div>'
                '</div>'
            )
            st.markdown(kpi_html, unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                st.markdown('<div class="section-title">🔴 Churn Distribution</div>', unsafe_allow_html=True)
                fig = px.pie(
                    pd.DataFrame({"Status":["Retained","Churned"],"Count":[total-churned,churned]}),
                    values="Count", names="Status", hole=0.55,
                    color_discrete_map={"Retained":"#1DB954","Churned":"#ff3333"})
                fig.update_layout(**PLOTLY, height=280,
                    annotations=[dict(text=f"{rate:.0f}%<br>Churn",x=0.5,y=0.5,
                                      font_size=13,font_color="#ccc",showarrow=False)])
                fig.update_traces(textfont=dict(color="#fff",size=13),textinfo="label+percent")
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                st.markdown('<div class="section-title">🎵 Subscription Breakdown</div>', unsafe_allow_html=True)
                sub = df["subscription_type"].value_counts().reset_index()
                sub.columns = ["Plan","Count"]
                fig = px.bar(sub, x="Plan", y="Count", color="Plan",
                    color_discrete_map={"Free":"#ff9500","Premium":"#1DB954","Student":"#4a9eff","Family":"#aa44ff"})
                fig.update_layout(**PLOTLY, height=280, showlegend=False)
                fig.update_traces(texttemplate="%{y:,}",textposition="outside",textfont=dict(color="#fff"))
                st.plotly_chart(fig, use_container_width=True)

            col1, col2 = st.columns(2)
            with col1:
                st.markdown('<div class="section-title">📊 Churn by Subscription</div>', unsafe_allow_html=True)
                cs = df.groupby("subscription_type")["is_churned"].mean().reset_index()
                cs.columns = ["Plan","Rate"]
                cs["Rate"] = (cs["Rate"]*100).round(1)
                cs = cs.sort_values("Rate",ascending=False)
                fig = go.Figure(go.Bar(
                    x=cs["Plan"], y=cs["Rate"],
                    marker=dict(color=cs["Rate"].tolist(),
                        colorscale=[[0,"#1DB954"],[0.5,"#ff9500"],[1,"#ff3333"]],
                        line=dict(width=0)),
                    text=[f"{v:.1f}%" for v in cs["Rate"]],
                    textposition="auto", textfont=dict(color="#fff")))
                fig.update_layout(**PLOTLY, height=280, showlegend=False,
                    yaxis=dict(range=[0,100],gridcolor="#1e1e1e"))
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                st.markdown('<div class="section-title">📱 Churn by Device</div>', unsafe_allow_html=True)
                cd = df.groupby("device_type")["is_churned"].mean().reset_index()
                cd.columns = ["Device","Rate"]
                cd["Rate"] = (cd["Rate"]*100).round(1)
                fig = go.Figure(go.Bar(
                    x=cd["Device"], y=cd["Rate"],
                    marker=dict(color=["#1DB954","#4a9eff","#ff9500"],line=dict(width=0)),
                    text=[f"{v:.1f}%" for v in cd["Rate"]],
                    textposition="auto", textfont=dict(color="#fff")))
                fig.update_layout(**PLOTLY, height=280, showlegend=False,
                    yaxis=dict(range=[0,100],gridcolor="#1e1e1e"))
                st.plotly_chart(fig, use_container_width=True)

            col1, col2 = st.columns(2)
            with col1:
                st.markdown('<div class="section-title">👥 Age Distribution</div>', unsafe_allow_html=True)
                fig = go.Figure()
                fig.add_trace(go.Histogram(x=df[df["is_churned"]==0]["age"],name="Retained",
                    nbinsx=20,marker=dict(color="#1DB954",opacity=0.8,line=dict(width=0))))
                fig.add_trace(go.Histogram(x=df[df["is_churned"]==1]["age"],name="Churned",
                    nbinsx=20,marker=dict(color="#ff3333",opacity=0.8,line=dict(width=0))))
                fig.update_layout(**PLOTLY,height=280,barmode="overlay",
                    legend=dict(font=dict(color="#ccc"),bgcolor="rgba(0,0,0,0)"),
                    xaxis_title="Age",yaxis_title="Count")
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                st.markdown('<div class="section-title">⏭️ Skip Rate vs Listen Time</div>', unsafe_allow_html=True)
                samp = df.sample(min(500,len(df)),random_state=42)
                fig = px.scatter(samp,x="skip_rate",y="listening_time",
                    color=samp["is_churned"].map({0:"Retained",1:"Churned"}),
                    color_discrete_map={"Retained":"#1DB954","Churned":"#ff3333"},opacity=0.6)
                fig.update_layout(**PLOTLY,height=280,
                    xaxis_title="Skip Rate",yaxis_title="Listen Time (hrs)",
                    legend=dict(font=dict(color="#ccc"),bgcolor="rgba(0,0,0,0)"))
                st.plotly_chart(fig, use_container_width=True)

            col1, col2 = st.columns(2)
            with col1:
                st.markdown('<div class="section-title">👤 Churn by Gender</div>', unsafe_allow_html=True)
                cg = df.groupby("gender")["is_churned"].mean().reset_index()
                cg.columns = ["Gender","Rate"]
                cg["Rate"] = (cg["Rate"]*100).round(1)
                fig = px.pie(cg,values="Rate",names="Gender",hole=0.4,
                    color_discrete_sequence=["#1DB954","#4a9eff","#ff9500","#aa44ff"])
                fig.update_layout(**PLOTLY,height=280)
                fig.update_traces(textfont=dict(color="#fff",size=12),textinfo="label+percent")
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                st.markdown('<div class="section-title">🌍 Top 10 Countries</div>', unsafe_allow_html=True)
                tc = df["country"].value_counts().head(10).reset_index()
                tc.columns = ["Country","Users"]
                fig = go.Figure(go.Bar(
                    y=tc["Country"],x=tc["Users"],orientation="h",
                    marker=dict(color=tc["Users"].tolist(),
                        colorscale=[[0,"#0d2a18"],[1,"#1DB954"]],line=dict(width=0)),
                    text=tc["Users"].tolist(),textposition="auto",textfont=dict(color="#fff")))
                fig.update_layout(**PLOTLY,height=280,
                    margin=dict(l=70,r=20,t=30,b=20),showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

    # ── CHAT ──────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown('<div class="section-title">💬 AI Chat Assistant</div>', unsafe_allow_html=True)

    with st.container():
        for message in st.session_state.chat_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    user_input = st.chat_input("Ask about churn risk, offers, or plans...")
    if user_input:
        st.session_state.chat_messages.append({"role":"user","content":user_input})
        context = {}
        if st.session_state.last_prediction:
            context = {
                "churn_probability": st.session_state.last_prediction.get("churn_probability",0.5),
                "risk_segment":      st.session_state.last_prediction.get("risk_segment","medium_risk"),
            }
        with st.spinner("Thinking..."):
            reply = chat_response(user_input, context)
        st.session_state.chat_messages.append({"role":"assistant","content":reply})
        st.rerun()

# ============================================================================
# PAGE: HELP
# ============================================================================
def page_help():
    st.markdown("""
    <div class="hero-header">
        <div class="hero-title">📚 Help & Documentation</div>
        <div class="hero-subtitle">Everything you need to know about Spotify Churn Guard</div>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["Getting Started", "Model & Features", "FAQ"])

    with tab1:
        st.markdown("""
### How to Use This App

**1. Run a Prediction**
Fill in the user feature inputs on the left panel of the Predict tab.
Click **Run Churn Prediction** — the gauge chart shows the risk score instantly.

**2. View SHAP Explanation**
Click **Generate SHAP Explanation** to see a colour-coded bar chart showing
which features increase (red) or decrease (green) churn risk.

**3. Get Playbook Recommendations**
Click **Get Playbook Recommendations** to see ranked intervention strategies
with conversion lift, retention improvement, and revenue impact estimates.

**4. Chat Assistant**
Ask the AI assistant questions about churn risk, Spotify plans, or offers.
It automatically uses your latest prediction as context.

**5. Analytics Tab**
View platform-wide churn metrics, risk distribution, and playbook success rates.
        """)

    with tab2:
        st.markdown("""
### Model Details

| Item | Detail |
|---|---|
| Primary model | `spotify_churn_model.pkl` |
| Type | HistGradientBoostingClassifier |
| Explainability | SHAP TreeExplainer |
| Scaler | StandardScaler (`scaler.pkl`) |
| Features | 15 columns (see below) |

### The 15 Features
| Feature | Description |
|---|---|
| age | User age |
| listening_time | Hours listened per day |
| songs_played_per_day | Daily song count |
| skip_rate | Fraction of songs skipped |
| ads_listened_per_week | Weekly ad exposure |
| offline_listening | Offline hours per day |
| ad_stress | Derived: ads × skip_rate |
| skip_intensity | Derived: skip_rate × songs/day |
| gender_Male / gender_Other | One-hot encoded gender |
| subscription_type_* | One-hot: Free / Premium / Student |
| device_type_Mobile / Web | One-hot encoded device |
        """)

    with tab3:
        st.markdown("""
### FAQ

**Q: What does churn probability mean?**
The likelihood (0–100%) that a user will cancel their Spotify subscription.

**Q: What are the risk segments?**
- 🟢 Low Risk (0–33%) — Likely to stay
- 🟠 Medium Risk (33–67%) — Needs engagement
- 🔴 High Risk (67%+) — Immediate action required

**Q: What are ad_stress and skip_intensity?**
These are derived features computed automatically:
- `ad_stress = ads_listened_per_week × skip_rate`
- `skip_intensity = skip_rate × songs_played_per_day`

**Q: Does this need a backend server?**
No. Everything runs inside Streamlit Cloud — model, SHAP, playbooks, and chat are all self-contained.

**Q: Why does the scaler show a warning?**
The scaler was saved with a newer sklearn version. This is a version mismatch warning only — it does not affect predictions.
        """)

# ============================================================================
# MAIN
# ============================================================================
def main():
    if "page"            not in st.session_state: st.session_state.page = "home"
    if "last_prediction" not in st.session_state: st.session_state.last_prediction = {}
    if "last_inputs"     not in st.session_state: st.session_state.last_inputs = {}
    if "tab1_last_uid"   not in st.session_state: st.session_state.tab1_last_uid = ""
    if "show_profile"    not in st.session_state: st.session_state.show_profile = False
    if "chat_session_id" not in st.session_state: st.session_state.chat_session_id = f"s_{int(time.time())}"
    if "chat_messages"   not in st.session_state: st.session_state.chat_messages = []

    model     = load_model()
    scaler    = load_scaler()
    explainer = load_explainer(model) if model else None
    df        = load_dataset()

    with st.sidebar:
        st.markdown("## 🎵 Navigation")
        page = st.radio("", ["Home", "Help & Docs"], index=0, label_visibility="collapsed")
        st.session_state.page = "home" if page == "Home" else "help"

        st.markdown("---")
        st.markdown("### ⚙️ System Status")

        model_status  = "✅ Model: Loaded"        if model    else "❌ Model: Not Found"
        scaler_status = "✅ Scaler: Ready"         if scaler   else "⚠️ Scaler: Missing"
        shap_status   = "✅ SHAP: Ready"           if explainer else "⚠️ SHAP: Unavailable"
        data_status   = f"✅ Dataset: {len(df):,} users" if df is not None else "❌ Dataset: Not Found"

        model_color  = "#1DB954" if model    else "#ff4444"
        scaler_color = "#1DB954" if scaler   else "#ff9500"
        shap_color   = "#1DB954" if explainer else "#ff9500"
        data_color   = "#1DB954" if df is not None else "#ff4444"

        st.markdown(f"""
<div style="display:flex;flex-direction:column;gap:8px;margin-top:4px;">
    <div style="background:#141414;border:1px solid {model_color}33;border-radius:8px;
                padding:8px 12px;color:{model_color};font-size:0.88rem;font-weight:600;">
        {model_status}
    </div>
    <div style="background:#141414;border:1px solid {data_color}33;border-radius:8px;
                padding:8px 12px;color:{data_color};font-size:0.88rem;font-weight:600;">
        {data_status}
    </div>
    <div style="background:#141414;border:1px solid {scaler_color}33;border-radius:8px;
                padding:8px 12px;color:{scaler_color};font-size:0.88rem;font-weight:600;">
        {scaler_status}
    </div>
    <div style="background:#141414;border:1px solid {shap_color}33;border-radius:8px;
                padding:8px 12px;color:{shap_color};font-size:0.88rem;font-weight:600;">
        {shap_status}
    </div>
</div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("""
<div style="color:#888;font-size:0.85rem;line-height:1.8;">
<strong style="color:#e0e0e0;">Spotify Churn Guard</strong><br>
v2.0 — Standalone · No backend<br><br>
🔮 15-feature ML model<br>
📖 SHAP explainability<br>
🎬 Playbook engine<br>
💬 Chat assistant
</div>
        """, unsafe_allow_html=True)

    if st.session_state.page == "home":
        page_home(model, scaler, explainer, df)
    else:
        page_help()

if __name__ == "__main__":
    main()
