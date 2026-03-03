# Role 4: Quick Reference Guide
## 60-Second Frontend Setup & Common Tasks

---

## ⚡ 60-Second Setup

```bash
# 1. Install packages (30 seconds)
pip install -r frontend_requirements.txt

# 2. Start backend (Terminal 1)
cd ../role3_backend
uvicorn backend_app:app --reload

# 3. Start frontend (Terminal 2)
streamlit run frontend_dashboard.py

# 4. Open in browser
# http://localhost:8501 ✅
```

---

## 🎯 5-Minute Getting Started

| Step | Command | Time |
|------|---------|------|
| 1️⃣ Install | `pip install -r frontend_requirements.txt` | 30s |
| 2️⃣ Backend | `uvicorn backend_app:app --reload` | 5s |
| 3️⃣ Frontend | `streamlit run frontend_dashboard.py` | 5s |
| 4️⃣ Open | Visit `http://localhost:8501` | 1s |
| 5️⃣ Test | Enter data and predict | 30s |
| **Total** | | **~1 min** |

---

## 📂 File Locations

```
CORE FILES (Use These):
├── frontend_dashboard.py           Main app (700 lines)
├── frontend_api_client.py          API client (400 lines)
├── frontend_requirements.txt        Dependencies
└── .streamlit/
    ├── config.toml                Config (theme, server)
    └── secrets.toml               Secrets (URLs, timeouts)

DOCUMENTATION:
├── ROLE4_README.md                Complete guide
├── ROLE4_QUICK_REFERENCE.md       This file
└── ROLE4_DEPLOYMENT_GUIDE.md      Deployment options

INTEGRATION:
├── backend_app.py                 (Role 3) backend
└── chatbot_flows.py               (Role 3) chatbot
```

---

## 🚀 Quick Deploy

### Streamlit Cloud (30 seconds, FREE)

```bash
# 1. Push to GitHub
git push -u origin main

# 2. Go to https://streamlit.io/cloud

# 3. Click "New app"
# - Select your repo
# - Select branch (main)
# - Select frontend_dashboard.py
# - Click "Deploy"

# DONE! You get a live URL like:
# https://spotify-churn-prediction-YOURNAME.streamlit.app/
```

### Local Docker (2 minutes)

```bash
# 1. Build
docker build -t spotify-frontend:latest .

# 2. Run
docker run -p 8501:8501 \
  -e BACKEND_URL=http://localhost:8000 \
  spotify-frontend:latest

# 3. Visit http://localhost:8501
```

### Heroku (1 minute)

```bash
# 1. Setup
heroku create spotify-churn-frontend

# 2. Deploy
git push heroku main

# 3. Open
heroku open
# URL: https://spotify-churn-frontend.herokuapp.com
```

---

## 🔑 API Client Examples

### Basic Usage

```python
from frontend_api_client import APIClient

# Initialize
client = APIClient("http://localhost:8000")

# Check health
if client.health():
    print("✅ Backend is running")
```

### Make Predictions

```python
# Single prediction
prediction = client.predict(
    user_id="user_001",
    features={
        "subscription_type": "Premium",
        "monthly_sessions": 45,
        "stream_hours": 120.5,
        "account_age_days": 365,
        "playlist_diversity": 0.8
    }
)

print(prediction["churn_probability"])  # 0-1
print(prediction["risk_segment"])       # Low/Medium/High
print(prediction["confidence"])         # 0-1
```

### Get Explanations

```python
explanation = client.explain(
    user_id="user_001",
    prediction_id="pred_001"
)

print(explanation["summary"])           # Why they churn
print(explanation["contribution"])      # Feature importance
```

### Recommend Playbooks

```python
playbooks = client.recommend_playbooks(
    user_id="user_001",
    prediction_id="pred_001",
    churn_probability=0.75,
    risk_segment="High"
)

for pb in playbooks:
    print(pb["name"])           # e.g., "Premium Upgrade"
    print(pb["success_rate"])   # 0-1
```

### Execute Playbook

```python
result = client.execute_playbook(
    user_id="user_001",
    prediction_id="pred_001",
    playbook_id="playbook_001",
    authorize=True
)

print(result["status"])         # queued, executing, completed
```

### Chat with Chatbot

```python
response = client.chat(
    user_id="user_001",
    session_id="session_001",
    message="Why might I churn?",
    context={}
)

print(response["reply"])        # Assistant's response
print(response["suggested_actions"])  # What to do next
```

---

## 🎨 Dashboard Tabs

### Tab 1: Single Prediction 🔍

**What it does:** Predict churn for one user

**Steps:**
1. Enter `User ID`
2. Set feature sliders
3. Click "Predict"
4. View gauge chart + explanation

**Output:**
- Churn probability gauge
- Risk level color-coded
- Feature importance chart
- Explanation summary
- Recommended playbooks

### Tab 2: Customer Profiles 👥

**What it does:** Look up historical customer data

**Steps:**
1. Enter `User ID`
2. Click "Load Profile"
3. Browse metrics

**Output:**
- Account info
- Prediction history chart
- Favorite genres
- Account metrics
- Risk trend

### Tab 3: Analytics 📊

**What it does:** Platform-wide metrics

**Shows:**
- Total users analyzed
- High-risk users count
- Playbooks executed
- Risk distribution pie chart
- Playbook success rates

### Tab 4: Chat 💬

**What it does:** Multi-turn conversations with chatbot

**Features:**
- Ask questions naturally
- Get personalized responses
- View suggested actions
- See available offers
- Full chat history

---

## 🔧 Configuration

### Default Settings

```toml
# .streamlit/config.toml
[theme]
primaryColor = "#1DB954"      # Spotify green
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"

[server]
port = 8501
address = "0.0.0.0"
```

### Custom Settings

**Via .streamlit/secrets.toml:**

```toml
BACKEND_URL = "http://localhost:8000"
BACKEND_TIMEOUT = 30
LOG_LEVEL = "INFO"
```

**Via Streamlit Cloud Dashboard:**

Settings → Secrets → Add:
```toml
BACKEND_URL = "https://your-backend.com"
```

---

## 🚨 Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| "Cannot connect to backend" | Backend not running | `uvicorn backend_app:app --reload` |
| "Port 8501 already in use" | Another app using port | `streamlit run frontend_dashboard.py --server.port 8502` |
| "Module not found" | Missing dependencies | `pip install -r frontend_requirements.txt` |
| "Secrets not loading" | Missing .streamlit/secrets.toml | Create the file with BACKEND_URL |
| "Very slow" | Slow backend response | Check BACKEND_TIMEOUT in secrets |

---

## 📊 Test Data

**Quick test user:**

```json
{
  "user_id": "test_001",
  "subscription_type": "Premium",
  "monthly_sessions": 45,
  "stream_hours": 120.5,
  "account_age_days": 365,
  "playlist_diversity": 0.8
}
```

**Expected result:**
- Churn probability: ~0.25-0.35 (Low risk)
- Confidence: ~0.92
- Risk segment: "Low"

---

## 🎯 Common Tasks

### Task 1: Check Backend Connection

```python
from frontend_api_client import APIClient

client = APIClient("http://localhost:8000")
if client.health():
    metrics = client.get_metrics()
    print(f"Users analyzed: {metrics['total_users']}")
```

### Task 2: Batch Predictions

```python
predictions = client.predict_batch([
    {"user_id": "u001", "features": {...}},
    {"user_id": "u002", "features": {...}},
])

for pred in predictions:
    print(f"{pred['user_id']}: {pred['churn_probability']}")
```

### Task 3: Explain Prediction

```python
explanation = client.explain("user_001", "pred_001")
print(explanation["summary"])       # Text explanation
print(explanation["contribution"])  # Feature importances
```

### Task 4: Show Chat History

```python
response = client.chat(
    user_id="user_001",
    session_id="session_001",
    message="Show my chat history",
    context={"show_history": True}
)
print(response["chat_history"])
```

---

## 🌍 Environment Variables

### Development (Local)

```bash
BACKEND_URL=http://localhost:8000
BACKEND_TIMEOUT=30
LOG_LEVEL=DEBUG
```

### Production (Streamlit Cloud)

Via Streamlit Cloud Dashboard Secrets:

```toml
BACKEND_URL=https://your-production-backend.com
BACKEND_TIMEOUT=60
LOG_LEVEL=INFO
```

---

## 📱 Mobile Testing

**Responsive design support:**

```
✅ Desktop 1920px    - Full features
✅ Tablet 768px      - Vertical layout
✅ Mobile 320px      - Single column
```

**Test on mobile:**
```bash
# Use your computer's IP
streamlit run frontend_dashboard.py

# On mobile, visit:
# http://<YOUR_PC_IP>:8501
```

---

## 🔐 Security Checklist

```
☐ No secrets in code
☐ No API keys in version control
☐ .streamlit/secrets.toml in .gitignore
☐ BACKEND_URL environment variable set
☐ CORS properly configured on backend
☐ Input validation enabled
☐ Error messages don't leak info
```

---

## 📈 Performance Tips

| Optimization | Impact | Difficulty |
|---|---|---|
| Cache predictions | 5x faster | Easy |
| Reduce batch size | Lower memory | Easy |
| Optimize charts | Faster render | Medium |
| Async backend calls | Non-blocking UI | Hard |

---

## 🔗 Quick Links

| Resource | URL |
|----------|-----|
| Streamlit Docs | https://docs.streamlit.io/ |
| API Reference | localhost:8000/docs |
| Deployment Guide | ROLE4_DEPLOYMENT_GUIDE.md |
| Complete README | ROLE4_README.md |

---

## 💡 Pro Tips

1. **Use session_state for persistence:**
   ```python
   if "user_id" not in st.session_state:
       st.session_state.user_id = None
   ```

2. **Cache API calls:**
   ```python
   @st.cache_data
   def get_user_profile(user_id):
       return client.predict(user_id, features)
   ```

3. **Show loading spinner:**
   ```python
   with st.spinner("Loading..."):
       result = client.predict(...)
   ```

4. **Organize code with tabs:**
   ```python
   tab1, tab2, tab3 = st.tabs(["Tab1", "Tab2", "Tab3"])
   with tab1:
       # Content here
   ```

---

## 🎓 Learning Path

1. **Day 1:** Setup + Single Prediction
2. **Day 2:** Customer Profiles + Analytics
3. **Day 3:** Chat Integration
4. **Day 4:** Deploy to Streamlit Cloud
5. **Day 5:** Customize & Extend

---

## 🆘 Getting Help

**For issues:**
1. Check ROLE4_README.md
2. Read ROLE4_DEPLOYMENT_GUIDE.md
3. Check error logs: `streamlit run --logger.level=debug`
4. Test backend health: `curl http://localhost:8000/health`

---

## 📝 Cheat Sheet

```bash
# Setup (one-time)
pip install -r frontend_requirements.txt

# Development (daily)
streamlit run frontend_dashboard.py

# Backend (in another terminal)
uvicorn backend_app:app --reload

# Deploy to Cloud (one-time)
git push -u origin main
# Then use https://streamlit.io/cloud

# Local Docker
docker build -t spotify-frontend:latest .
docker run -p 8501:8501 spotify-frontend:latest

# Check health
curl http://localhost:8000/health
curl http://localhost:8501/healthz (if enabled)
```

---

**Version:** 1.0.0  
**Last Updated:** 2026-02-26  
**Status:** ✅ PRODUCTION READY
