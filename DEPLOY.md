# Deployment Guide for Render

## Prerequisites
1. A [Render account](https://render.com) (free tier available)
2. Git repository (GitHub, GitLab, or Gitea)
3. Project pushed to a git repository

## Step-by-Step Deployment Instructions

### 1. Push Your Project to GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/fake-job-detector.git
git push -u origin main
```

### 2. Connect to Render
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **New +** → **Web Service**
3. Select **Build and deploy from a Git repository**
4. Connect your GitHub account and select your repository
5. Choose **fake-job-detector** repository

### 3. Configure Service
- **Name**: `fake-job-detector` (or your preferred name)
- **Runtime**: Python 3
- **Branch**: main
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python app.py`
- **Plan**: Free (or Starter/Pro for production)
- **Region**: Choose closest to your users

### 4. Environment Variables (Optional)
If you need environment variables, add them in the **Environment** section:
```
PORT: 8000
PYTHON_VERSION: 3.11
```

### 5. Deploy
Click **Create Web Service** and Render will automatically:
1. Clone your repository
2. Install dependencies from `requirements.txt`
3. Run `python app.py`
4. Assign you a unique URL like: `https://fake-job-detector.onrender.com`

## Post-Deployment

### Access Your App
Your app will be available at: `https://fake-job-detector.onrender.com`
- Dashboard UI: `https://fake-job-detector.onrender.com/`
- API Health Check: `https://fake-job-detector.onrender.com/api/health`
- Analyze Job: `POST https://fake-job-detector.onrender.com/api/analyze`

### View Logs
In Render Dashboard → Your Service → **Logs** tab

### Redeploy
Push changes to your `main` branch, and Render will automatically redeploy.

## Troubleshooting

### Service won't start
- Check the **Logs** tab for errors
- Ensure `PORT` environment variable is set correctly
- Verify all dependencies in `requirements.txt` are available

### Port binding errors
- The app is configured to use the `PORT` environment variable (default 8000)
- Render automatically sets this, so it should work out of the box

### Dependencies missing
- Update `requirements.txt` and push to trigger a rebuild
- Render will automatically redeploy

## Using render.yaml (Alternative Method)

Instead of manual configuration, you can use the `render.yaml` file:

1. In your GitHub repository root, the `render.yaml` file defines the service configuration
2. Go to Render Dashboard
3. Click **New +** → **Web Service**
4. Render will auto-detect and use `render.yaml` configuration
5. Review settings and click **Create Web Service**

This ensures consistent deployments and version control of your infrastructure.

## Scaling (Production Use)
- Upgrade from **Free** to **Starter** or **Professional** plan for:
  - Always-on service (free tier spins down after 15 min inactivity)
  - More memory and CPU
  - Custom domains
  - Database options (PostgreSQL, MySQL, MongoDB)

## Resources
- [Render Documentation](https://render.com/docs)
- [Python on Render](https://render.com/docs/deploy-python)
- [Environment Variables](https://render.com/docs/environment-variables)
