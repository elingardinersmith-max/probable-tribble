# API Setup Guide - Enhanced Crawling

This guide walks you through setting up the external APIs to supercharge your crawling capabilities.

## Overview

The enhanced crawler uses three tiers of data sources:

**Tier 1: Free APIs (Recommended)**
- Google Custom Search API - 100 free searches/day
- NewsAPI.org - 100 requests/day on free tier

**Tier 2: Government Sites (Always Free)**
- State Public Utility Commission websites
- City Council Legistar systems
- FERC eLibrary
- State legislature bill trackers

**Tier 3: Fallback**
- Simulated data for testing

## 1. Google Custom Search API Setup

Google Custom Search gives you access to Google's search index with 100 free searches per day.

### Step 1: Get API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the **Custom Search API**:
   - Go to "APIs & Services" > "Library"
   - Search for "Custom Search API"
   - Click "Enable"
4. Create credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "API Key"
   - Copy your API key

### Step 2: Create Custom Search Engine

1. Go to [Programmable Search Engine](https://programmablesearchengine.google.com/)
2. Click "Add" to create a new search engine
3. Configure:
   - **Sites to search**: Choose "Search the entire web"
   - **Name**: "Utility Municipalization Monitor"
4. Click "Create"
5. Go to "Setup" > "Basic" and copy your **Search engine ID** (cx parameter)

### Step 3: Configure in Backend

Add to your `.env` file:
```bash
GOOGLE_API_KEY=your_api_key_here
GOOGLE_CSE_ID=your_search_engine_id_here
```

### Limits & Pricing
- **Free tier**: 100 searches/day
- **Paid tier**: $5 per 1,000 queries (after free tier)
- Each search query counts as 1 search

## 2. NewsAPI.org Setup

NewsAPI provides access to news articles from 80,000+ sources worldwide.

### Step 1: Sign Up

1. Go to [NewsAPI.org](https://newsapi.org/)
2. Click "Get API Key"
3. Sign up for free account (developer tier)
4. Verify your email
5. Copy your API key from the dashboard

### Step 2: Configure in Backend

Add to your `.env` file:
```bash
NEWS_API_KEY=your_newsapi_key_here
```

### Limits & Pricing
- **Free tier**: 100 requests/day, articles from last 30 days
- **Paid tier**: Starting at $449/month for 250,000 requests/month
- Each request can return up to 100 articles

### Optimization Tips
- Use specific queries to maximize relevance
- Combine with date ranges to get recent news
- Cache results to avoid duplicate requests

## 3. Government Site Scrapers (No API Keys Needed)

These scrapers work automatically without API keys:

### State PUC Sites
The crawler automatically checks:
- California PUC (cpuc.ca.gov)
- Texas PUC (puc.texas.gov)
- New York PSC (dps.ny.gov)
- Florida PSC (psc.state.fl.us)
- Illinois ICC (icc.illinois.gov)
- Colorado PUC (puc.colorado.gov)

### City Council Agendas (Legistar)
Automatically scrapes these cities:
- Boulder, CO
- San Francisco, CA
- Seattle, WA
- Austin, TX
- Portland, OR
- Minneapolis, MN

### FERC eLibrary
- Federal Energy Regulatory Commission filings
- Requires no API key for basic access
- Advanced access available through FERC API registration

## 4. Complete .env Configuration

Copy this template to your `.env` file:

```bash
# Google Custom Search API
GOOGLE_API_KEY=AIzaSyD...your_key_here
GOOGLE_CSE_ID=017576662...your_cse_id

# NewsAPI.org
NEWS_API_KEY=1a2b3c4d...your_newsapi_key

# Server Configuration
FLASK_ENV=development
FLASK_DEBUG=True
PORT=5000

# Data Storage
DATA_DIR=data

# Crawl Configuration
DEFAULT_CRAWL_INTERVAL_HOURS=6
MAX_RESULTS_PER_QUERY=10

# Rate Limiting
REQUESTS_PER_MINUTE=30
REQUEST_DELAY=1
```

## 5. Testing Your Setup

Test each API individually:

### Test Google Search
```bash
# Set environment variables
export GOOGLE_API_KEY=your_key
export GOOGLE_CSE_ID=your_cse_id

# Run test
python -c "
from crawler import search_google
results = search_google('utility municipalization', 5)
print(f'Found {len(results)} results')
for r in results:
    print(f'  - {r[\"title\"][:60]}...')
"
```

### Test NewsAPI
```bash
export NEWS_API_KEY=your_key

python -c "
from crawler import search_newsapi
results = search_newsapi('public power initiative', 5)
print(f'Found {len(results)} results')
for r in results:
    print(f'  - {r[\"title\"][:60]}...')
"
```

### Test Government Scrapers
```bash
python -c "
from crawler import scrape_state_puc_sites, scrape_legistar_sites
puc = scrape_state_puc_sites()
leg = scrape_legistar_sites()
print(f'PUC sites: {len(puc)} results')
print(f'Legistar: {len(leg)} results')
"
```

## 6. Running Enhanced Crawls

### Full Crawl with All Sources
```bash
python app.py
# In another terminal:
curl -X POST http://localhost:5000/api/crawl
```

The crawler will automatically use all configured sources in this order:
1. Google Custom Search (if API key configured)
2. NewsAPI.org (if API key configured)
3. State PUC websites (always)
4. Legistar city councils (always)
5. FERC filings (always)
6. Fallback simulated data (if no APIs configured)

## 7. Monitoring Usage

### Google Custom Search
- Check quota: [Cloud Console](https://console.cloud.google.com/apis/api/customsearch.googleapis.com/quotas)
- 100 queries/day free
- Resets at midnight Pacific Time

### NewsAPI
- Check usage: [NewsAPI Dashboard](https://newsapi.org/account)
- 100 requests/day free
- Resets at midnight UTC

### Government Sites
- No usage limits
- Be respectful with request frequency (1-2 seconds between requests)

## 8. Cost Optimization

### Free Tier Strategy (Recommended for Small Scale)
- Google: 100 searches/day = 3,000 searches/month
- NewsAPI: 100 requests/day = 3,000 requests/month
- Run 2-3 crawls per day
- Use 4-5 queries per crawl
- Total: ~50 API calls per crawl

### Paid Tier Strategy (For Production Scale)
- Google: $5/1,000 queries = ~$15/month for 3,000 queries
- NewsAPI: $449/month for 250,000 requests
- Run crawls every 2-4 hours
- Use 10-15 queries per crawl
- Scrape government sites more aggressively

### Hybrid Strategy (Best Value)
- Use free Google + NewsAPI tiers
- Aggressive government site scraping (free)
- Schedule 2 full crawls per day
- Supplement with targeted manual crawls
- Total cost: $0/month

## 9. Troubleshooting

### "Google API credentials not configured"
- Check `.env` file has GOOGLE_API_KEY and GOOGLE_CSE_ID
- Verify API key is enabled in Cloud Console
- Check Custom Search API is enabled

### "NewsAPI key not configured"
- Check `.env` file has NEWS_API_KEY
- Verify key at newsapi.org/account
- Check you're not over daily limit

### "Request limit exceeded"
- Wait until your quota resets (midnight)
- Reduce crawl frequency
- Use fewer queries per crawl
- Consider upgrading to paid tier

### "No results found"
- Check your search queries are relevant
- Verify internet connection
- Check API keys are valid
- Try manual API test (see section 5)

## 10. Advanced Configuration

### Custom Search Engine Refinements

Improve Google CSE results:
1. Go to your CSE control panel
2. Add these sites to "Sites to search" for better results:
   - ballotpedia.org
   - utilitydive.com
   - americanpublicpower.org
   - publicpower.org
3. Enable "Search the entire web but emphasize included sites"

### Add More Government Sources

Edit `crawler.py` to add more state/city sites:

```python
puc_sites = {
    'California': 'https://www.cpuc.ca.gov',
    'Your State': 'https://your-puc-website.gov',
    # Add more...
}

legistar_cities = {
    'Your City, ST': 'https://yourcity.legistar.com/api/v1',
    # Add more...
}
```

## 11. Legal & Ethical Considerations

- **Respect robots.txt**: The crawler respects site crawling rules
- **Rate limiting**: 1-2 second delays between requests to avoid overload
- **Terms of Service**: Review API TOS before heavy usage
- **Data usage**: Collected data is for monitoring purposes only
- **Attribution**: Always attribute sources when sharing data

## 12. Next Steps

1. Set up at least Google Custom Search (free 100/day)
2. Add NewsAPI key for comprehensive coverage
3. Test with a manual crawl
4. Enable scheduled crawling if results are good
5. Monitor API usage and adjust frequency
6. Consider paid tiers once you validate the system

## Need Help?

- Google CSE: https://support.google.com/programmable-search
- NewsAPI: https://newsapi.org/docs
- Legistar: Contact your city's IT department
- General issues: Open a GitHub issue
