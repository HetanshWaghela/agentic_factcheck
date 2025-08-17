"""
Content Scanner - Fetches content from various sources.

This module handles scanning different content sources like news APIs,
RSS feeds, and social media for crisis-related information.
"""

import asyncio
import aiohttp
import feedparser
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from .config import Config
from .models import ContentItem

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ContentScanner:
    """
    Scans multiple content sources for crisis-related information.
    
    This class is responsible for:
    1. Fetching content from news APIs
    2. Parsing RSS feeds
    3. Filtering content for crisis relevance
    """
    
    def __init__(self, config: Config = None):
        self.config = config or Config()
        
    async def scan_all_sources(self) -> List[ContentItem]:
        """
        Scan all configured content sources and return relevant items.
        
        Returns:
            List of ContentItem objects containing crisis-relevant content
        """
        logger.info("Starting content scan across all sources...")
        
        # Run all scanning tasks concurrently
        tasks = [
            self._scan_news_api(),
            self._scan_rss_feeds(),
        ]
        
        # Note: Social media scanning would go here too
        # self._scan_social_media()
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine all results
        all_content = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error in scanning task {i}: {result}")
            else:
                all_content.extend(result)
        
        # Filter for crisis-relevant content
        filtered_content = self._filter_crisis_content(all_content)
        
        logger.info(f"Found {len(filtered_content)} crisis-relevant items out of {len(all_content)} total")
        return filtered_content
    
    async def _scan_news_api(self) -> List[ContentItem]:
        """
        Scan news sources using News API.
        
        This method searches for news articles related to crisis keywords.
        """
        if not self.config.NEWS_API_KEY:
            logger.warning("No News API key configured - skipping news API scan")
            return []
        
        content_items = []
        
        # Limit to first 3 keywords to avoid API rate limits
        keywords_to_search = self.config.CRISIS_KEYWORDS[:3]
        
        async with aiohttp.ClientSession() as session:
            for keyword in keywords_to_search:
                try:
                    url = "https://newsapi.org/v2/everything"
                    params = {
                        'q': keyword,
                        'language': 'en',
                        'sortBy': 'publishedAt',
                        'from': (datetime.now() - timedelta(hours=24)).isoformat(),
                        'apiKey': self.config.NEWS_API_KEY,
                        'pageSize': 20  # Limit results
                    }
                    
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            for article in data.get('articles', []):
                                if self._is_valid_article(article):
                                    content_item = self._create_content_item_from_article(article)
                                    content_items.append(content_item)
                        else:
                            logger.warning(f"News API returned status {response.status} for keyword '{keyword}'")
                
                except Exception as e:
                    logger.error(f"Error scanning News API for keyword '{keyword}': {e}")
                
                # Small delay to be nice to the API
                await asyncio.sleep(0.5)
        
        logger.info(f"Collected {len(content_items)} articles from News API")
        return content_items
    
    async def _scan_rss_feeds(self) -> List[ContentItem]:
        """
        Scan RSS feeds for recent content.
        
        This method parses RSS feeds to get the latest news articles.
        """
        content_items = []
        
        for feed_url in self.config.RSS_FEEDS:
            try:
                # Parse RSS feed (using thread pool since feedparser is blocking)
                loop = asyncio.get_event_loop()
                feed = await loop.run_in_executor(None, feedparser.parse, feed_url)
                
                # Process feed entries
                for entry in feed.entries:
                    try:
                        content_item = self._create_content_item_from_rss_entry(entry, feed)
                        if content_item and self._is_recent_content(content_item):
                            content_items.append(content_item)
                    except Exception as e:
                        logger.error(f"Error processing RSS entry: {e}")
                
            except Exception as e:
                logger.error(f"Error scanning RSS feed {feed_url}: {e}")
        
        logger.info(f"Collected {len(content_items)} articles from RSS feeds")
        return content_items
    
    def _create_content_item_from_article(self, article: Dict[str, Any]) -> ContentItem:
        """Create a ContentItem from a News API article."""
        try:
            published_at = datetime.fromisoformat(
                article['publishedAt'].replace('Z', '+00:00')
            )
        except:
            published_at = datetime.now()
        
        return ContentItem(
            title=article.get('title', ''),
            content=article.get('description', '') or article.get('content', ''),
            source=article.get('source', {}).get('name', 'Unknown'),
            url=article.get('url', ''),
            published_at=published_at,
            source_type='news_api'
        )
    
    def _create_content_item_from_rss_entry(self, entry: Any, feed: Any) -> ContentItem:
        """Create a ContentItem from an RSS feed entry."""
        try:
            # Try to parse the published date
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published_at = datetime(*entry.published_parsed[:6])
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                published_at = datetime(*entry.updated_parsed[:6])
            else:
                published_at = datetime.now()
            
            return ContentItem(
                title=entry.get('title', ''),
                content=entry.get('summary', '') or entry.get('description', ''),
                source=feed.feed.get('title', 'RSS Feed'),
                url=entry.get('link', ''),
                published_at=published_at,
                source_type='rss'
            )
        except Exception as e:
            logger.error(f"Error creating content item from RSS entry: {e}")
            return None
    
    def _is_valid_article(self, article: Dict[str, Any]) -> bool:
        """Check if an article has the minimum required information."""
        return (
            article.get('title') and 
            (article.get('description') or article.get('content')) and
            article.get('url')
        )
    
    def _is_recent_content(self, content_item: ContentItem) -> bool:
        """Check if content is recent enough to be relevant."""
        max_age = timedelta(hours=self.config.MAX_CONTENT_AGE_HOURS)
        return datetime.now() - content_item.published_at <= max_age
    
    def _filter_crisis_content(self, content_items: List[ContentItem]) -> List[ContentItem]:
        """
        Filter content for crisis relevance and sort by relevance score.
        
        Args:
            content_items: List of all content items
            
        Returns:
            List of crisis-relevant content items, sorted by relevance
        """
        filtered_items = []
        
        for item in content_items:
            relevance_score = self._calculate_crisis_relevance(item)
            if relevance_score > 0.2:  # Threshold for relevance
                item.crisis_relevance_score = relevance_score
                filtered_items.append(item)
        
        # Sort by relevance score (highest first)
        filtered_items.sort(key=lambda x: x.crisis_relevance_score, reverse=True)
        
        return filtered_items
    
    def _calculate_crisis_relevance(self, item: ContentItem) -> float:
        """
        Calculate how relevant content is to crisis situations.
        
        Args:
            item: ContentItem to evaluate
            
        Returns:
            Relevance score between 0.0 and 1.0
        """
        # Combine title and content for analysis
        text = f"{item.title} {item.content}".lower()
        
        # Count keyword matches
        keyword_matches = 0
        total_keywords = len(self.config.CRISIS_KEYWORDS)
        
        for keyword in self.config.CRISIS_KEYWORDS:
            if keyword.lower() in text:
                keyword_matches += 1
        
        # Basic scoring: percentage of keywords found
        base_score = keyword_matches / total_keywords
        
        # Boost score for certain indicators
        urgency_words = ['breaking', 'urgent', 'emergency', 'alert', 'critical']
        urgency_boost = sum(1 for word in urgency_words if word in text) * 0.1
        
        # Final score (capped at 1.0)
        final_score = min(base_score + urgency_boost, 1.0)
        
        return final_score
