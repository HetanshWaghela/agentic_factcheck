"""
Configuration management for the fact-checking system.
Handles API keys, user inputs, and system settings.
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration class for fact-checking system."""
    
    # API Keys
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    SERPER_API_KEY = os.getenv("SERPER_API_KEY") 
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    
    # System settings
    USER_AGENT = "factcheck/1.0"
    
    # Default values
    DEFAULT_MAX_CHARS = 3000
    DEFAULT_NUM_ARTICLES = 1
    DEFAULT_TIME_RANGE = 'm'
    DEFAULT_VERIFICATION_DEPTH = 'quick'
    
    # Processing settings
    BATCH_SIZE = 3
    SOURCES_PER_CLAIM = {
        'quick': 5,
        'thorough': 8
    }
    
    # Time range mappings
    TIME_RANGES = {
        'h': 'qdr:h',
        'd': 'qdr:d', 
        'w': 'qdr:w',
        'm': 'qdr:m1',
        'y': 'qdr:y'
    }
    
    @classmethod
    def setup_environment(cls):
        """Set up environment variables."""
        os.environ["USER_AGENT"] = cls.USER_AGENT
    
    @classmethod
    def get_credible_sources(cls):
        """Return categorized credible sources."""
        return {
            'tier1': [
                'reuters.com', 'ap.org', 'bbc.com', 'npr.org', 'pbs.org',
                'factcheck.org', 'snopes.com', 'politifact.com',
                'nature.com', 'science.org', 'nejm.org'
            ],
            'tier2': [
                'cnn.com', 'nytimes.com', 'washingtonpost.com', 'wsj.com',
                'theguardian.com', 'economist.com', 'time.com', 'newsweek.com'
            ],
            'diverse_sources': [
                'foxnews.com', 'breitbart.com',
                'huffpost.com', 'vox.com', 
                'reason.com', 'libertarianism.org'
            ]
        }

def get_user_inputs():
    """Get configuration from user input."""
    print("Fact-Checking Agent Configuration")
    print("=" * 40)
    
    search_topic = input("Enter search topic (e.g., 'climate change', 'global trade'): ").strip()
    if not search_topic:
        search_topic = "global trade"
        print(f"Using default topic: {search_topic}")
    
    print("\nWebsite options:")
    print("- Enter specific site (e.g., 'cnn.com', 'whitehouse.gov')")
    print("- Enter 'any' for all websites")
    site = input("Enter website (or 'any' for all sites): ").strip().lower()
    
    print("\nTime range options:")
    print("- h: Past hour")
    print("- d: Past day") 
    print("- w: Past week")
    print("- m: Past month (default)")
    print("- y: Past year")
    time_range = input("Enter time range [h/d/w/m/y] (default: m): ").strip().lower()
    if time_range not in Config.TIME_RANGES:
        time_range = Config.DEFAULT_TIME_RANGE
    
    try:
        max_chars = int(input(f"Enter max characters to analyze (default: {Config.DEFAULT_MAX_CHARS}): ").strip() or str(Config.DEFAULT_MAX_CHARS))
        if max_chars <= 0:
            max_chars = Config.DEFAULT_MAX_CHARS
    except ValueError:
        max_chars = Config.DEFAULT_MAX_CHARS
        print(f"Invalid input, using default: {max_chars}")
    
    try:
        num_articles = int(input(f"Enter number of articles to analyze (default: {Config.DEFAULT_NUM_ARTICLES}): ").strip() or str(Config.DEFAULT_NUM_ARTICLES))
        if num_articles <= 0:
            num_articles = Config.DEFAULT_NUM_ARTICLES
    except ValueError:
        num_articles = Config.DEFAULT_NUM_ARTICLES
        print(f"Invalid input, using default: {num_articles}")
    
    print("\nVerification depth:")
    print("- quick: 5 sources per claim (faster)")
    print("- thorough: 8 sources per claim (more accurate)")
    depth = input("Enter verification depth [quick/thorough] (default: quick): ").strip().lower()
    if depth not in Config.SOURCES_PER_CLAIM:
        depth = Config.DEFAULT_VERIFICATION_DEPTH
    
    return {
        'search_topic': search_topic,
        'site': site,
        'time_range': Config.TIME_RANGES[time_range],
        'max_chars': max_chars,
        'num_articles': num_articles,
        'sources_per_claim': Config.SOURCES_PER_CLAIM[depth]
    }
