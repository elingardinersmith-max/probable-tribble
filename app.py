"""
Utility Municipalization Monitor - Production Flask Application
Serves both API and static frontend files
"""

from flask import Flask, jsonify, request, send_from_directory, send_file
from flask_cors import CORS
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

# Data storage directory
DATA_DIR = Path(os.environ.get('DATA_DIR', 'data'))
DATA_DIR.mkdir(exist_ok=True)
MENTIONS_FILE = DATA_DIR / 'mentions.json'
CRAWL_LOG_FILE = DATA_DIR / 'crawl_log.json'

def load_mentions():
    """Load mentions from JSON file"""
    if MENTIONS_FILE.exists():
        try:
            with open(MENTIONS_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.error("Error loading mentions file, returning empty list")
            return []
    return []

def save_mentions(mentions):
    """Save mentions to JSON file"""
    try:
        with open(MENTIONS_FILE, 'w') as f:
            json.dump(mentions, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving mentions: {e}")

def load_crawl_log():
    """Load crawl history"""
    if CRAWL_LOG_FILE.exists():
        try:
            with open(CRAWL_LOG_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

def save_crawl_log(log_entry):
    """Append to crawl log"""
    logs = load_crawl_log()
    logs.append(log_entry)
    logs = logs[-100:]  # Keep only last 100 entries
    try:
        with open(CRAWL_LOG_FILE, 'w') as f:
            json.dump(logs, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving crawl log: {e}")

# Serve frontend
@app.route('/')
def index():
    """Serve the main frontend page"""
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory('static', path)

# API Routes
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'environment': os.environ.get('FLASK_ENV', 'production')
    })

@app.route('/api/mentions', methods=['GET'])
def get_mentions():
    """Get all mentions with optional filtering"""
    try:
        mentions = load_mentions()
        
        # Apply filters from query parameters
        status = request.args.get('status')
        location = request.args.get('location')
        priority = request.args.get('priority')
        
        if status:
            mentions = [m for m in mentions if m.get('status') == status]
        if location and location != 'all':
            mentions = [m for m in mentions if m.get('location') == location]
        if priority and priority != 'all':
            mentions = [m for m in mentions if m.get('priority') == priority]
        
        return jsonify(mentions)
    except Exception as e:
        logger.error(f"Error getting mentions: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/mentions/<mention_id>', methods=['GET'])
def get_mention(mention_id):
    """Get a single mention by ID"""
    try:
        mentions = load_mentions()
        mention = next((m for m in mentions if str(m.get('id')) == mention_id), None)
        
        if mention:
            return jsonify(mention)
        return jsonify({'error': 'Mention not found'}), 404
    except Exception as e:
        logger.error(f"Error getting mention: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/mentions/<mention_id>', methods=['PATCH'])
def update_mention(mention_id):
    """Update a mention (status, tags, etc.)"""
    try:
        mentions = load_mentions()
        data = request.json
        
        mention_index = next((i for i, m in enumerate(mentions) if str(m.get('id')) == mention_id), None)
        
        if mention_index is not None:
            # Update allowed fields
            allowed_fields = ['status', 'tags', 'notes', 'priority']
            for field in allowed_fields:
                if field in data:
                    mentions[mention_index][field] = data[field]
            
            mentions[mention_index]['updated_at'] = datetime.now().isoformat()
            save_mentions(mentions)
            return jsonify(mentions[mention_index])
        
        return jsonify({'error': 'Mention not found'}), 404
    except Exception as e:
        logger.error(f"Error updating mention: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/mentions/<mention_id>', methods=['DELETE'])
def delete_mention(mention_id):
    """Delete a mention"""
    try:
        mentions = load_mentions()
        original_count = len(mentions)
        mentions = [m for m in mentions if str(m.get('id')) != mention_id]
        
        if len(mentions) < original_count:
            save_mentions(mentions)
            return jsonify({'message': 'Mention deleted successfully'})
        
        return jsonify({'error': 'Mention not found'}), 404
    except Exception as e:
        logger.error(f"Error deleting mention: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/crawl', methods=['POST'])
def trigger_crawl():
    """Trigger a web crawl"""
    try:
        from crawler import run_crawl
        
        # Get crawl parameters
        data = request.json or {}
        queries = data.get('queries', [
            'utility municipalization',
            'public power initiative',
            'municipal utility',
            'franchise agreement utility'
        ])
        max_results_per_query = data.get('max_results_per_query', 10)
        
        logger.info(f"Starting crawl with {len(queries)} queries")
        
        # Run the crawl
        new_mentions = run_crawl(queries, max_results_per_query)
        
        # Load existing mentions
        existing_mentions = load_mentions()
        existing_urls = {m.get('url') for m in existing_mentions}
        
        # Filter out duplicates
        unique_new_mentions = [
            m for m in new_mentions 
            if m.get('url') not in existing_urls
        ]
        
        # Add to storage
        all_mentions = existing_mentions + unique_new_mentions
        save_mentions(all_mentions)
        
        # Log the crawl
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'queries': queries,
            'total_found': len(new_mentions),
            'new_unique': len(unique_new_mentions),
            'duplicates': len(new_mentions) - len(unique_new_mentions)
        }
        save_crawl_log(log_entry)
        
        logger.info(f"Crawl complete: {len(unique_new_mentions)} new mentions")
        
        return jsonify({
            'success': True,
            'new_mentions': len(unique_new_mentions),
            'total_found': len(new_mentions),
            'duplicates': len(new_mentions) - len(unique_new_mentions),
            'mentions': unique_new_mentions[:10]  # Return first 10 for preview
        })
        
    except Exception as e:
        logger.error(f"Crawl error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get statistics about mentions"""
    try:
        mentions = load_mentions()
        
        total = len(mentions)
        pending = len([m for m in mentions if m.get('status') == 'pending'])
        approved = len([m for m in mentions if m.get('status') == 'approved'])
        deleted = len([m for m in mentions if m.get('status') == 'deleted'])
        
        # Count today's captures
        today = datetime.now().date()
        today_captures = 0
        for m in mentions:
            try:
                capture_date = datetime.fromisoformat(m.get('capturedAt', '2000-01-01')).date()
                if capture_date == today:
                    today_captures += 1
            except:
                pass
        
        # Get unique locations and sources
        locations = list(set(m.get('location') for m in mentions if m.get('location')))
        sources = list(set(m.get('source') for m in mentions if m.get('source')))
        
        return jsonify({
            'total': total,
            'pending': pending,
            'approved': approved,
            'deleted': deleted,
            'today_captured': today_captures,
            'locations': locations,
            'sources': sources
        })
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/crawl/log', methods=['GET'])
def get_crawl_log():
    """Get crawl history"""
    try:
        logs = load_crawl_log()
        limit = request.args.get('limit', 20, type=int)
        return jsonify(logs[-limit:])
    except Exception as e:
        logger.error(f"Error getting crawl log: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/export', methods=['GET'])
def export_data():
    """Export all mentions as JSON"""
    try:
        mentions = load_mentions()
        status_filter = request.args.get('status')
        
        if status_filter:
            mentions = [m for m in mentions if m.get('status') == status_filter]
        
        return jsonify({
            'exported_at': datetime.now().isoformat(),
            'count': len(mentions),
            'mentions': mentions
        })
    except Exception as e:
        logger.error(f"Error exporting data: {e}")
        return jsonify({'error': str(e)}), 500

# Error handlers
@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    # If it's an API request, return JSON
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Not found'}), 404
    # Otherwise serve the frontend (for client-side routing)
    return send_from_directory('static', 'index.html')

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    logger.error(f"Server error: {e}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Create data directory if it doesn't exist
    DATA_DIR.mkdir(exist_ok=True)
    
    # Initialize empty mentions file if it doesn't exist
    if not MENTIONS_FILE.exists():
        save_mentions([])
    
    # Get port from environment variable (for deployment platforms)
    port = int(os.environ.get('PORT', 5000))
    
    # Run the Flask app
    logger.info(f"Starting Utility Monitor on port {port}")
    logger.info(f"Frontend: http://localhost:{port}")
    logger.info(f"API: http://localhost:{port}/api/health")
    
    app.run(
        debug=os.environ.get('FLASK_DEBUG', 'False').lower() == 'true',
        host='0.0.0.0',
        port=port
    )
