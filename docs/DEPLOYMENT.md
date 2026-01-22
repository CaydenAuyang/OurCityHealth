# GitHub Pages Deployment Guide

## Quick Setup

Your project showcase is now ready to deploy! Follow these steps:

1. **Go to your repository on GitHub:**
   - Navigate to: https://github.com/CaydenAuyang/Our-City-Health---Sentiment-Project

2. **Enable GitHub Pages:**
   - Click on **Settings** (in the repository navigation bar)
   - Scroll down to **Pages** in the left sidebar
   - Under **Source**, select:
     - **Deploy from a branch**
     - Branch: `main`
     - Folder: `/docs`
   - Click **Save**

3. **Wait for deployment:**
   - GitHub will build and deploy your site (usually takes 1-2 minutes)
   - You'll see a green checkmark when it's ready

4. **Access your site:**
   - Your site will be live at: https://caydenauyang.github.io/Our-City-Health---Sentiment-Project/

## Files Included

- `index.html` - Main project showcase page
- `corporate_dashboard.html` - Corporate Intelligence Dashboard
- All required images (PNG files)
- `.nojekyll` - Ensures GitHub Pages serves files correctly

## Available Pages

- **Project Showcase**: https://caydenauyang.github.io/Our-City-Health---Sentiment-Project/
- **Corporate Dashboard**: https://caydenauyang.github.io/Our-City-Health---Sentiment-Project/corporate_dashboard.html

## Updating the Site

Simply update files in the `docs/` folder, commit, and push:
```bash
git add docs/
git commit -m "Update showcase"
git push origin main
```

GitHub Pages will automatically rebuild and deploy your changes.
