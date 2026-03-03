@echo off
REM Role 4 Frontend - Streamlit Cloud Deployment Helper (Windows)
REM This script prepares your code for Streamlit Cloud deployment

setlocal enabledelayedexpansion

echo.
echo 🎯 Spotify Churn Prediction - Role 4 Deployment Helper
echo ======================================================
echo.

REM Check if git is installed
git --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Git is not installed or not in PATH
    echo Please install Git from: https://git-scm.com/
    pause
    exit /b 1
)

REM Initialize git if needed
if not exist ".git" (
    echo 📌 Initializing Git repository...
    git init
    echo.
)

REM Check git status and commit
echo 📌 Checking for changes...
git status --porcelain >nul 2>&1
if errorlevel 0 (
    echo 📌 Staging all files...
    git add -A
    echo.
    
    echo 📌 Committing changes...
    git commit -m "Role 4 - Frontend ^& UX - Streamlit Dashboard Development"
    echo.
)

REM Check if remote exists
git config --get remote.origin.url >nul 2>&1
if errorlevel 1 (
    echo.
    echo ⚠️  No GitHub remote configured yet.
    echo.
    echo 📝 Follow these steps:
    echo 1. Create a new repository on GitHub: https://github.com/new
    echo 2. Run these commands:
    echo    git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
    echo    git branch -M main
    echo    git push -u origin main
    echo.
) else (
    echo 📌 Pushing to GitHub...
    git push -u origin main
    echo.
)

echo ✅ Git repository ready!
echo.
echo 🚀 NEXT: Deploy to Streamlit Cloud
echo ===================================
echo.
echo 1. Open: https://streamlit.io/cloud
echo 2. Sign in with your GitHub account
echo 3. Click "New app"
echo 4. Select:
echo    Repository: YOUR_REPO
echo    Branch: main
echo    Main file path: frontend_dashboard.py
echo 5. Click "Deploy"
echo.
echo ⏱️  Your app will deploy in 2-3 minutes
echo.
echo 🎉 You'll get a URL like:
echo    https://spotify-churn-prediction-YOUR_USERNAME.streamlit.app/
echo.
echo 📌 Troubleshooting:
echo    - Make sure backend is running
echo    - Set BACKEND_URL in Streamlit Cloud secrets
echo    - Check deployment logs for errors
echo.
pause
