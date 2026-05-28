import json
import requests
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def fetch_feed(source: str, url: Optional[str] = None, api_key: Optional[str] = None) -> list[dict]:
    """
    Fetch records from external REST/CSV feeds.
    
    Args:
        source: Source identifier (e.g., 'feed_a', 'feed_b')
        url: Optional feed URL override
        api_key: Optional API key for authenticated feeds
    
    Returns:
        List of record dicts
    """
    # Feed URLs configured via environment or passed directly
    feed_urls = {
        'feed_a': 'https://api.example.com/feed-a',
        'feed_b': 'https://api.example.com/feed-b',
    }
    feed_url = url or feed_urls.get(source)
    
    if not feed_url:
        logger.warning(f"No URL configured for source: {source}")
        return []
    
    headers = {}
    if api_key:
        headers['Authorization'] = f'Bearer {api_key}'
    
    try:
        response = requests.get(feed_url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Handle different response formats
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            if 'records' in data:
                return data['records']
            if 'results' in data:
                return data['results']
            if 'data' in data:
                return data['data']
        
        logger.warning(f"Unexpected response format from {source}")
        return []
        
    except requests.RequestException as e:
        logger.error(f"Failed to fetch from {source}: {e}")
        return []


def fetch_csv_feed(url: str) -> list[dict]:
    """Fetch and parse a CSV feed."""
    import csv
    import io
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        reader = csv.DictReader(io.StringIO(response.text))
        return list(reader)
    except requests.RequestException as e:
        logger.error(f"Failed to fetch CSV from {url}: {e}")
        return []