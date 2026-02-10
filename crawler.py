"""
Web Crawler for Utility Municipalization Mentions
Uses Google Custom Search API, NewsAPI, and custom .gov scrapers
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
import re
import os
from urllib.parse import urlparse, urljoin
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY', '')
GOOGLE_CSE_ID = os.environ.get('GOOGLE_CSE_ID', '')
NEWS_API_KEY = os.environ.get('NEWS_API_KEY', '')

# Rate limiting
REQUEST_DELAY = 1  # seconds between requests

def extract_location(text):
    """Extract location (city, state) from text"""
    # Common US states and cities patterns
    state_abbr = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 
                  'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
                  'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
                  'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
                  'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY']
    
    cities = ['San Francisco', 'Los Angeles', 'San Diego', 'New York', 'Chicago',
              'Houston', 'Phoenix', 'Philadelphia', 'San Antonio', 'Dallas',
              'Austin', 'Jacksonville', 'Seattle', 'Denver', 'Portland',
              'Boston', 'Detroit', 'Nashville', 'Minneapolis', 'Boulder',
              'Sacramento', 'Atlanta', 'Miami', 'Cleveland', 'Pittsburgh']
    
    # Try to find city, state pattern
    for city in cities:
        if city.lower() in text.lower():
            for state in state_abbr:
                if f'{city}, {state}' in text or f'{city.lower()}, {state.lower()}' in text.lower():
                    return f'{city}, {state}'
            return city
    
    # Try to find state
    for state in state_abbr:
        if re.search(rf'\b{state}\b', text):
            return state
    
    return 'Unknown'

def extract_utility(text):
    """Extract utility company name from text"""
    utilities = [
        'Pacific Gas & Electric', 'PG&E', 'Southern California Edison', 'SCE',
        'San Diego Gas & Electric', 'SDG&E', 'Duke Energy', 'ComEd',
        'Xcel Energy', 'Consolidated Edison', 'Con Edison', 'Dominion Energy',
        'FirstEnergy', 'Entergy', 'AEP', 'American Electric Power',
        'Exelon', 'NextEra', 'Florida Power & Light', 'FPL',
        'Georgia Power', 'Alabama Power', 'PSE&G', 'National Grid',
        'Eversource', 'Avista', 'Puget Sound Energy', 'PSE',
        'Portland General Electric', 'PGE', 'CenterPoint', 'Ameren',
        'WE Energies', 'Consumers Energy', 'DTE Energy', 'Oncor',
        'CPS Energy', 'Austin Energy', 'Seattle City Light', 'LADWP',
        'Sacramento Municipal Utility District', 'SMUD', 'Salt River Project',
        'SRP', 'TVA', 'Tennessee Valley Authority'
    ]
    
    for utility in utilities:
        if utility.lower() in text.lower():
            return utility
    
    return 'Municipal Utility Discussion'

def determine_utility_type(text):
    """Determine utility type from text"""
    text_lower = text.lower()
    
    if any(word in text_lower for word in ['water', 'sewer', 'wastewater']):
        return 'Water'
    elif any(word in text_lower for word in ['gas', 'natural gas']):
        return 'Gas'
    elif any(word in text_lower for word in ['multi-utility', 'multiple utilities', 'electric and gas', 'electric and water']):
        return 'Multi-utility'
    else:
        return 'Electric'

def determine_stage(text):
    """Determine the stage of municipalization effort"""
    text_lower = text.lower()
    
    if any(word in text_lower for word in ['ballot', 'vote', 'election', 'referendum', 'measure']):
        return 'Ballot Measure'
    elif any(word in text_lower for word in ['lawsuit', 'litigation', 'court', 'legal', 'eminent domain', 'condemnation']):
        return 'Litigation'
    elif any(word in text_lower for word in ['active', 'proceeding', 'proposal', 'plan', 'moving forward', 'approved', 'authorized']):
        return 'Active'
    else:
        return 'Exploratory'

def determine_priority(text):
    """Determine priority level"""
    text_lower = text.lower()
    high_priority_terms = ['vote', 'lawsuit', 'court', 'ballot', 'approved', 
                           'authorized', 'emergency', 'urgent', 'deadline']
    
    if any(term in text_lower for term in high_priority_terms):
        return 'high'
    return 'normal'

def search_google(query, num_results=10):
    """Search Google Custom Search API with pagination support"""
    if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
        logger.warning("Google API credentials not configured")
        return []
    
    results = []
    
    try:
        # Google CSE API returns max 10 results per request
        # For more results, we need to paginate
        pages_needed = (num_results + 9) // 10  # ceiling division
        
        for page in range(pages_needed):
            start_index = page * 10 + 1
            
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': GOOGLE_API_KEY,
                'cx': GOOGLE_CSE_ID,
                'q': query,
                'num': min(10, num_results - len(results)),
                'start': start_index,
                'dateRestrict': 'm6'  # Last 6 months for relevance
            }
            
            logger.info(f"Google search: {query} (page {page + 1})")
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            for item in data.get('items', []):
                results.append({
                    'title': item.get('title', ''),
                    'url': item.get('link', ''),
                    'snippet': item.get('snippet', ''),
                    'source': urlparse(item.get('link', '')).netloc,
                    'date': item.get('pagemap', {}).get('metatags', [{}])[0].get('article:published_time', '')
                })
            
            # Check if we have enough results
            if len(results) >= num_results:
                break
            
            # Rate limiting
            time.sleep(REQUEST_DELAY)
        
        logger.info(f"Google search found {len(results)} results for: {query}")
        return results[:num_results]
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Google search request error: {e}")
        return []
    except Exception as e:
        logger.error(f"Google search error: {e}")
        return []

def search_newsapi(query, num_results=10):
    """Search NewsAPI.org for recent news articles"""
    if not NEWS_API_KEY:
        logger.warning("NewsAPI key not configured")
        return []
    
    try:
        url = "https://newsapi.org/v2/everything"
        
        # Calculate date range (last 30 days)
        to_date = datetime.now()
        from_date = to_date - timedelta(days=30)
        
        params = {
            'apiKey': NEWS_API_KEY,
            'q': query,
            'language': 'en',
            'sortBy': 'publishedAt',
            'pageSize': min(num_results, 100),  # API max is 100
            'from': from_date.strftime('%Y-%m-%d'),
            'to': to_date.strftime('%Y-%m-%d')
        }
        
        logger.info(f"NewsAPI search: {query}")
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        results = []
        
        for article in data.get('articles', []):
            # Filter out removed articles
            if article.get('title') == '[Removed]':
                continue
                
            results.append({
                'title': article.get('title', ''),
                'url': article.get('url', ''),
                'snippet': article.get('description', ''),
                'source': article.get('source', {}).get('name', urlparse(article.get('url', '')).netloc),
                'date': article.get('publishedAt', '')
            })
        
        logger.info(f"NewsAPI found {len(results)} results for: {query}")
        return results
        
    except requests.exceptions.RequestException as e:
        logger.error(f"NewsAPI request error: {e}")
        return []
    except Exception as e:
        logger.error(f"NewsAPI error: {e}")
        return []

def scrape_ferc_filings():
    """Scrape Federal Energy Regulatory Commission filings"""
    results = []
    
    try:
        # FERC eLibrary search for municipalization-related filings
        base_url = "https://elibrary.ferc.gov"
        
        # Search for recent dockets related to municipalization
        search_terms = ['municipal', 'municipalization', 'public power', 'condemnation']
        
        for term in search_terms:
            try:
                # Note: FERC has a search API but requires specific access
                # This is a simplified example - you'd need to implement proper API access
                logger.info(f"Searching FERC for: {term}")
                
                # Placeholder - implement actual FERC API integration
                # See: https://www.ferc.gov/docs-filing/elibrary-api.asp
                
                time.sleep(REQUEST_DELAY)
                
            except Exception as e:
                logger.error(f"FERC search error for {term}: {e}")
                continue
        
    except Exception as e:
        logger.error(f"FERC scraping error: {e}")
    
    return results

def scrape_state_puc_sites():
    """Scrape state Public Utility Commission websites"""
    results = []
    
    # Major state PUC websites
    puc_sites = {
        'California': 'https://www.cpuc.ca.gov',
        'Texas': 'https://www.puc.texas.gov',
        'New York': 'https://www.dps.ny.gov',
        'Florida': 'https://www.psc.state.fl.us',
        'Illinois': 'https://www.icc.illinois.gov',
        'Colorado': 'https://puc.colorado.gov',
    }
    
    for state, base_url in puc_sites.items():
        try:
            logger.info(f"Scraping {state} PUC")
            
            # Try to find news/press releases page
            news_paths = ['/news', '/press-releases', '/newsroom', '/media']
            
            for path in news_paths:
                try:
                    url = base_url + path
                    response = requests.get(url, timeout=10, headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    })
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Look for links containing municipalization keywords
                        keywords = ['municipal', 'franchise', 'public power', 'takeover']
                        
                        for link in soup.find_all('a', href=True):
                            link_text = link.get_text().lower()
                            href = link['href']
                            
                            if any(keyword in link_text for keyword in keywords):
                                full_url = urljoin(base_url, href)
                                
                                results.append({
                                    'title': link.get_text().strip(),
                                    'url': full_url,
                                    'snippet': f'{state} PUC: {link.get_text().strip()[:200]}',
                                    'source': f'{state} Public Utility Commission',
                                    'date': datetime.now().isoformat()
                                })
                        
                        break  # Found a valid news page
                        
                except Exception as e:
                    logger.debug(f"Failed to scrape {url}: {e}")
                    continue
            
            time.sleep(REQUEST_DELAY)
            
        except Exception as e:
            logger.error(f"Error scraping {state} PUC: {e}")
            continue
    
    logger.info(f"Found {len(results)} results from state PUC sites")
    return results

def scrape_legistar_sites():
    """Scrape city council agendas from Legistar-based systems"""
    results = []
    
    # Major cities using Legistar for council agendas
    legistar_cities = {
        'Boulder, CO': 'https://bouldercolorado.gov/api/v2/legistar',
        'San Francisco, CA': 'https://sfgov.legistar.com/api/v1',
        'Seattle, WA': 'https://seattle.legistar.com/api/v1',
        'Austin, TX': 'https://austin.legistar.com/api/v1',
        'Portland, OR': 'https://portland.legistar.com/api/v1',
        'Minneapolis, MN': 'https://lims.minneapolismn.gov/api/v1'
    }
    
    keywords = ['municipal', 'utility', 'franchise', 'public power', 'electric', 
                'xcel', 'pge', 'duke energy', 'municipalization']
    
    for city, api_base in legistar_cities.items():
        try:
            logger.info(f"Searching {city} council agendas")
            
            # Get recent meetings (last 90 days)
            events_url = f"{api_base}/Events"
            params = {
                '$filter': f"EventDate ge datetime'{(datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')}'",
                '$top': 50
            }
            
            response = requests.get(events_url, params=params, timeout=10)
            
            if response.status_code != 200:
                logger.debug(f"Failed to access {city} Legistar API")
                continue
            
            events = response.json()
            
            for event in events:
                event_id = event.get('EventId')
                if not event_id:
                    continue
                
                # Get agenda items for this meeting
                items_url = f"{api_base}/Events/{event_id}/EventItems"
                items_response = requests.get(items_url, timeout=10)
                
                if items_response.status_code != 200:
                    continue
                
                items = items_response.json()
                
                for item in items:
                    title = item.get('EventItemTitle', '')
                    matter_name = item.get('EventItemMatterName', '')
                    matter_file = item.get('EventItemMatterFile', '')
                    
                    combined_text = f"{title} {matter_name}".lower()
                    
                    # Check if any keyword is in the item
                    if any(keyword in combined_text for keyword in keywords):
                        event_date = event.get('EventDate', '')[:10]
                        
                        results.append({
                            'title': f"{city} Council: {title[:100]}",
                            'url': f"{api_base.replace('/api/v1', '')}/MeetingDetail.aspx?ID={event_id}",
                            'snippet': f"Council agenda item: {matter_name}. {title[:150]}",
                            'source': f'{city} City Council',
                            'date': event_date
                        })
            
            time.sleep(REQUEST_DELAY)
            
        except Exception as e:
            logger.error(f"Error scraping {city} Legistar: {e}")
            continue
    
    logger.info(f"Found {len(results)} results from Legistar sites")
    return results

def scrape_state_legislature_sites():
    """Scrape state legislature bill tracking sites"""
    results = []
    
    # State legislature tracking URLs
    state_leg_sites = {
        'California': {
            'search_url': 'https://leginfo.legislature.ca.gov/faces/billSearchClient.xhtml',
            'keywords': ['municipal utility', 'public power', 'community choice']
        },
        'Colorado': {
            'search_url': 'https://leg.colorado.gov/bills',
            'keywords': ['municipal utility', 'franchise']
        },
        'Texas': {
            'search_url': 'https://capitol.texas.gov/Search/BillSearch.aspx',
            'keywords': ['municipal utility', 'municipalization']
        }
    }
    
    for state, config in state_leg_sites.items():
        try:
            logger.info(f"Searching {state} legislature bills")
            
            # This is a simplified example - each state has different APIs/formats
            # You would need to implement specific scrapers for each state
            
            # Placeholder for actual implementation
            # Most states have APIs or RSS feeds available
            
            time.sleep(REQUEST_DELAY)
            
        except Exception as e:
            logger.error(f"Error scraping {state} legislature: {e}")
            continue
    
    return results

def scrape_ballot_initiatives():
    """Scrape ballot initiative tracking sites"""
    results = []
    
    try:
        # Ballotpedia tracks ballot measures
        # Note: Would need to implement proper scraping with consent
        logger.info("Searching ballot initiative databases")
        
        # Major ballot tracking sources:
        # - Ballotpedia
        # - National Conference of State Legislatures
        # - State Secretary of State websites
        
        # Placeholder for implementation
        
    except Exception as e:
        logger.error(f"Error scraping ballot initiatives: {e}")
    
    return results

def search_news_fallback(query, num_results=10):
    """Fallback: Generate simulated results based on real patterns"""
    # This is a fallback for demo purposes
    # In production, you'd use actual news APIs like NewsAPI.org
    
    base_results = [
        {
            'title': f'{query.title()} Discussion in Boulder City Council',
            'url': f'https://example.com/boulder-{query.replace(" ", "-")}',
            'snippet': f'Boulder City Council debates {query} at recent meeting. Officials discuss feasibility study and timeline for implementation.',
            'source': 'Boulder Daily Camera'
        },
        {
            'title': f'California Counties Explore {query.title()}',
            'url': f'https://example.com/california-{query.replace(" ", "-")}',
            'snippet': f'Multiple California counties are examining {query} options as utility rates continue to rise.',
            'source': 'Sacramento Bee'
        },
        {
            'title': f'Texas Legislature Considers {query.title()} Bill',
            'url': f'https://example.com/texas-{query.replace(" ", "-")}',
            'snippet': f'New legislation would streamline {query} process for Texas municipalities.',
            'source': 'Texas Tribune'
        }
    ]
    
    return base_results[:num_results]

def scrape_rss_feeds():
    """Scrape RSS feeds from local news sources"""
    # List of RSS feeds to monitor
    feeds = [
        'https://www.utilitydive.com/feeds/news/',
        # Add more RSS feeds here
    ]
    
    results = []
    
    for feed_url in feeds:
        try:
            response = requests.get(feed_url, timeout=10)
            if response.status_code == 200:
                # Parse RSS feed (would need feedparser library)
                # This is a placeholder
                pass
        except Exception as e:
            print(f"RSS feed error for {feed_url}: {e}")
    
    return results

def process_search_result(result):
    """Process a search result into a mention object"""
    text = f"{result['title']} {result['snippet']}"
    
    mention = {
        'id': f"{int(time.time() * 1000)}{hash(result['url']) % 10000}",
        'title': result['title'],
        'url': result['url'],
        'snippet': result['snippet'],
        'source': result['source'],
        'location': extract_location(text),
        'utility': extract_utility(text),
        'utilityType': determine_utility_type(text),
        'stage': determine_stage(text),
        'priority': determine_priority(text),
        'capturedAt': datetime.now().isoformat(),
        'status': 'pending',
        'tags': []
    }
    
    return mention

def run_crawl(queries, max_results_per_query=10):
    """Run a comprehensive crawl across all sources"""
    all_mentions = []
    seen_urls = set()
    
    logger.info(f"Starting comprehensive crawl with {len(queries)} queries...")
    
    # 1. Google Custom Search
    logger.info("=== Phase 1: Google Custom Search ===")
    for query in queries:
        results = search_google(query, max_results_per_query)
        
        for result in results:
            url = result.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                mention = process_search_result(result)
                all_mentions.append(mention)
        
        time.sleep(REQUEST_DELAY)
    
    logger.info(f"Google Search: {len(all_mentions)} mentions found")
    
    # 2. NewsAPI
    logger.info("=== Phase 2: NewsAPI.org ===")
    initial_count = len(all_mentions)
    
    for query in queries:
        results = search_newsapi(query, max_results_per_query)
        
        for result in results:
            url = result.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                mention = process_search_result(result)
                all_mentions.append(mention)
        
        time.sleep(REQUEST_DELAY)
    
    logger.info(f"NewsAPI: {len(all_mentions) - initial_count} new mentions found")
    
    # 3. State PUC Sites
    logger.info("=== Phase 3: State Public Utility Commissions ===")
    initial_count = len(all_mentions)
    
    puc_results = scrape_state_puc_sites()
    for result in puc_results:
        url = result.get('url', '')
        if url and url not in seen_urls:
            seen_urls.add(url)
            mention = process_search_result(result)
            all_mentions.append(mention)
    
    logger.info(f"State PUCs: {len(all_mentions) - initial_count} new mentions found")
    
    # 4. Legistar City Council Agendas
    logger.info("=== Phase 4: City Council Agendas (Legistar) ===")
    initial_count = len(all_mentions)
    
    legistar_results = scrape_legistar_sites()
    for result in legistar_results:
        url = result.get('url', '')
        if url and url not in seen_urls:
            seen_urls.add(url)
            mention = process_search_result(result)
            all_mentions.append(mention)
    
    logger.info(f"Legistar: {len(all_mentions) - initial_count} new mentions found")
    
    # 5. FERC Filings (if implemented)
    logger.info("=== Phase 5: FERC Filings ===")
    initial_count = len(all_mentions)
    
    ferc_results = scrape_ferc_filings()
    for result in ferc_results:
        url = result.get('url', '')
        if url and url not in seen_urls:
            seen_urls.add(url)
            mention = process_search_result(result)
            all_mentions.append(mention)
    
    logger.info(f"FERC: {len(all_mentions) - initial_count} new mentions found")
    
    # Summary
    logger.info(f"\n{'='*60}")
    logger.info(f"CRAWL COMPLETE")
    logger.info(f"Total mentions found: {len(all_mentions)}")
    logger.info(f"Unique URLs: {len(seen_urls)}")
    logger.info(f"{'='*60}\n")
    
    return all_mentions

def search_specific_sources():
    """Search specific government and utility commission sources"""
    # These would be custom scrapers for specific sites
    sources = [
        # City council meeting agendas
        # State legislature bill trackers
        # Public utility commission filings
        # etc.
    ]
    
    results = []
    # Implementation would go here
    return results

if __name__ == '__main__':
    # Test the crawler
    test_queries = [
        'utility municipalization news',
        'public power initiative',
        'municipal utility ballot'
    ]
    
    mentions = run_crawl(test_queries, 5)
    print(f"\nFound {len(mentions)} mentions:")
    for m in mentions[:3]:
        print(f"  - {m['title']}")
