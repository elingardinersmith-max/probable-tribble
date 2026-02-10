# Utility Monitor - Full-Stack Web Application

A production-ready web application for monitoring utility municipalization across the United States.

## 🚀 Quick Deploy

### Option 1: Deploy to Render (Recommended - Free Tier Available)

1. **Fork or Clone this Repository**
   ```bash
   git clone <your-repo-url>
   cd webapp
   ```

2. **Create Account on Render**
   - Go to [render.com](https://render.com)
   - Sign up with GitHub

3. **Deploy**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Configure:
     - **Name**: utility-monitor
     - **Environment**: Python 3
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `gunicorn app:app`
     - **Plan**: Free

4. **Add Environment Variables** (Optional for enhanced crawling)
   - Go to "Environment" tab
   - Add:
     - `GOOGLE_API_KEY`: your_google_api_key
     - `GOOGLE_CSE_ID`: your_custom_search_engine_id
     - `NEWS_API_KEY`: your_newsapi_key
     - `FLASK_ENV`: production

5. **Deploy!**
   - Click "Create Web Service"
   - Wait 3-5 minutes
   - Your app will be live at: `https://utility-monitor.onrender.com`

### Option 2: Deploy to Railway

1. **Create Account on Railway**
   - Go to [railway.app](https://railway.app)
   - Sign up with GitHub

2. **Deploy**
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Railway auto-detects Python and deploys

3. **Add Environment Variables**
   - Go to "Variables" tab
   - Add your API keys (same as above)

4. **Access Your App**
   - Railway provides a custom URL
   - Check "Settings" tab for your URL

### Option 3: Deploy to Heroku

1. **Install Heroku CLI**
   ```bash
   brew install heroku/brew/heroku  # Mac
   # or download from heroku.com
   ```

2. **Login and Create App**
   ```bash
   heroku login
   heroku create utility-monitor
   ```

3. **Set Environment Variables**
   ```bash
   heroku config:set GOOGLE_API_KEY=your_key
   heroku config:set GOOGLE_CSE_ID=your_cse_id
   heroku config:set NEWS_API_KEY=your_key
   ```

4. **Deploy**
   ```bash
   git push heroku main
   heroku open
   ```

### Option 4: Deploy to Vercel (Frontend + Serverless API)

1. **Install Vercel CLI**
   ```bash
   npm i -g vercel
   ```

2. **Deploy**
   ```bash
   vercel
   ```

3. **Follow Prompts**
   - Link to your project
   - Configure build settings
   - Add environment variables

## 🏃 Run Locally

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Environment Variables (Optional)

```bash
# Copy example env file
cp ../.env.example .env

# Edit .env with your API keys
nano .env
```

### 3. Run the App

```bash
python app.py
```

The app will be available at `http://localhost:5000`

## 📁 Project Structure

```
webapp/
├── app.py                 # Flask application (backend + frontend serving)
├── crawler.py             # Web crawling logic
├── requirements.txt       # Python dependencies
├── Procfile              # Deployment configuration
├── runtime.txt           # Python version
├── .gitignore            # Git ignore rules
├── static/               # Frontend files
│   └── index.html        # Single-page application
└── data/                 # Data storage (created on first run)
    ├── mentions.json     # All collected mentions
    └── crawl_log.json    # Crawl history
```

## 🔧 Configuration

### Environment Variables

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `PORT` | No | Server port | 5000 |
| `FLASK_ENV` | No | Environment (development/production) | production |
| `FLASK_DEBUG` | No | Debug mode (True/False) | False |
| `GOOGLE_API_KEY` | No | Google Custom Search API key | None |
| `GOOGLE_CSE_ID` | No | Google Custom Search Engine ID | None |
| `NEWS_API_KEY` | No | NewsAPI.org API key | None |
| `DATA_DIR` | No | Data storage directory | data |

### API Keys Setup

The app works without API keys (using government scrapers only), but adding APIs significantly improves coverage:

**Google Custom Search** (100 free searches/day):
1. [Get API Key](https://developers.google.com/custom-search/v1/overview)
2. [Create Custom Search Engine](https://programmablesearchengine.google.com/)

**NewsAPI.org** (100 free requests/day):
1. [Sign up at NewsAPI.org](https://newsapi.org/register)
2. Copy your API key

See `../backend/API_SETUP_GUIDE.md` for detailed instructions.

## 🎯 Features

### Data Sources
- ✅ Google Custom Search (with API key)
- ✅ NewsAPI.org (with API key)
- ✅ 6 State Public Utility Commissions
- ✅ 6 City Council Legistar systems
- ✅ Federal FERC (framework ready)

### Capabilities
- 🔍 Multi-source web crawling
- 🤖 Smart data extraction (location, utility, stage, priority)
- 📊 Real-time statistics dashboard
- 🔄 Manual and automated crawling
- 🎨 Admin review interface
- 📱 Fully responsive design
- 💾 JSON data persistence
- 🚀 One-click deployment

## 📊 Usage

### Running Your First Crawl

1. Open your deployed app URL
2. Click "Run Crawl Now"
3. Wait 30-60 seconds
4. Review mentions in the "Review Queue"
5. Click "Approve" or "Delete" on each item

### Setting Up Automated Crawling

To enable automated crawling every 6 hours, you can:

**Option A: Use a Cron Service (like cron-job.org)**
1. Sign up at [cron-job.org](https://cron-job.org)
2. Create a new cron job
3. URL: `https://your-app.onrender.com/api/crawl`
4. Method: POST
5. Schedule: Every 6 hours
6. Headers: `Content-Type: application/json`

**Option B: Add a Scheduler to Your App**
- The backend includes `scheduler.py` for this
- For free hosting, external cron is usually better

## 🔒 Security Notes

- Never commit `.env` files with real API keys
- Use environment variables for all secrets
- The app includes CORS protection
- Rate limiting on API calls
- Input validation on all endpoints

## 📈 Scaling

### Free Tier Limitations
- **Render Free**: Apps sleep after 15 min of inactivity
- **Railway Free**: 500 hours/month
- **Heroku Free**: Deprecated (use paid tier)

### Recommendations
- Start with Render's free tier
- Add API keys for better coverage
- Upgrade to paid tier (~$7/month) for:
  - No sleeping
  - Custom domain
  - More resources
  - Faster performance

## 🐛 Troubleshooting

### App Not Loading
- Check deployment logs in your platform dashboard
- Verify all dependencies installed correctly
- Check `PORT` environment variable is set

### Crawl Returns No Results
- Verify API keys are set correctly
- Check rate limits (100/day for free tiers)
- Government scrapers work without API keys

### Data Not Persisting
- Free tiers may reset storage periodically
- Consider upgrading for persistent storage
- Or use an external database (PostgreSQL, MongoDB)

## 📝 API Endpoints

```
GET  /                    - Frontend application
GET  /api/health          - Health check
GET  /api/mentions        - Get all mentions
GET  /api/mentions/:id    - Get single mention
PATCH /api/mentions/:id   - Update mention
DELETE /api/mentions/:id  - Delete mention
POST /api/crawl           - Trigger crawl
GET  /api/stats           - Get statistics
GET  /api/crawl/log       - Get crawl history
GET  /api/export          - Export data as JSON
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally
5. Submit a pull request

## 📄 License

MIT License - feel free to use for any purpose

## 🆘 Support

- Check logs in your deployment platform
- Review API_SETUP_GUIDE.md for API configuration
- Open an issue on GitHub
- Check deployment platform documentation

## 🎉 You're Done!

Your utility municipalization monitor is now live and accessible via link!

Visit your URL and start monitoring utility conversations across the United States.
