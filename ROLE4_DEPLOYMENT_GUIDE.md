# Role 4 — Frontend Deployment & Hosting Guide
## Streamlit Web Dashboard for Spotify Churn Prediction

**Version:** 1.0.0  
**Date:** 2026-02-26  
**Author:** Role 4 Frontend Developer

---

## 🚀 Quick Start (Local Development)

### Step 1: Install Dependencies

```bash
pip install -r frontend_requirements.txt
```

### Step 2: Configure Backend Connection

Create `.streamlit/secrets.toml`:

```toml
BACKEND_URL = "http://localhost:8000"
BACKEND_TIMEOUT = 30
```

### Step 3: Start Streamlit App

```bash
streamlit run frontend_dashboard.py
```

### Step 4: Access Dashboard

Open browser: **http://localhost:8501**

---

## 🌐 Deploy to Streamlit Cloud (FREE, Easiest)

### Getting a **Live URL** in 5 minutes ⚡

#### Step 1: Push Code to GitHub

```bash
# Initialize git repo
git init
git add .
git commit -m "Initial commit"

# Create GitHub account (if needed) and push
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/spotify-churn-prediction.git
git push -u origin main
```

#### Step 2: Sign Up for Streamlit Cloud

1. Go to **https://streamlit.io/cloud**
2. Click **"Sign in with GitHub"**
3. Authorize Streamlit
4. Accept terms

#### Step 3: Deploy App

Dashboard → **"New app"**

```
Repository:    YOUR_USERNAME/spotify-churn-prediction
Branch:        main
Main file path: frontend_dashboard.py
```

Click **"Deploy"** ✨

#### Step 4: Get Your Live URL

```
https://spotify-churn-prediction-YOUR_USERNAME.streamlit.app/
```

**That's it!** Your app is now live! 🎉

---

## 🔧 Streamlit Cloud Configuration

### Configure Secrets in Cloud Dashboard

1. Go to your deployed app
2. Click **Settings** (gear icon)
3. Choose **Secrets**
4. Paste secrets:

```toml
BACKEND_URL = "https://your-backend-domain.com"
BACKEND_TIMEOUT = 30
LOG_LEVEL = "INFO"
```

### Custom Domain (Premium Feature)

```
https://your-custom-domain.com
```

---

## 🐳 Docker Deployment

### Dockerfile for Frontend

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY frontend_requirements.txt .
RUN pip install -r frontend_requirements.txt

# Copy app
COPY frontend_dashboard.py .
COPY frontend_api_client.py .

# Create streamlit config
RUN mkdir -p .streamlit
COPY .streamlit/config.toml .streamlit/

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run
CMD ["streamlit", "run", "frontend_dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Build & Run

```bash
# Build image
docker build -t spotify-churn-frontend:latest .

# Run container
docker run -p 8501:8501 \
  -e BACKEND_URL=http://localhost:8000 \
  spotify-churn-frontend:latest

# Access
http://localhost:8501
```

---

## ☁️ Deploy to AWS

### Step 1: Push Docker Image to ECR

```bash
# Create ECR repository
aws ecr create-repository --repository-name spotify-churn-frontend

# Build and push
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

docker tag spotify-churn-frontend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/spotify-churn-frontend:latest

docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/spotify-churn-frontend:latest
```

### Step 2: Deploy to AWS AppRunner

```bash
# Create service
aws apprunner create-service \
  --service-name spotify-churn-frontend \
  --source-configuration "ImageRepository={ImageIdentifier=<account-id>.dkr.ecr.us-east-1.amazonaws.com/spotify-churn-frontend:latest,ImageRepositoryType=ECR,ImageConfiguration={Port=8501,RuntimeEnvironmentVariables={BACKEND_URL=https://your-backend.com}}}" \
  --instance-configuration Cpu=1,Memory=2048
```

**Your URL:** `https://your-service-id.us-east-1.apprunner.amazonaws.com`

---

## 🚀 Deploy to Heroku

```bash
# Install Heroku CLI
curl https://cli.heroku.com/install.sh | sh

# Login
heroku login

# Create app
heroku create spotify-churn-frontend

# Create Procfile
echo "web: streamlit run frontend_dashboard.py --server.port=\$PORT --server.address=0.0.0.0" > Procfile

# Set environment
heroku config:set BACKEND_URL=https://your-backend.herokuapp.com -a spotify-churn-frontend

# Deploy
git push heroku main

# View app
heroku open -a spotify-churn-frontend
```

**Your URL:** `https://spotify-churn-frontend.herokuapp.com`

---

## 🔗 Deploy to Vercel + Backend

### Step 1: Build REST Backend

Use Role 3 backend deployment on Vercel/AWS

### Step 2: Update Frontend Config

In Streamlit secrets, set:

```toml
BACKEND_URL = "https://your-backend-domain.vercel.app"
```

### Step 3: Deploy Frontend to Streamlit Cloud

(See Streamlit Cloud section above)

---

## 📊 Connecting to Backend

### Local Development

```toml
BACKEND_URL = "http://localhost:8000"
```

### Production Deployment

```toml
BACKEND_URL = "https://api.your-domain.com"
```

---

## 🧪 Testing the Frontend

### Unit Tests

```bash
pytest frontend_test.py -v
```

### Manual Testing

1. Start backend: `python backend_app.py`
2. Start frontend: `streamlit run frontend_dashboard.py`
3. Test each feature:
   - [ ] Make prediction
   - [ ] View explanation
   - [ ] Get playbooks
   - [ ] Chat with assistant

---

## 🔐 Security Considerations

- ✅ Never commit secrets to Git
- ✅ Use `.streamlit/secrets.toml` (add to `.gitignore`)
- ✅ For Streamlit Cloud, use dashboard secrets manager
- ✅ Use HTTPS for production
- ✅ Validate all user inputs
- ✅ Implement rate limiting on backend

---

## 📋 Deployment Checklist

### Before Deploying

- [ ] Backend API running and accessible
- [ ] All dependencies in `frontend_requirements.txt`
- [ ] Secrets configured (not in code)
- [ ] Backend URL set correctly
- [ ] Tested locally: `streamlit run frontend_dashboard.py`

### Streamlit Cloud Deployment

- [ ] GitHub repo created and pushed
- [ ] Streamlit Cloud account created
- [ ] App deployed and URL generated
- [ ] Secrets configured in cloud dashboard
- [ ] Backend connection verified

### Docker/Cloud Deployment

- [ ] Dockerfile created and tested
- [ ] Environment variables set correctly
- [ ] Health checks configured
- [ ] Domain/URL verified
- [ ] SSL certificate installed

---

## 🌍 Demo URLs (After Deployment)

Replace `YOUR_USERNAME` with your GitHub username:

```
Streamlit Cloud:
https://spotify-churn-prediction-YOUR_USERNAME.streamlit.app/

AWS AppRunner:
https://your-service-id.us-east-1.apprunner.amazonaws.com/

Heroku:
https://spotify-churn-frontend.herokuapp.com/

Custom Domain:
https://your-custom-domain.com/
```

---

## 📞 Troubleshooting

### Issue: "Cannot connect to backend"

**Solution:**
```toml
# Update .streamlit/secrets.toml
BACKEND_URL = "http://localhost:8000"  # Local
# OR
BACKEND_URL = "https://your-backend-domain.com"  # Production
```

### Issue: App crashes on load

```bash
# Check for errors
streamlit run frontend_dashboard.py --logger.level=debug

# View requirements
pip list
```

### Issue: Slow performance

```toml
# Increase timeout
BACKEND_TIMEOUT = 60
```

---

## 📖 File Structure

```
spotify_churn_prediction/
├── frontend_dashboard.py           # Main Streamlit app
├── frontend_api_client.py          # API client library
├── frontend_requirements.txt        # Python dependencies
├── .streamlit/
│   ├── config.toml                # Streamlit config
│   └── secrets.toml               # Secrets (local only)
├── Dockerfile                      # Docker image
├── Procfile                        # Heroku config
└── ROLE4_DEPLOYMENT_GUIDE.md      # This file
```

---

## 🎯 Next Steps

1. **Local Testing:** Run dashboard locally
2. **Push to GitHub:** Commit code to repository
3. **Choose Platform:**
   - **Easiest:** Streamlit Cloud (recommended)
   - **Most Flexible:** Docker + AWS
   - **Free Option:** Heroku
4. **Deploy:** Follow platform-specific steps above
5. **Share URL:** Get your live dashboard link!

---

## 📊 What's Included

### Pages

1. **Home / Dashboard**
   - Single prediction maker
   - Customer profile explorer
   - Platform analytics
   - Chat assistant widget

2. **Help & Documentation**
   - Getting started guide
   - API status check
   - FAQ section

### Features

✅ Real-time churn predictions  
✅ SHAP explanation visualizations  
✅ Playbook recommendations  
✅ Multi-turn chatbot  
✅ Customer profile lookup  
✅ Platform analytics  
✅ Responsive design  
✅ Mobile-friendly  

---

## 🎓 Learning Resources

- **Streamlit Docs:** https://docs.streamlit.io/
- **Streamlit Cloud:** https://streamlit.io/cloud
- **Plotly Visualization:** https://plotly.com/python/
- **Docker Docs:** https://docs.docker.com/

---

## ✅ Status: READY TO DEPLOY

Your frontend is production-ready! 🚀

**Recommended Deployment:** Streamlit Cloud (5 minutes setup)

---

**Contact:** Role 4 Frontend Developer  
**Last Updated:** 2026-02-26  
**Version:** 1.0.0
