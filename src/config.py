"""
Configuration settings for the Agentic Fact-Check system.
This file contains all the settings and API keys needed for the system to work.
"""

import os
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """
    Central configuration class for all system settings.
    
    This class loads settings from environment variables and provides
    sensible defaults for the fact-checking system.
    """
    
    def __init__(self):
        # API Keys (all optional - system works without them!)
        self.NEWS_API_KEY = os.getenv('NEWS_API_KEY', '')
        self.TWITTER_BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN', '')
        
        # Processing settings
        self.SCAN_INTERVAL_MINUTES = int(os.getenv('SCAN_INTERVAL_MINUTES', '60'))
        self.MAX_CONTENT_AGE_HOURS = int(os.getenv('MAX_CONTENT_AGE_HOURS', '24'))
        self.BATCH_SIZE = int(os.getenv('BATCH_SIZE', '20'))
        
        # Logging
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        
        # Keywords for crisis detection
        self.CRISIS_KEYWORDS = [
            'pandemic', 'covid', 'outbreak', 'epidemic', 'virus',
            'climate change', 'global warming', 'natural disaster',
            'earthquake', 'hurricane', 'wildfire', 'flood',
            'war', 'conflict', 'invasion', 'military', 'terrorism',
            'economic crisis', 'recession', 'inflation', 'market crash',
            'breaking news', 'urgent', 'emergency', 'alert'
        ]
        
        # Reliable news sources for News API
        self.NEWS_SOURCES = [
            'bbc-news', 'cnn', 'reuters', 'ap-news', 'the-guardian-uk',
            'al-jazeera-english', 'associated-press'
        ]
        
        # RSS feeds for news scanning
        self.RSS_FEEDS = [
            'https://feeds.bbci.co.uk/news/world/rss.xml',
            'http://rss.cnn.com/rss/edition.rss',
            'https://www.reuters.com/rssFeed/worldNews',
            'https://feeds.npr.org/1001/rss.xml'
        ]
        
        # Fact-checking sources
        self.FACT_CHECK_SOURCES = [
            'snopes.com', 'factcheck.org', 'politifact.com',
            'fullfact.org', 'reuters.com/fact-check',
            'apnews.com/hub/ap-fact-check'
        ]
    
    def validate_config(self) -> List[str]:
        """
        Check if required configuration is properly set up.
        Returns a list of missing or invalid settings.
        """
        issues = []
        
        if not self.NEWS_API_KEY:
            issues.append("NEWS_API_KEY is recommended for news scanning (but system works without it)")
        
        if not self.TWITTER_BEARER_TOKEN:
            issues.append("TWITTER_BEARER_TOKEN is recommended for social media monitoring (but system works without it)")
        
        return issues
    
    def get_summary(self) -> dict:
        """Get a summary of current configuration (without sensitive data)."""
        return {
            'batch_size': self.BATCH_SIZE,
            'scan_interval': self.SCAN_INTERVAL_MINUTES,
            'crisis_keywords_count': len(self.CRISIS_KEYWORDS),
            'news_sources_count': len(self.NEWS_SOURCES),
            'rss_feeds_count': len(self.RSS_FEEDS),
            'has_news_key': bool(self.NEWS_API_KEY),
            'has_twitter_key': bool(self.TWITTER_BEARER_TOKEN),
            'system_type': 'free_version'
        }
