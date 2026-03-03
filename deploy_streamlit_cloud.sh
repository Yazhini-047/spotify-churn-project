#!/bin/bash
# Role 4 Frontend - Streamlit Cloud Deployment Script
# This script automates the deployment to Streamlit Cloud

set -e

echo "🎯 Spotify Churn Prediction - Role 4 Deployment Helper"
echo "======================================================="
echo ""

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📌 Initializing Git repository..."
    git init
    echo ""
fi

# Check if we're on main branch
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")
if [ "$BRANCH" != "main" ]; then
    echo "📌 Creating/switching to main branch..."
    git checkout -b main 2>/dev/null || git checkout main
    echo ""
fi

# Check for changes
if [ -z "$(git status --porcelain)" ]; then
    echo "✅ No changes to commit"
else
    echo "📌 Staging all files..."
    git add -A
    echo ""
    
    echo "📌 Committing changes..."
    git commit -m "Role 4 - Frontend & UX - Streamlit Dashboard Development"
    echo ""
fi

# Check if remote exists
if ! git config --get remote.origin.url > /dev/null; then
    echo "⚠️  No GitHub remote configured yet."
    echo ""
    echo "📝 Next steps:"
    echo "1. Create a new repository on GitHub"
    echo "2. Run the command shown on GitHub:"
    echo "   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git"
    echo "   git branch -M main"
    echo "   git push -u origin main"
    echo ""
else
    echo "📌 Pushing to GitHub..."
    git push -u origin main
    echo ""
fi

echo "✅ Git repository ready!"
echo ""
echo "🚀 NEXT: Deploy to Streamlit Cloud"
echo "===================================="
echo ""
echo "1. Open: https://streamlit.io/cloud"
echo "2. Sign in with GitHub account"
echo "3. Click 'New app'"
echo "4. Select:"
echo "   Repository: YOUR_REPO"
echo "   Branch: main"
echo "   Main file path: frontend_dashboard.py"
echo "5. Click 'Deploy'"
echo ""
echo "⏱️  Your app will be deployed in ~2-3 minutes"
echo ""
echo "🎉 You'll get a URL like:"
echo "   https://spotify-churn-prediction-YOUR_USERNAME.streamlit.app/"
echo ""
echo "📌 Troubleshooting:"
echo "   - Make sure backend is accessible from your cloud deployment"
echo "   - Set BACKEND_URL in Streamlit Cloud secrets"
echo "   - Check deployment logs for errors"
echo ""
