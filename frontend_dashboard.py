"""
ROLE 4: FRONTEND & UX - STREAMLIT DASHBOARD
============================================
Interactive web interface for Spotify Churn Prediction System.

Features:
- Dashboard with real-time churn predictions
- Customer profile exploration
- SHAP explanation visualizations
- Playbook recommendation & execution
- Multi-turn chatbot widget
- User management

Run: streamlit run frontend_dashboard.py
Deploy: streamlit run frontend_dashboard.py --logger.level=info

Author: Role 4 Frontend Developer
Date: 2026-02-26
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import requests
import json
from typing import Dict, Any, List, Optional
import time

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
    .main {
        padding: 0;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .risk-high {
        color: #ff3333;
        font-weight: bold;
    }
    .risk-medium {
        color: #ff9500;
        font-weight: bold;
    }
    .risk-low {
        color: #00cc66;
        font-weight: bold;
    }
    .header-title {
        color: #1DB954;
        font-size: 2.5em;
        font-weight: bold;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# API CLIENT
# ============================================================================

class APIClient:
    """Client for backend API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.timeout = 30
    
    def predict(self, user_id: str, features: Dict[str, Any]) -> Dict:
        """Make prediction"""
        try:
            response = requests.post(
                f"{self.base_url}/predict",
                json={"user_id": user_id, "features": features},
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot connect to backend. Make sure it's running on http://localhost:8000")
            return None
        except Exception as e:
            st.error(f"❌ Prediction error: {str(e)}")
            return None
    
    def explain(self, user_id: str, prediction_id: str, depth: str = "detailed") -> Dict:
        """Get explanation"""
        try:
            response = requests.post(
                f"{self.base_url}/explain",
                json={
                    "user_id": user_id,
                    "prediction_id": prediction_id,
                    "explanation_depth": depth
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"❌ Explanation error: {str(e)}")
            return None
    
    def get_playbooks(self, user_id: str, prediction_id: str, 
                      churn_prob: float, risk_segment: str) -> Dict:
        """Get playbook recommendations"""
        try:
            response = requests.post(
                f"{self.base_url}/playbook/recommend",
                json={
                    "user_id": user_id,
                    "prediction_id": prediction_id,
                    "churn_probability": churn_prob,
                    "risk_segment": risk_segment
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"❌ Playbook error: {str(e)}")
            return None
    
    def chat(self, user_id: str, session_id: str, message: str, context: Dict = None) -> Dict:
        """Send chat message"""
        try:
            response = requests.post(
                f"{self.base_url}/chat",
                json={
                    "user_id": user_id,
                    "session_id": session_id,
                    "messages": [{"role": "user", "content": message}],
                    "context": context or {}
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"❌ Chat error: {str(e)}")
            return None
    
    def health(self) -> bool:
        """Check backend health"""
        try:
            response = requests.get(
                f"{self.base_url}/health",
                timeout=5
            )
            return response.status_code == 200
        except:
            return False


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_risk_color(risk_segment: str) -> str:
    """Get color for risk segment"""
    colors = {
        "high_risk": "#ff3333",
        "medium_risk": "#ff9500",
        "low_risk": "#00cc66"
    }
    return colors.get(risk_segment, "#999999")


def get_risk_emoji(risk_segment: str) -> str:
    """Get emoji for risk segment"""
    emojis = {
        "high_risk": "🔴",
        "medium_risk": "🟠",
        "low_risk": "🟢"
    }
    return emojis.get(risk_segment, "⚪")


def format_churn_probability(prob: float) -> str:
    """Format churn probability as percentage"""
    return f"{prob*100:.1f}%"


def create_gauge_chart(value: float, title: str) -> go.Figure:
    """Create gauge chart for churn probability"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value * 100,
        title={"text": title},
        domain={"x": [0, 1], "y": [0, 1]},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": "darkblue"},
            "steps": [
                {"range": [0, 33], "color": "#00cc66"},
                {"range": [33, 67], "color": "#ff9500"},
                {"range": [67, 100], "color": "#ff3333"}
            ],
            "threshold": {
                "line": {"color": "red", "width": 4},
                "thickness": 0.75,
                "value": 90
            }
        }
    ))
    fig.update_layout(height=300, margin=dict(b=0))
    return fig


def create_feature_importance_chart(features: List[Dict]) -> go.Figure:
    """Create bar chart of feature importances"""
    if not features:
        return None
    
    df = pd.DataFrame(features)
    df = df.sort_values('impact_percentage', ascending=True)
    
    colors = [
        '#ff3333' if x > 0 else '#00cc66'
        for x in df['impact_percentage']
    ]
    
    fig = go.Figure(data=[
        go.Bar(
            y=df['feature_name'],
            x=df['impact_percentage'],
            orientation='h',
            marker=dict(color=colors),
            text=df['impact_percentage'].round(1),
            textposition='auto',
        )
    ])
    
    fig.update_layout(
        title="Feature Importance (SHAP Values)",
        xaxis_title="Impact on Churn (%)",
        yaxis_title="Features",
        height=400,
        margin=dict(l=150),
        showlegend=False
    )
    return fig


def create_prediction_history_chart(history: List[Dict]) -> go.Figure:
    """Create line chart of prediction history"""
    if not history:
        return None
    
    df = pd.DataFrame(history)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['churn_probability'] * 100,
        mode='lines+markers',
        name='Churn Probability',
        line=dict(color='#1DB954', width=3),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title="Churn Risk Over Time",
        xaxis_title="Date",
        yaxis_title="Churn Probability (%)",
        height=300,
        hovermode='x unified',
        template='plotly_white'
    )
    return fig


# ============================================================================
# PAGE: HOME / DASHBOARD
# ============================================================================

def page_home():
    """Home/Dashboard page"""
    
    col1, col2, col3 = st.columns([2, 3, 1])
    
    with col1:
        st.markdown('<div class="header-title">🎵 Spotify Churn Prediction</div>', 
                   unsafe_allow_html=True)
    
    with col3:
        # Check API status
        api = APIClient()
        if api.health():
            st.success("✅ Backend Connected")
        else:
            st.error("❌ Backend Offline")
    
    st.markdown("---")
    
    # Tabs
    tab1, tab2, tab3 = st.tabs([
        "🔍 Single Prediction",
        "👥 Customer Profiles",
        "📊 Analytics"
    ])
    
    # =====================================================================
    # TAB 1: SINGLE PREDICTION
    # =====================================================================
    
    with tab1:
        st.subheader("Predict Churn Risk for a User")
        
        col1, col2 = st.columns(2)
        
        with col1:
            user_id = st.text_input(
                "User ID",
                value="user_001",
                help="Unique user identifier"
            )
            
            subscription_type = st.selectbox(
                "Subscription Type",
                ["Free", "Premium"],
                help="User's current subscription"
            )
            
            num_sessions = st.slider(
                "Monthly Sessions",
                min_value=0,
                max_value=100,
                value=10,
                help="Number of app sessions per month"
            )
        
        with col2:
            monthly_stream_hours = st.slider(
                "Monthly Stream Hours",
                min_value=0.0,
                max_value=200.0,
                value=5.5,
                step=0.5,
                help="Hours streamed per month"
            )
            
            account_age_days = st.slider(
                "Account Age (days)",
                min_value=0,
                max_value=1000,
                value=30,
                help="Days since account creation"
            )
            
            playlist_diversity = st.slider(
                "Playlist Diversity",
                min_value=0.0,
                max_value=1.0,
                value=0.6,
                step=0.1,
                help="Diversity of music genres (0-1)"
            )
        
        # Make prediction
        if st.button("🔮 Predict Churn Risk", use_container_width=True, key="predict_btn"):
            api = APIClient()
            
            features = {
                "subscription_type": subscription_type,
                "num_sessions": num_sessions,
                "monthly_stream_hours": monthly_stream_hours,
                "account_age_days": account_age_days,
                "playlist_diversity": playlist_diversity
            }
            
            with st.spinner("Making prediction..."):
                prediction = api.predict(user_id, features)
            
            if prediction:
                st.session_state.last_prediction = prediction
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "Churn Risk",
                        f"{prediction['churn_probability']*100:.1f}%",
                        delta=f"Confidence: {prediction['confidence_score']:.0%}"
                    )
                
                with col2:
                    st.metric(
                        "Risk Segment",
                        f"{get_risk_emoji(prediction['risk_segment'])} {prediction['risk_segment'].replace('_', ' ').title()}"
                    )
                
                with col3:
                    st.metric(
                        "Prediction",
                        "⚠️ CHURN" if prediction['prediction_label'] == 1 else "✅ RETAIN"
                    )
                
                # Show gauge
                fig = create_gauge_chart(
                    prediction['churn_probability'],
                    "Churn Probability"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Show explanation button
                if st.button("📖 Show Explanation", key="explain_btn"):
                    with st.spinner("Generating explanation..."):
                        explanation = api.explain(
                            user_id,
                            prediction['prediction_id'],
                            "detailed"
                        )
                    
                    if explanation:
                        st.info(f"**Summary:** {explanation['summary']}")
                        
                        st.subheader("📍 Key Drivers")
                        for driver in explanation['key_drivers']:
                            st.write(f"• {driver}")
                        
                        st.subheader("💡 Feature Impact")
                        fig = create_feature_importance_chart(
                            explanation['feature_attributions']
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                        st.subheader("💬 Actionable Insights")
                        for insight in explanation['actionable_insights']:
                            st.success(f"✨ {insight}")
                
                # Show playbooks
                if st.button("🎬 Get Recommendations", key="playbook_btn"):
                    with st.spinner("Finding best playbooks..."):
                        playbooks = api.get_playbooks(
                            user_id,
                            prediction['prediction_id'],
                            prediction['churn_probability'],
                            prediction['risk_segment']
                        )
                    
                    if playbooks:
                        st.subheader(f"Recommended: {playbooks['best_playbook_id']}")
                        
                        for pb in playbooks['recommended_playbooks']:
                            with st.expander(f"📋 {pb['name']}", expanded=True):
                                st.write(f"**Priority:** {pb['priority']}")
                                st.write(f"**Estimated Conversion Lift:** {pb['estimated_impact'].get('conversion_rate_lift', 0):.0%}")
                                st.write(f"**Retention Improvement:** {pb['estimated_impact'].get('retention_improvement', 0):.0%}")
    
    # =====================================================================
    # TAB 2: CUSTOMER PROFILES
    # =====================================================================
    
    with tab2:
        st.subheader("Customer Profile Explorer")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            profile_user_id = st.text_input(
                "Enter User ID",
                value="user_002",
                key="profile_user"
            )
        
        with col2:
            if st.button("📋 Load Profile", use_container_width=True):
                # Create sample profile data
                st.session_state.show_profile = True
        
        if st.session_state.get("show_profile", False):
            # Sample profile data
            profile_data = {
                "user_id": profile_user_id,
                "subscription": "Free",
                "account_age": 45,
                "sessions_last_30": 12,
                "stream_hours_last_30": 6.2,
                "favorite_genres": ["Pop", "Hip-Hop", "RnB"],
                "playlists_count": 8,
                "followers_count": 3
            }
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Account Age", f"{profile_data['account_age']} days")
            with col2:
                st.metric("Sessions (30d)", profile_data['sessions_last_30'])
            with col3:
                st.metric("Stream Hours (30d)", f"{profile_data['stream_hours_last_30']:.1f}h")
            
            st.subheader("Favorite Genres")
            genres_df = pd.DataFrame({
                'Genre': profile_data['favorite_genres'],
                'Streams': [15, 12, 8]
            })
            fig = px.bar(genres_df, x='Genre', y='Streams', color='Streams',
                        color_continuous_scale='Viridis')
            st.plotly_chart(fig, use_container_width=True)
            
            # Prediction history
            st.subheader("Churn Risk History")
            history = [
                {"date": (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"),
                 "churn_probability": 0.4 + (i * 0.05)}
                for i in range(30, 0, -5)
            ]
            fig = create_prediction_history_chart(history)
            st.plotly_chart(fig, use_container_width=True)
    
    # =====================================================================
    # TAB 3: ANALYTICS
    # =====================================================================
    
    with tab3:
        st.subheader("Platform Analytics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Users Analyzed", "15,230")
        with col2:
            st.metric("High Risk Users", "3,245", "-245")
        with col3:
            st.metric("Playbooks Executed", "1,892", "+143")
        with col4:
            st.metric("Avg Churn Risk", "42.3%", "-2.1%")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Risk Distribution")
            risk_df = pd.DataFrame({
                'Segment': ['Low Risk', 'Medium Risk', 'High Risk'],
                'Count': [8100, 4885, 3245]
            })
            fig = px.pie(risk_df, values='Count', names='Segment',
                        color_discrete_map={
                            'Low Risk': '#00cc66',
                            'Medium Risk': '#ff9500',
                            'High Risk': '#ff3333'
                        })
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Playbook Success Rate")
            pb_df = pd.DataFrame({
                'Playbook': ['High-Risk Convert', 'Engagement Boost', 'Retention Plus'],
                'Success Rate': [75, 62, 58]
            })
            fig = px.bar(pb_df, x='Playbook', y='Success Rate',
                        color='Success Rate', color_continuous_scale='RdYlGn')
            st.plotly_chart(fig, use_container_width=True)
    
    # =====================================================================
    # CHAT ASSISTANT (OUTSIDE TABS)
    # =====================================================================
    
    st.markdown("---")
    st.subheader("💬 Chat Assistant")
    
    # Display chat history
    chat_container = st.container()
    
    with chat_container:
        for message in st.session_state.chat_messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
    
    # Chat input (MUST be outside tabs)
    user_input = st.chat_input("Ask about churn risk or recommendations...")
    
    if user_input:
        # Add user message to history
        st.session_state.chat_messages.append({
            "role": "user",
            "content": user_input
        })
        
        # Get response from API
        with st.spinner("Chatbot thinking..."):
            api = APIClient()
            context = {
                "churn_probability": st.session_state.last_prediction.get(
                    'churn_probability', 0.5
                ) if st.session_state.last_prediction else 0.5
            }
            
            response = api.chat(
                "user_001",
                st.session_state.chat_session_id,
                user_input,
                context
            )
        
        if response:
            assistant_msg = response['message']['content']
            st.session_state.chat_messages.append({
                "role": "assistant",
                "content": assistant_msg
            })
            
            # Show suggested actions
            if response.get('suggested_actions'):
                st.info("**Suggested Actions:**")
                for action in response['suggested_actions']:
                    st.write(f"• {action.get('label', action)}")
            
            # Show offers
            if response.get('offers'):
                st.success("**Available Offers:**")
                for offer in response['offers']:
                    st.write(f"✨ {offer.get('label', offer)}")
            
            st.success("✅ Message sent! Scroll up to see the response.")


# ============================================================================
# PAGE: HELP & DOCUMENTATION
# ============================================================================

def page_help():
    """Help and documentation page"""
    
    st.title("📚 Help & Documentation")
    
    tab1, tab2, tab3 = st.tabs(["Getting Started", "API Status", "FAQ"])
    
    with tab1:
        st.markdown("""
        # Getting Started
        
        ## 1. Single Prediction
        - Enter user details in the "Single Prediction" tab
        - Click "🔮 Predict Churn Risk" to get results
        - View risk gauge and get explanations
        
        ## 2. View Explanations
        - Click "📖 Show Explanation" after a prediction
        - See key drivers and feature impact
        - Get actionable insights
        
        ## 3. Get Recommendations
        - Click "🎬 Get Recommendations"
        - View recommended playbooks
        - Execute actions to retain users
        
        ## 4. Chat with Assistant
        - Ask questions about churn risk
        - Get personalized recommendations
        - Activate offers through conversation
        
        ## 5. Analytics Dashboard
        - View platform-wide insights
        - Track playbook success rates
        - Monitor risk distribution
        """)
    
    with tab2:
        api = APIClient()
        col1, col2, col3 = st.columns(3)
        
        with col1:
            health = api.health()
            if health:
                st.success("✅ Backend API: Connected")
            else:
                st.error("❌ Backend API: Offline")
        
        with col2:
            if health:
                st.info("Status: All Systems Operational")
        
        with col3:
            st.metric("Last Check", "Just now")
    
    with tab3:
        st.markdown("""
        # Frequently Asked Questions
        
        ## Q: What does the churn probability mean?
        **A:** It's the likelihood (0-100%) that a user will cancel their Spotify subscription in the near future.
        
        ## Q: What are risk segments?
        **A:** 
        - 🟢 **Low Risk (0-33%)** - Likely to stay
        - 🟠 **Medium Risk (33-67%)** - Needs engagement
        - 🔴 **High Risk (67%+)** - Immediate action needed
        
        ## Q: What are playbooks?
        **A:** Automated intervention sequences (emails, offers, incentives) designed to retain users based on their risk level.
        
        ## Q: How do I read the explanations?
        **A:** SHAP values show which features most influence the churn prediction. Positive values increase churn risk, negative values decrease it.
        
        ## Q: Can I chat with the assistant?
        **A:** Yes! The chat widget can explain your risk, recommend offers, and even execute playbooks through conversation.
        """)


# ============================================================================
# SIDEBAR NAVIGATION
# ============================================================================

def main():
    """Main application"""
    
    # Initialize session state
    if "page" not in st.session_state:
        st.session_state.page = "home"
    if "last_prediction" not in st.session_state:
        st.session_state.last_prediction = {}
    if "show_profile" not in st.session_state:
        st.session_state.show_profile = False
    if "chat_session_id" not in st.session_state:
        st.session_state.chat_session_id = f"session_{int(time.time())}"
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    
    # Sidebar
    with st.sidebar:
        st.title("🎵 Navigation")
        
        page = st.radio(
            "Select Page",
            ["Home", "Help & Docs"],
            index=0 if st.session_state.page == "home" else 1,
            key="nav_radio"
        )
        
        st.session_state.page = "home" if page == "Home" else "help"
        
        st.markdown("---")
        
        # Backend connection info
        st.subheader("⚙️ Configuration")
        
        api = APIClient()
        if api.health():
            st.success("✅ Backend Connected")
            col1, col2 = st.columns(2)
            with col1:
                st.caption("API Status")
            with col2:
                st.caption("Online")
        else:
            st.error("❌ Backend Offline")
            st.caption("Make sure backend is running on http://localhost:8000")
        
        st.markdown("---")
        
        st.markdown("""
        ### About
        **Spotify Churn Prediction System**
        
        Version 1.0.0
        Date: 2026-02-26
        
        ### Quick Links
        - [API Docs](http://localhost:8000/docs)
        - [GitHub](https://github.com)
        - [Contact Support](mailto:support@example.com)
        """)
    
    # Page routing
    if st.session_state.page == "home":
        page_home()
    else:
        page_help()


if __name__ == "__main__":
    main()
