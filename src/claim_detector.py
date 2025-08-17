"""
Claim Detector - Extracts verifiable claims from content.

This module uses FREE natural language processing techniques 
to identify specific factual statements that can be fact-checked and verified.
No paid APIs required!
"""

import asyncio
import re
import logging
from typing import List, Dict, Any
from datetime import datetime

# Import free NLP libraries
try:
    import nltk
    from textblob import TextBlob
    
    # Download required NLTK data (only happens once)
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True) 
    nltk.download('averaged_perceptron_tagger', quiet=True)
    nltk.download('vader_lexicon', quiet=True)
    NLP_AVAILABLE = True
except ImportError:
    NLP_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("NLTK/TextBlob not available - using basic text processing")

from .config import Config
from .models import ContentItem, Claim

logger = logging.getLogger(__name__)


class ClaimDetector:
    """
    Detects and extracts factual claims from content using FREE techniques.
    
    This class uses advanced natural language processing to:
    1. Identify specific factual statements
    2. Classify claims by type using pattern matching
    3. Assess urgency and verifiability using sentiment analysis
    4. Extract entities using named entity recognition
    
    No paid APIs required - everything runs locally and is FREE!
    """
    
    def __init__(self, config=None):
        self.config = config or Config()
        
        # Patterns for different types of claims
        self.statistical_patterns = [
            r'\d+\.?\d*\s*%',  # Percentages: 45%, 12.5%
            r'\d+\.?\d*\s*(million|billion|thousand)',  # Large numbers
            r'increased?\s+by\s+\d+',  # "increased by 20"
            r'decreased?\s+by\s+\d+',  # "decreased by 15"
            r'\d+\.?\d*\s+times',  # "5 times higher"
            r'study\s+(shows?|found|indicates?)',  # Study references
            r'research\s+(shows?|found|indicates?)',  # Research references
            r'according\s+to\s+(data|statistics?|study)',  # Data references
        ]
        
        self.event_patterns = [
            r'(happened|occurred|took place)\s+(on|in|at)',  # Past events
            r'(will happen|scheduled|planned)\s+for',  # Future events
            r'(announced|confirmed|reported)\s+(that|yesterday|today)',  # Announcements
            r'(attack|explosion|accident|meeting|summit|election)',  # Event types
            r'(signed|approved|rejected|passed)\s+(the|a|an)',  # Official actions
        ]
        
        self.policy_patterns = [
            r'(government|president|minister|official)\s+(announced|said|declared)',
            r'(new|proposed)\s+(law|regulation|policy|bill)',
            r'(banned|approved|authorized|prohibited)',
            r'(legislation|act|amendment)\s+(will|would|has)',
            r'(budget|funding|investment)\s+of\s+\$?\d+',
        ]
        
        # Urgency keywords with scores
        self.urgency_keywords = {
            'breaking': 4, 'urgent': 3, 'emergency': 5, 'critical': 4,
            'immediate': 3, 'alert': 3, 'warning': 2, 'crisis': 4,
            'death': 4, 'died': 4, 'attack': 4, 'explosion': 4,
            'pandemic': 3, 'outbreak': 3, 'disaster': 3, 'conflict': 3
        }
        
    async def extract_claims_from_content(self, content_items: List[ContentItem]) -> List[Claim]:
        """
        Extract verifiable claims from a list of content items.
        
        Args:
            content_items: List of content to analyze
            
        Returns:
            List of extracted claims
        """
        logger.info(f"Extracting claims from {len(content_items)} content items...")
        
        all_claims = []
        
        for content_item in content_items:
            try:
                claims = await self.extract_claims_from_single_item(content_item)
                all_claims.extend(claims)
            except Exception as e:
                logger.error(f"Error extracting claims from {content_item.source}: {e}")
        
        logger.info(f"Extracted {len(all_claims)} claims total")
        return all_claims
    
    async def extract_claims_from_single_item(self, content_item: ContentItem) -> List[Claim]:
        """
        Extract claims from a single content item using advanced NLP.
        
        This uses multiple techniques:
        1. Sentence segmentation (with TextBlob if available)
        2. Pattern matching for different claim types
        3. Entity extraction using NLP
        4. Sentiment analysis for urgency assessment
        """
        claims = []
        text = f"{content_item.title} {content_item.content}"
        
        # Break text into sentences
        sentences = self._split_into_sentences(text)
        
        # Analyze each sentence for claims
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 15:  # Skip very short sentences
                continue
            
            # Check for statistical claims
            if self._matches_patterns(sentence, self.statistical_patterns):
                claim = self._create_claim(
                    sentence, 'statistic', content_item, 
                    urgency_boost=2, verifiability=8
                )
                claims.append(claim)
            
            # Check for event claims  
            elif self._matches_patterns(sentence, self.event_patterns):
                claim = self._create_claim(
                    sentence, 'event', content_item,
                    urgency_boost=1, verifiability=7
                )
                claims.append(claim)
            
            # Check for policy claims
            elif self._matches_patterns(sentence, self.policy_patterns):
                claim = self._create_claim(
                    sentence, 'policy', content_item,
                    urgency_boost=3, verifiability=9
                )
                claims.append(claim)
        
        return claims
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences using the best available method."""
        if NLP_AVAILABLE:
            try:
                blob = TextBlob(text)
                return [str(sentence) for sentence in blob.sentences]
            except:
                pass
        
        # Fallback: simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _matches_patterns(self, text: str, patterns: List[str]) -> bool:
        """Check if text matches any of the given regex patterns."""
        text_lower = text.lower()
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return True
        return False
    
    def _create_claim(self, claim_text: str, claim_type: str, 
                     content_item: ContentItem, urgency_boost: int = 0, 
                     verifiability: int = 5) -> Claim:
        """Create a Claim object with enhanced analysis."""
        
        # Extract entities
        entities = self._extract_entities(claim_text)
        
        # Calculate urgency
        base_urgency = self._assess_urgency(claim_text)
        final_urgency = min(base_urgency + urgency_boost, 10)
        
        # Generate unique ID
        claim_id = f"{content_item.source}_{hash(claim_text) % 100000}"
        
        return Claim(
            id=claim_id,
            claim_text=claim_text,
            claim_type=claim_type,
            entities=entities,
            urgency=final_urgency,
            verifiability=verifiability,
            source_item=content_item,
            detected_at=datetime.now()
        )
    
    def _extract_entities(self, text: str) -> List[str]:
        """
        Extract entities using the best available method.
        
        Tries advanced NLP first, falls back to simple pattern matching.
        """
        entities = []
        
        if NLP_AVAILABLE:
            try:
                # Use TextBlob for part-of-speech tagging
                blob = TextBlob(text)
                
                # Extract proper nouns
                for word, pos in blob.tags:
                    if pos in ['NNP', 'NNPS']:  # Proper nouns
                        if len(word) > 2 and word not in ['The', 'A', 'An', 'This', 'That']:
                            entities.append(word)
            except:
                pass  # Fall back to simple method
        
        # Always also use simple pattern matching
        # Extract numbers and percentages
        numbers = re.findall(r'\d+\.?\d*\s*(?:%|million|billion|thousand)?', text)
        entities.extend(numbers[:3])
        
        # Extract capitalized words (likely proper nouns)
        words = text.split()
        for word in words:
            clean_word = word.strip('.,!?";:')
            if (clean_word.istitle() and len(clean_word) > 2 and 
                clean_word not in ['The', 'A', 'An', 'This', 'That', 'And', 'But']):
                entities.append(clean_word)
        
        # Remove duplicates and return top 5
        return list(set(entities))[:5]
    
    def _assess_urgency(self, text: str) -> int:
        """
        Assess urgency using sentiment analysis and keywords.
        
        Returns urgency score from 1-10.
        """
        base_urgency = 3
        
        # Use sentiment analysis if available
        if NLP_AVAILABLE:
            try:
                blob = TextBlob(text)
                sentiment = blob.sentiment
                
                # Negative sentiment often indicates urgent/serious news
                if sentiment.polarity < -0.3:
                    base_urgency += 2
                elif sentiment.polarity < -0.1:
                    base_urgency += 1
                
                # High subjectivity might indicate opinion vs fact
                if sentiment.subjectivity > 0.7:
                    base_urgency -= 1
            except:
                pass
        
        # Check for urgent keywords
        text_lower = text.lower()
        max_keyword_urgency = 0
        
        for keyword, urgency_score in self.urgency_keywords.items():
            if keyword in text_lower:
                max_keyword_urgency = max(max_keyword_urgency, urgency_score)
        
        # Combine base urgency with keyword urgency
        final_urgency = base_urgency + max_keyword_urgency
        return min(final_urgency, 10)  # Cap at 10
    
    async def prioritize_claims(self, claims: List[Claim]) -> List[Claim]:
        """
        Sort claims by priority for verification.
        
        Priority is based on urgency and verifiability scores.
        """
        def calculate_priority_score(claim: Claim) -> float:
            return (claim.urgency * 0.6) + (claim.verifiability * 0.4)
        
        prioritized_claims = sorted(claims, key=calculate_priority_score, reverse=True)
        
        logger.info(f"Prioritized {len(prioritized_claims)} claims")
        return prioritized_claims
