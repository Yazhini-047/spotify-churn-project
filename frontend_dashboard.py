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
    background: #1a1a1a !important;
    border: 1px solid #1DB95455 !important;
    border-radius: 50px !important;
    padding: 4px 8px !important;
}
[data-testid="stChatInputContainer"] textarea {
    background: transparent !important;
    color: #e0e0e0 !important;
}
/* Fix white bottom bar */
.stChatFloatingInputContainer {
    background: #0a0a0a !important;
    border-top: 1px solid #1e1e1e !important;
    padding: 1rem 2rem !important;
}
section[data-testid="stBottom"] {
    background: #0a0a0a !important;
    border-top: 1px solid #1e1e1e !important;
}
section[data-testid="stBottom"] > div {
    background: #0a0a0a !important;
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

/* Nuclear fix for white chat bar */
section[data-testid="stBottom"]                       { background: #0a0a0a !important; }
section[data-testid="stBottom"] > div                 { background: #0a0a0a !important; }
section[data-testid="stBottom"] > div > div           { background: #0a0a0a !important; }
.stChatFloatingInputContainer                         { background: #0a0a0a !important; border-top: 1px solid #1e1e1e !important; }
.stChatFloatingInputContainer > div                   { background: #0a0a0a !important; }
[data-testid="stChatInputContainer"]                  { background: #161616 !important; border: 1px solid #1DB95466 !important; border-radius: 50px !important; }
[data-testid="stChatInputContainer"] textarea         { background: transparent !important; color: #e0e0e0 !important; }
[data-testid="stChatInputContainer"] textarea::placeholder { color: #555 !important; }


    /* Sidebar toggle CSS - shows hamburger when sidebar collapsed */
    [data-testid="stSidebarCollapsedControl"] button {
        background: #1DB954 !important;
        color: #000 !important;
        border-radius: 8px !important;
        font-size: 20px !important;
        width: 40px !important;
        height: 40px !important;
        border: none !important;
        box-shadow: 0 2px 10px rgba(29,185,84,0.4) !important;
    }
    [data-testid="stSidebarCollapsedControl"] button:hover {
        background: #22d160 !important;
        transform: scale(1.1) !important;
    }

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

    model_badge = "✅ Model Active" if model else "❌ Model Missing"
    st.markdown(f'<div class="hero-header"><div style="display:flex;justify-content:space-between;align-items:flex-start;"><div><div class="hero-title">🎵 Spotify Churn Guard</div><div class="hero-subtitle">Spotify Customer Churn Prediction with XAI and Actionable Playbooks</div></div><div style="text-align:right;color:rgba(255,255,255,0.85);font-size:0.85rem;">{model_badge}</div></div></div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🔍  Predict & Explain", "👥  Customer Profile", "📊  Analytics"])

    # ================================================================
    # TAB 1 - PREDICT & EXPLAIN
    # ================================================================
    with tab1:
        if model is None or df is None:
            st.markdown("**⚠️ Model or dataset not loaded.**")
        else:
            all_ids = df["user_id"].tolist()
            col_sel, col_btn = st.columns([3, 1])
            with col_sel:
                selected_uid = st.selectbox("Customer ID", all_ids, key="tab1_uid", label_visibility="collapsed")
            with col_btn:
                predict_clicked = st.button("🔮 Predict", use_container_width=True, key="tab1_predict")

            if predict_clicked or st.session_state.get("tab1_last_uid") != str(selected_uid):
                st.session_state.tab1_last_uid = str(selected_uid)
                customer = get_customer(df, str(selected_uid))
                inputs = {k: v for k, v in customer.items() if k not in ["country","is_churned"]}
                with st.spinner(f"Analysing user {selected_uid}..."):
                    prediction = make_prediction(model, scaler, str(selected_uid), inputs)
                if prediction:
                    st.session_state.last_prediction = prediction

            st.markdown("---")
            customer = get_customer(df, str(selected_uid))
            col_form, col_result = st.columns([1, 1], gap="large")

            with col_form:
                st.markdown('<div class="section-title">🎯 Churn-Related Features</div>', unsafe_allow_html=True)
                churn_fields = [
                    ("⏭️ Skip Rate",       f"{customer['skip_rate']*100:.0f}%",     "High skip = poor recommendations"),
                    ("📢 Ads Per Week",     str(customer["ads_listened_per_week"]),    "More ads = higher frustration"),
                    ("⏱️ Listen Time/day", f"{customer['listening_time']} hrs",      "Low listening = disengagement"),
                    ("🎶 Songs Per Day",    str(customer["songs_played_per_day"]),     "Low songs = low engagement"),
                    ("📶 Offline Hours",    f"{customer['offline_listening']} hrs",  "Low offline = less Premium value"),
                    ("🎵 Subscription",     customer["subscription_type"],             "Free users churn more often"),
                ]
                rows = [churn_fields[i:i+2] for i in range(0, len(churn_fields), 2)]
                for row in rows:
                    cols = st.columns(2)
                    for col, (label, value, hint) in zip(cols, row):
                        with col:
                            st.markdown(f'<div style="background:#141414;border:1px solid #252525;border-radius:10px;padding:0.9rem 1rem;margin-bottom:0.6rem;"><div style="color:#1DB954;font-size:0.7rem;font-weight:700;text-transform:uppercase;">{label}</div><div style="color:#fff;font-size:1.3rem;font-weight:700;">{value}</div><div style="color:#555;font-size:0.75rem;">{hint}</div></div>', unsafe_allow_html=True)

            with col_result:
                st.markdown('<div class="section-title">🎯 Prediction Result</div>', unsafe_allow_html=True)
                if st.session_state.get("last_prediction"):
                    pred  = st.session_state.last_prediction
                    prob  = pred["churn_probability"]
                    risk  = pred["risk_segment"]
                    label = pred["prediction_label"]
                    risk_color = "#ff4444" if risk=="high_risk" else "#ff9500" if risk=="medium_risk" else "#1DB954"
                    verdict = "⚠️ Will Churn" if label==1 else "✅ Will Retain"
                    st.markdown(f'<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-bottom:1rem;"><div style="background:#141414;border:1px solid #252525;border-radius:12px;padding:1rem;text-align:center;"><div style="color:#888;font-size:0.7rem;text-transform:uppercase;font-weight:600;">Churn Risk</div><div style="color:{risk_color};font-size:1.8rem;font-weight:700;">{prob*100:.1f}%</div></div><div style="background:#141414;border:1px solid #252525;border-radius:12px;padding:1rem;text-align:center;"><div style="color:#888;font-size:0.7rem;text-transform:uppercase;font-weight:600;">Confidence</div><div style="color:#fff;font-size:1.8rem;font-weight:700;">{pred["confidence_score"]*100:.0f}%</div></div><div style="background:#141414;border:1px solid {risk_color}55;border-radius:12px;padding:1rem;text-align:center;"><div style="color:#888;font-size:0.7rem;text-transform:uppercase;font-weight:600;">Verdict</div><div style="color:{risk_color};font-size:1rem;font-weight:700;">{verdict}</div></div></div>', unsafe_allow_html=True)
                    st.markdown(f"**Risk Level:** {get_risk_badge(risk)}&nbsp;&nbsp;**{get_risk_emoji(risk)} {risk.replace('_',' ').title()}**", unsafe_allow_html=True)
                    st.plotly_chart(gauge_chart(prob), use_container_width=True)
                else:
                    st.markdown('<div style="background:#141414;border:1px dashed #333;border-radius:16px;padding:3rem;text-align:center;"><div style="font-size:3rem;">🎯</div><div style="font-size:1rem;color:#888;margin-top:0.5rem;">Select a customer to see prediction</div></div>', unsafe_allow_html=True)

            if st.session_state.get("last_prediction"):
                pred = st.session_state.last_prediction
                st.markdown("---")
                col_exp, col_pb = st.columns(2, gap="large")
                with col_exp:
                    st.markdown('<div class="section-title">📖 XAI — SHAP Explanation</div>', unsafe_allow_html=True)
                    if st.button("Generate SHAP Explanation", use_container_width=True, key="explain_btn"):
                        if explainer is None:
                            for i in _build_insights([], pred["risk_segment"]):
                                st.markdown(f'<div style="background:#1DB95418;border:1px solid #1DB95444;border-radius:8px;padding:0.6rem 1rem;color:#1DB954;margin:4px 0;">{i}</div>', unsafe_allow_html=True)
                        else:
                            with st.spinner("Computing SHAP values..."):
                                explanation = make_explanation(explainer, pred)
                            if explanation:
                                st.info(f"**Summary:** {explanation['summary']}")
                                fig = shap_chart(explanation["feature_attributions"])
                                if fig:
                                    st.plotly_chart(fig, use_container_width=True)
                                for i in explanation["actionable_insights"]:
                                    st.markdown(f'<div style="background:#1DB95418;border:1px solid #1DB95444;border-radius:8px;padding:0.6rem 1rem;color:#1DB954;margin:4px 0;">{i}</div>', unsafe_allow_html=True)
                with col_pb:
                    st.markdown('<div class="section-title">🎬 Playbook Recommendations</div>', unsafe_allow_html=True)
                    if st.button("Get Playbook Recommendations", use_container_width=True, key="playbook_btn"):
                        pb = get_playbooks(pred)
                        st.markdown(f"**🎯 Best Match:** `{pb['best_playbook_id']}`")
                        for p in pb["recommended_playbooks"]:
                            with st.expander(f"📋 {p['name']}  —  Priority {p['priority']}", expanded=True):
                                st.write(f"**Description:** {p['description']}")
                                col_a, col_b, col_c = st.columns(3)
                                with col_a:
                                    st.write(f"**Conversion Lift**")
                                    st.write(f"{p['estimated_impact']['conversion_rate_lift']:.0%}")
                                with col_b:
                                    st.write(f"**Retention Boost**")
                                    st.write(f"{p['estimated_impact']['retention_improvement']:.0%}")
                                with col_c:
                                    st.write(f"**Revenue / User**")
                                    st.write(f"${p['estimated_impact']['revenue']:.2f}")
                                st.write("**Action Steps:**")
                                for a in p["actions"]:
                                    st.write(f"  • Step {a['step']} [{a['channel']}]: {a['action']}")
    # ================================================================
    # TAB 2 - CUSTOMER PROFILE
    # ================================================================
    with tab2:
        st.markdown('<div class="section-title">Customer Profile Explorer</div>', unsafe_allow_html=True)
        if df is None:
            st.markdown("**⚠️ Dataset not found.**")
        else:
            all_ids2 = df["user_id"].tolist()
            profile_uid = st.selectbox("Select Customer ID", all_ids2, key="profile_uid", label_visibility="collapsed")
            customer2 = get_customer(df, str(profile_uid))
            sub_color = "#1DB954" if customer2["subscription_type"]=="Premium" else "#4a9eff" if customer2["subscription_type"]=="Student" else "#ff9500"
            st.markdown(f'<div style="background:linear-gradient(135deg,#141414,#1c1c1c);border:1px solid #252525;border-radius:16px;padding:1.5rem 2rem;margin:1rem 0;"><div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:1rem;"><div><div style="color:#1DB954;font-size:0.75rem;font-weight:700;text-transform:uppercase;letter-spacing:2px;">Customer ID</div><div style="color:#fff;font-size:1.8rem;font-weight:700;">{profile_uid}</div></div><div style="display:flex;gap:1.5rem;flex-wrap:wrap;"><div style="text-align:center;"><div style="color:#888;font-size:0.7rem;text-transform:uppercase;">Age</div><div style="color:#fff;font-size:1.3rem;font-weight:700;">{customer2["age"]}</div></div><div style="text-align:center;"><div style="color:#888;font-size:0.7rem;text-transform:uppercase;">Gender</div><div style="color:#fff;font-size:1.3rem;font-weight:700;">{customer2["gender"]}</div></div><div style="text-align:center;"><div style="color:#888;font-size:0.7rem;text-transform:uppercase;">Country</div><div style="color:#fff;font-size:1.3rem;font-weight:700;">{customer2["country"]}</div></div><div style="text-align:center;"><div style="color:#888;font-size:0.7rem;text-transform:uppercase;">Device</div><div style="color:#fff;font-size:1.3rem;font-weight:700;">{customer2["device_type"]}</div></div><div style="text-align:center;"><div style="color:#888;font-size:0.7rem;text-transform:uppercase;">Plan</div><div style="color:{sub_color};font-size:1.3rem;font-weight:700;">{customer2["subscription_type"]}</div></div></div></div></div>', unsafe_allow_html=True)

            m1,m2,m3,m4,m5 = st.columns(5)
            with m1: st.markdown(f'<div style="background:#141414;border:1px solid #25252555;border-radius:10px;padding:0.8rem;text-align:center;"><div style="color:#888;font-size:0.7rem;text-transform:uppercase;">Listen/day</div><div style="color:#1DB954;font-size:1.3rem;font-weight:700;">{customer2["listening_time"]} hrs</div></div>', unsafe_allow_html=True)
            with m2: st.markdown(f'<div style="background:#141414;border:1px solid #25252555;border-radius:10px;padding:0.8rem;text-align:center;"><div style="color:#888;font-size:0.7rem;text-transform:uppercase;">Songs/day</div><div style="color:#fff;font-size:1.3rem;font-weight:700;">{customer2["songs_played_per_day"]}</div></div>', unsafe_allow_html=True)
            with m3: st.markdown(f'<div style="background:#141414;border:1px solid #ff333333;border-radius:10px;padding:0.8rem;text-align:center;"><div style="color:#888;font-size:0.7rem;text-transform:uppercase;">Skip Rate</div><div style="color:#ff4444;font-size:1.3rem;font-weight:700;">{customer2["skip_rate"]*100:.0f}%</div></div>', unsafe_allow_html=True)
            with m4: st.markdown(f'<div style="background:#141414;border:1px solid #ff950033;border-radius:10px;padding:0.8rem;text-align:center;"><div style="color:#888;font-size:0.7rem;text-transform:uppercase;">Ads/week</div><div style="color:#ff9500;font-size:1.3rem;font-weight:700;">{customer2["ads_listened_per_week"]}</div></div>', unsafe_allow_html=True)
            with m5: st.markdown(f'<div style="background:#141414;border:1px solid #4a9eff33;border-radius:10px;padding:0.8rem;text-align:center;"><div style="color:#888;font-size:0.7rem;text-transform:uppercase;">Offline</div><div style="color:#4a9eff;font-size:1.3rem;font-weight:700;">{customer2["offline_listening"]} hrs</div></div>', unsafe_allow_html=True)

            col1, col2, col3 = st.columns(3, gap="medium")
            with col1:
                st.markdown('<div class="section-title">⏱️ Time Breakdown</div>', unsafe_allow_html=True)
                idle = max(0, 5 - customer2["listening_time"] - customer2["offline_listening"])
                fig = px.pie(pd.DataFrame({"Activity":["Listening","Offline","Idle"],"Hours":[customer2["listening_time"],customer2["offline_listening"],idle]}),
                    values="Hours",names="Activity",hole=0.5,
                    color_discrete_map={"Listening":"#1DB954","Offline":"#4a9eff","Idle":"#222"})
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="#111111",font=dict(color="#ccc"),height=260,annotations=[dict(text="Time",x=0.5,y=0.5,font_size=12,font_color="#ccc",showarrow=False)])
                fig.update_traces(textfont=dict(color="#fff",size=12),textinfo="label+percent")
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                st.markdown('<div class="section-title">📢 Engagement</div>', unsafe_allow_html=True)
                eng_labels = ["Listen","Songs","Skip","Ads","Offline"]
                eng_values = [min(100,customer2["listening_time"]/24*100),min(100,customer2["songs_played_per_day"]/100*100),
                    customer2["skip_rate"]*100,min(100,customer2["ads_listened_per_week"]/50*100),min(100,customer2["offline_listening"]/10*100)]
                fig = go.Figure(go.Bar(x=eng_labels,y=eng_values,
                    marker=dict(color=["#1DB954","#1DB954","#ff4444","#ff9500","#4a9eff"],line=dict(width=0)),
                    text=[f"{v:.0f}%" for v in eng_values],textposition="auto",textfont=dict(color="#fff",size=11)))
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="#111111",font=dict(color="#ccc"),height=260,showlegend=False)
                fig.update_yaxes(range=[0,110])
                st.plotly_chart(fig, use_container_width=True)
            with col3:
                st.markdown('<div class="section-title">📱 Activity</div>', unsafe_allow_html=True)
                fig = go.Figure(go.Bar(
                    y=["Songs/day","Ads/week","Offline hrs","Listen hrs"],
                    x=[customer2["songs_played_per_day"],customer2["ads_listened_per_week"],customer2["offline_listening"],customer2["listening_time"]],
                    orientation="h",
                    marker=dict(color=["#1DB954","#ff9500","#4a9eff","#1DB954"],line=dict(width=0)),
                    textposition="auto",textfont=dict(color="#fff",size=11)))
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="#111111",font=dict(color="#ccc"),height=260,showlegend=False,margin=dict(l=90,r=20,t=30,b=20))
                st.plotly_chart(fig, use_container_width=True)

            st.markdown('<div class="section-title">📋 Complete Feature Profile</div>', unsafe_allow_html=True)
            all_fields = [
                {"Feature":"Customer ID","Value":str(profile_uid),"Category":"Identity"},
                {"Feature":"Age","Value":str(customer2["age"]),"Category":"Demographics"},
                {"Feature":"Gender","Value":customer2["gender"],"Category":"Demographics"},
                {"Feature":"Country","Value":customer2["country"],"Category":"Demographics"},
                {"Feature":"Subscription","Value":customer2["subscription_type"],"Category":"Account"},
                {"Feature":"Device","Value":customer2["device_type"],"Category":"Account"},
                {"Feature":"Listen Time/day","Value":f"{customer2['listening_time']} hrs","Category":"Engagement"},
                {"Feature":"Songs Per Day","Value":str(customer2["songs_played_per_day"]),"Category":"Engagement"},
                {"Feature":"Offline Hours","Value":f"{customer2['offline_listening']} hrs","Category":"Engagement"},
                {"Feature":"Skip Rate","Value":f"{customer2['skip_rate']*100:.0f}%","Category":"Behaviour"},
                {"Feature":"Ads Per Week","Value":str(customer2["ads_listened_per_week"]),"Category":"Behaviour"},
                {"Feature":"Churned","Value":"Yes" if customer2["is_churned"]==1 else "No","Category":"Status"},
            ]
            st.dataframe(pd.DataFrame(all_fields),use_container_width=True,hide_index=True,
                column_config={"Feature":st.column_config.TextColumn("Feature",width="medium"),
                               "Value":st.column_config.TextColumn("Value",width="medium"),
                               "Category":st.column_config.TextColumn("Category",width="small")})

    # TAB 3 - ANALYTICS (v1773716604)
    with tab3:
        if df is None:
            st.markdown("**Dataset not loaded**")
        else:
            # ── 5 key numbers ──────────────────────────────────────────
            total   = len(df)
            churned = int(df["is_churned"].sum())
            kept    = total - churned
            rate    = round(churned / total * 100, 1)
            skip    = round(df["skip_rate"].mean() * 100, 1)

            a1,a2,a3,a4,a5 = st.columns(5)
            with a1:
                st.markdown('<div style="background:#141414;border:1px solid #1DB95444;border-radius:12px;padding:1rem;text-align:center;margin-bottom:1rem;"><div style="color:#888;font-size:0.72rem;text-transform:uppercase;letter-spacing:1px;">Total Users</div><div style="color:#1DB954;font-size:2rem;font-weight:800;">'+str(f"{total:,}")+'</div></div>', unsafe_allow_html=True)
            with a2:
                st.markdown('<div style="background:#141414;border:1px solid #ff333344;border-radius:12px;padding:1rem;text-align:center;margin-bottom:1rem;"><div style="color:#888;font-size:0.72rem;text-transform:uppercase;letter-spacing:1px;">Churned</div><div style="color:#ff4444;font-size:2rem;font-weight:800;">'+str(f"{churned:,}")+'</div></div>', unsafe_allow_html=True)
            with a3:
                st.markdown('<div style="background:#141414;border:1px solid #ff950044;border-radius:12px;padding:1rem;text-align:center;margin-bottom:1rem;"><div style="color:#888;font-size:0.72rem;text-transform:uppercase;letter-spacing:1px;">Retained</div><div style="color:#ff9500;font-size:2rem;font-weight:800;">'+str(f"{kept:,}")+'</div></div>', unsafe_allow_html=True)
            with a4:
                st.markdown('<div style="background:#141414;border:1px solid #ff333344;border-radius:12px;padding:1rem;text-align:center;margin-bottom:1rem;"><div style="color:#888;font-size:0.72rem;text-transform:uppercase;letter-spacing:1px;">Churn Rate</div><div style="color:#ff4444;font-size:2rem;font-weight:800;">'+str(rate)+'%</div></div>', unsafe_allow_html=True)
            with a5:
                st.markdown('<div style="background:#141414;border:1px solid #ffffff22;border-radius:12px;padding:1rem;text-align:center;margin-bottom:1rem;"><div style="color:#888;font-size:0.72rem;text-transform:uppercase;letter-spacing:1px;">Avg Skip</div><div style="color:#fff;font-size:2rem;font-weight:800;">'+str(skip)+'%</div></div>', unsafe_allow_html=True)

            st.markdown("---")

            # ── Row 1: Churn pie + Subscription bar ────────────────────
            r1c1, r1c2 = st.columns(2)

            with r1c1:
                st.markdown("**🔴 Churn vs Retained**")
                pie_df = pd.DataFrame({"Status": ["Retained", "Churned"], "Count": [kept, churned]})
                fig = px.pie(pie_df, values="Count", names="Status", hole=0.5,
                             color_discrete_map={"Retained": "#1DB954", "Churned": "#ff3333"})
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",
                                  font=dict(color="#ccc"), height=300,
                                  margin=dict(t=20,b=20,l=20,r=20))
                fig.update_traces(textfont_color="#fff", textinfo="label+percent")
                st.plotly_chart(fig, use_container_width=True)

            with r1c2:
                st.markdown("**🎵 Users by Subscription**")
                sub_df = df["subscription_type"].value_counts().reset_index()
                sub_df.columns = ["Plan", "Count"]
                fig = px.bar(sub_df, x="Plan", y="Count",
                             color_discrete_sequence=["#1DB954","#ff9500","#4a9eff","#aa44ff"],
                             color="Plan", text="Count")
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",
                                  plot_bgcolor="#111111",
                                  font=dict(color="#ccc"), height=300,
                                  showlegend=False,
                                  margin=dict(t=20,b=20,l=20,r=20))
                fig.update_traces(textposition="outside", textfont_color="#fff")
                st.plotly_chart(fig, use_container_width=True)

            # ── Row 2: Churn by subscription + Churn by device ─────────
            r2c1, r2c2 = st.columns(2)

            with r2c1:
                st.markdown("**📊 Churn Rate by Subscription**")
                cs = df.groupby("subscription_type")["is_churned"].mean().reset_index()
                cs.columns = ["Plan", "Rate"]
                cs["Rate"] = (cs["Rate"] * 100).round(1)
                cs = cs.sort_values("Rate", ascending=False)
                fig = px.bar(cs, x="Plan", y="Rate", color="Plan",
                             color_discrete_sequence=["#ff3333","#ff9500","#1DB954","#4a9eff"],
                             text=[str(v)+"%" for v in cs["Rate"]])
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",
                                  plot_bgcolor="#111111",
                                  font=dict(color="#ccc"), height=300,
                                  showlegend=False, yaxis_range=[0,100],
                                  margin=dict(t=20,b=20,l=20,r=20))
                fig.update_traces(textposition="outside", textfont_color="#fff")
                st.plotly_chart(fig, use_container_width=True)

            with r2c2:
                st.markdown("**📱 Churn Rate by Device**")
                cd = df.groupby("device_type")["is_churned"].mean().reset_index()
                cd.columns = ["Device", "Rate"]
                cd["Rate"] = (cd["Rate"] * 100).round(1)
                fig = px.bar(cd, x="Device", y="Rate", color="Device",
                             color_discrete_sequence=["#1DB954","#4a9eff","#ff9500"],
                             text=[str(v)+"%" for v in cd["Rate"]])
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",
                                  plot_bgcolor="#111111",
                                  font=dict(color="#ccc"), height=300,
                                  showlegend=False, yaxis_range=[0,100],
                                  margin=dict(t=20,b=20,l=20,r=20))
                fig.update_traces(textposition="outside", textfont_color="#fff")
                st.plotly_chart(fig, use_container_width=True)

            # ── Row 3: Age histogram + Countries ───────────────────────
            r3c1, r3c2 = st.columns(2)

            with r3c1:
                st.markdown("**👥 Age Distribution**")
                fig = go.Figure()
                fig.add_trace(go.Histogram(
                    x=df[df["is_churned"]==0]["age"],
                    name="Retained", nbinsx=20,
                    marker_color="#1DB954", opacity=0.8))
                fig.add_trace(go.Histogram(
                    x=df[df["is_churned"]==1]["age"],
                    name="Churned", nbinsx=20,
                    marker_color="#ff3333", opacity=0.8))
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",
                                  plot_bgcolor="#111111",
                                  font=dict(color="#ccc"), height=300,
                                  barmode="overlay",
                                  legend=dict(font_color="#ccc", bgcolor="rgba(0,0,0,0)"),
                                  margin=dict(t=20,b=20,l=20,r=20))
                st.plotly_chart(fig, use_container_width=True)

            with r3c2:
                st.markdown("**🌍 Top 10 Countries**")
                tc = df["country"].value_counts().head(10).reset_index()
                tc.columns = ["Country", "Users"]
                fig = px.bar(tc, y="Country", x="Users",
                             orientation="h",
                             color_discrete_sequence=["#1DB954"],
                             text="Users")
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",
                                  plot_bgcolor="#111111",
                                  font=dict(color="#ccc"), height=300,
                                  showlegend=False,
                                  margin=dict(t=20,b=20,l=80,r=30))
                fig.update_traces(textposition="outside", textfont_color="#fff")
                st.plotly_chart(fig, use_container_width=True)

    # CHAT - Inline section
    st.markdown("---")
    st.markdown('<div class="section-title">💬 AI Chat Assistant</div>', unsafe_allow_html=True)

    # Show message history
    for msg in st.session_state.chat_messages[-10:]:
        if msg["role"] == "user":
            st.markdown(
                '<div style="display:flex;justify-content:flex-end;margin:6px 0;">'
                '<div style="background:#1DB954;color:#000;border-radius:18px 18px 4px 18px;'
                'padding:10px 16px;max-width:75%;font-size:0.9rem;font-weight:500;">'
                + msg["content"] + '</div></div>',
                unsafe_allow_html=True)
        else:
            st.markdown(
                '<div style="display:flex;justify-content:flex-start;margin:6px 0;">'
                '<div style="background:#161616;color:#e0e0e0;border-radius:18px 18px 18px 4px;'
                'border:1px solid #2a2a2a;padding:10px 16px;max-width:75%;font-size:0.9rem;">'
                + msg["content"] + '</div></div>',
                unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Input row using columns - no st.chat_input so no white bar
    col_inp, col_btn = st.columns([6, 1])
    with col_inp:
        user_input = st.text_input(
            "chat_input_hidden",
            placeholder="Ask about churn risk or recommendations...",
            label_visibility="collapsed",
            key="chat_text_input")
    with col_btn:
        send_clicked = st.button("Send", use_container_width=True, key="chat_send_btn")

    if (send_clicked or user_input) and st.session_state.get("chat_text_input", "").strip():
        msg_text = st.session_state.chat_text_input.strip()
        if msg_text and (send_clicked or msg_text != st.session_state.get("last_chat_sent","")):
            st.session_state.last_chat_sent = msg_text
            st.session_state.chat_messages.append({"role": "user", "content": msg_text})
            context = {}
            if st.session_state.last_prediction:
                context = {
                    "churn_probability": st.session_state.last_prediction.get("churn_probability", 0.5),
                    "risk_segment":      st.session_state.last_prediction.get("risk_segment", "medium_risk"),
                }
            reply = chat_response(msg_text, context)
            st.session_state.chat_messages.append({"role": "assistant", "content": reply})
            st.rerun()

def page_help():
    st.markdown('<div class="hero-header"><div class="hero-title">📚 Help &amp; Documentation</div><div class="hero-subtitle">Everything you need to use Spotify Churn Guard effectively</div></div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🚀 Getting Started", "🤖 Model & Features", "❓ FAQ"])

    with tab1:
        st.markdown("### 🚀 Getting Started")
        st.markdown("---")
        st.markdown("#### 1️⃣ Predict & Explain Tab")
        st.markdown("Select any customer from the dropdown. The app instantly runs a churn prediction using the trained ML model. You will see the **Churn Risk %**, **Confidence score**, and a **Risk Level badge** (Low / Medium / High).")
        st.markdown("- 🔮 **Run Prediction** — Select a customer ID and click Predict")
        st.markdown("- 📖 **Generate SHAP Explanation** — See which features drive churn risk up (red) or down (green)")
        st.markdown("- 🎬 **Get Playbook Recommendations** — Get step-by-step intervention plans to retain the customer")
        st.markdown("---")
        st.markdown("#### 2️⃣ Customer Profile Tab")
        st.markdown("Select any of the 8,000 real customers. View their full details — age, gender, country, subscription type, device, listening habits — with 3 activity charts and a complete feature table.")
        st.markdown("---")
        st.markdown("#### 3️⃣ Analytics Tab")
        st.markdown("Platform-wide insights from all 8,000 users: 5 key metrics and 6 charts covering churn distribution, subscription breakdown, churn by device, age distribution, and top 10 countries.")
        st.markdown("---")
        st.markdown("#### 4️⃣ Chat Assistant")
        st.markdown("Scroll to the bottom of the page. Type your question and click **Send**. The assistant uses your latest prediction as context. Try asking:")
        st.markdown("- *Why might this user churn?*")
        st.markdown("- *What offers can we give them?*")
        st.markdown("- *Explain the SHAP values*")
        st.markdown("- *What is the difference between Premium and Student plans?*")

    with tab2:
        st.markdown("### 🤖 Model & Technical Details")
        st.markdown("---")
        st.markdown("#### Model Information")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("| Property | Value |\n|---|---|\n| **Model File** | `spotify_churn_model.pkl` |\n| **Algorithm** | HistGradientBoostingClassifier |\n| **Training Data** | 8,000 Spotify users |\n| **Target Variable** | `is_churned` (0=Stay, 1=Churn) |\n| **Explainability** | SHAP TreeExplainer |\n| **Scaler** | StandardScaler (`scaler.pkl`) |\n| **Total Features** | 15 columns |\n| **Deployment** | Streamlit Cloud — no backend |")
        with col2:
            st.markdown("#### How Predictions Work")
            st.markdown("1. Customer features are loaded from the dataset")
            st.markdown("2. Features are encoded and scaled using the saved scaler")
            st.markdown("3. The trained model predicts churn probability (0–100%)")
            st.markdown("4. SHAP values explain which features drove the prediction")
            st.markdown("5. Playbooks are recommended based on the risk segment")
            st.markdown("6. Chat assistant uses the prediction as context")
        st.markdown("---")
        st.markdown("#### 📋 The 15 Input Features")
        st.markdown("| # | Feature | Type | Description | Churn Impact |\n|---|---|---|---|---|\n| 1 | `age` | Numeric | User age in years | Younger users churn more |\n| 2 | `listening_time` | Numeric | Hours of music per day | Low = higher churn risk |\n| 3 | `songs_played_per_day` | Numeric | Daily song count | Low = disengaged user |\n| 4 | `skip_rate` | Numeric 0–1 | Fraction of songs skipped | High = poor recommendations |\n| 5 | `ads_listened_per_week` | Numeric | Weekly ad exposure | High = ad-fatigued user |\n| 6 | `offline_listening` | Numeric | Offline hours per day | Low = less Premium value |\n| 7 | `ad_stress` | Derived | ads × skip_rate | Combined frustration score |\n| 8 | `skip_intensity` | Derived | skip_rate × songs/day | Engagement quality score |\n| 9 | `gender_Male` | Binary | 1 if Male | One-hot encoded |\n| 10 | `gender_Other` | Binary | 1 if Other | One-hot encoded |\n| 11 | `subscription_type_Free` | Binary | 1 if Free plan | Free users churn most |\n| 12 | `subscription_type_Premium` | Binary | 1 if Premium | Premium users churn least |\n| 13 | `subscription_type_Student` | Binary | 1 if Student | Mid-level churn risk |\n| 14 | `device_type_Mobile` | Binary | 1 if Mobile | One-hot encoded |\n| 15 | `device_type_Web` | Binary | 1 if Web browser | One-hot encoded |")
        st.markdown("---")
        st.markdown("#### 🎯 Risk Segments")
        rc1, rc2, rc3 = st.columns(3)
        with rc1: st.markdown('<div style="background:#1DB95418;border:1px solid #1DB95455;border-radius:12px;padding:1rem;text-align:center;"><div style="font-size:1.5rem;">🟢</div><div style="color:#1DB954;font-weight:700;font-size:1.1rem;margin:0.4rem 0;">Low Risk (0–33%)</div><div style="color:#aaa;font-size:0.85rem;">User likely to stay. Good time to upsell Premium.</div></div>', unsafe_allow_html=True)
        with rc2: st.markdown('<div style="background:#ff950018;border:1px solid #ff950055;border-radius:12px;padding:1rem;text-align:center;"><div style="font-size:1.5rem;">🟠</div><div style="color:#ff9500;font-weight:700;font-size:1.1rem;margin:0.4rem 0;">Medium Risk (33–67%)</div><div style="color:#aaa;font-size:0.85rem;">Needs engagement. Send personalised content and offers.</div></div>', unsafe_allow_html=True)
        with rc3: st.markdown('<div style="background:#ff333318;border:1px solid #ff333355;border-radius:12px;padding:1rem;text-align:center;"><div style="font-size:1.5rem;">🔴</div><div style="color:#ff4444;font-weight:700;font-size:1.1rem;margin:0.4rem 0;">High Risk (67–100%)</div><div style="color:#aaa;font-size:0.85rem;">Immediate action needed. Trigger retention playbook now.</div></div>', unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("#### 📖 Understanding SHAP Values")
        st.markdown("SHAP explains **why** the model made a prediction, not just what it predicted.")
        st.markdown("- 🔴 **Red bars** — Feature is **increasing** churn risk (pushing probability higher)")
        st.markdown("- 🟢 **Green bars** — Feature is **decreasing** churn risk (pushing probability lower)")
        st.markdown("- The **longer the bar**, the more impact that feature has on this specific prediction")
        st.markdown("**Example:** A user with skip_rate = 0.85 will show a long red SHAP bar for skip_rate — meaning their high skip rate is the biggest reason they are predicted to churn.")

    with tab3:
        st.markdown("### ❓ Frequently Asked Questions")
        st.markdown("---")
        faqs = [
            ("What is churn prediction?", "Churn prediction uses machine learning to identify which customers are likely to cancel their subscription. This app analyses 15 behavioural and demographic features of each Spotify user and outputs a churn probability score."),
            ("What does the churn probability percentage mean?", "It represents the likelihood (0 to 100%) that a user will cancel. For example, 85% means the model is highly confident this user is about to churn and needs immediate intervention."),
            ("What are XAI and SHAP?", "XAI stands for Explainable AI. Instead of just giving a prediction, it explains WHY. SHAP assigns each feature a score showing how much it contributed to pushing the prediction up or down. Red = increases risk, Green = decreases risk."),
            ("What are Actionable Playbooks?", "Playbooks are structured intervention plans — sequences of actions (emails, in-app messages, SMS, push notifications) designed to retain a user. Each playbook is matched to the risk level with estimated conversion lift and retention improvement."),
            ("Why are some features derived like ad_stress and skip_intensity?", "These are engineered features created by combining raw features. ad_stress = ads_per_week x skip_rate captures ad frustration. skip_intensity = skip_rate x songs_per_day measures how actively disengaged a user is."),
            ("What does the Analytics tab show?", "Platform-wide insights from all 8,000 users: total users, churn rate, average skip rate, churn by subscription type, churn by device, age distribution of churned vs retained users, and top countries by user count."),
            ("Does this need a backend server?", "No. The entire app runs on Streamlit Cloud. The ML model, SHAP explainer, playbook engine, and chat all run directly in the app — no FastAPI, no localhost, no external APIs needed."),
            ("Why does the model show very high churn probability for some users?", "The model learned that certain combinations strongly predict churn — e.g. a Free plan user with high skip rate and high ad exposure. When multiple risk factors combine, the model correctly identifies high churn risk."),
            ("How accurate is the model?", "The model uses HistGradientBoostingClassifier trained on 8,000 Spotify user records with StandardScaler normalisation. Exact accuracy metrics can be found in the training script train_final_model.py."),
            ("Can I add my own customer data?", "Yes — replace spotify dataset.csv with your own CSV using the same column names. The app will automatically load all users. If column names differ, update FEATURE_COLUMNS in frontend_dashboard.py."),
            ("What is the difference between Free, Premium, and Student plans?", "Free users have ads and limited skips — they churn most frequently. Premium ($9.99/month) has ad-free listening, offline downloads, and HD audio — lowest churn. Student ($4.99/month) has same Premium benefits at half price."),
            ("What do the playbook action steps mean?", "Each playbook has numbered steps delivered through different channels: Email (direct email to user), In-App (banner shown inside the Spotify app), Push (mobile push notification), SMS (text message). Steps are ordered by priority and timing."),
        ]
        for q, a in faqs:
            with st.expander("❓ " + q):
                st.markdown("**Answer:** " + a)

def main():
    if "page"            not in st.session_state: st.session_state.page = "home"
    if "last_prediction" not in st.session_state: st.session_state.last_prediction = {}
    if "last_inputs"     not in st.session_state: st.session_state.last_inputs = {}
    if "tab1_last_uid"   not in st.session_state: st.session_state.tab1_last_uid = ""
    if "show_profile"    not in st.session_state: st.session_state.show_profile = False
    if "chat_session_id" not in st.session_state: st.session_state.chat_session_id = f"s_{int(time.time())}"
    if "chat_messages"   not in st.session_state: st.session_state.chat_messages = []
    if "last_chat_sent" not in st.session_state: st.session_state.last_chat_sent = ""

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
