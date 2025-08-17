"""
Data models for the fact-checking system.
These classes define the structure of data as it flows through the pipeline.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class ContentItem:
    """
    Represents a piece of content from any source (news, social media, etc.)
    
    This is the basic unit of information that flows through our system.
    """
    title: str
    content: str
    source: str
    url: str
    published_at: datetime
    source_type: str  # 'news_api', 'rss', 'social_media'
    
    # Optional fields added during processing
    crisis_relevance_score: float = 0.0
    detected_language: str = 'en'
    translated_content: Optional[Dict[str, str]] = None


@dataclass
class Claim:
    """
    Represents a factual claim extracted from content that can be verified.
    """
    id: str
    claim_text: str
    claim_type: str  # 'statistic', 'event', 'policy', 'medical', etc.
    entities: List[str]  # People, organizations mentioned
    urgency: int  # 1-10 scale
    verifiability: int  # 1-10 scale
    
    # Source information
    source_item: ContentItem
    detected_at: datetime
    
    # Verification results (added later)
    verification: Optional[Dict[str, Any]] = None
    verified_at: Optional[datetime] = None


@dataclass
class VerificationResult:
    """
    Results of fact-checking a claim.
    """
    verdict: str  # 'true', 'false', 'misleading', 'needs_context', 'unverifiable'
    confidence: float  # 0.0 to 1.0
    explanation: str
    key_evidence: List[str]
    context_needed: str
    sources_used: List[str]
    
    # Quality metrics
    evidence_quality_score: float = 0.0
    source_diversity_score: float = 0.0


@dataclass
class TrendAnalysis:
    """
    Analysis of misinformation trends and patterns.
    """
    timestamp: datetime
    emerging_topics: List[Dict[str, Any]]
    false_claim_patterns: Dict[str, Any]
    source_reliability: Dict[str, Any]
    urgency_assessment: Dict[str, Any]
    
    # Recommendations
    recommended_actions: List[str]


class ProcessingStatus:
    """
    Tracks the status of content as it moves through the pipeline.
    """
    
    # Processing stages
    RECEIVED = "received"
    CLAIM_DETECTION = "claim_detection"
    VERIFICATION = "verification"
    TREND_ANALYSIS = "trend_analysis"
    EXPLANATION_GENERATION = "explanation_generation"
    COMPLETED = "completed"
    ERROR = "error"
    
    def __init__(self):
        self.current_stage = self.RECEIVED
        self.errors = []
        self.timestamps = {self.RECEIVED: datetime.now()}

    def advance_to(self, stage: str, error: str):
        """Move to the next processing stage."""
        if error:
            self.current_stage = self.ERROR
            self.errors.append(error)
        else:
            self.current_stage = stage
        
        self.timestamps[stage] = datetime.now()
    
    def get_processing_time(self) -> float:
        """Get total processing time in seconds."""
        if self.COMPLETED in self.timestamps or self.ERROR in self.timestamps:
            end_stage = self.COMPLETED if self.COMPLETED in self.timestamps else self.ERROR
            start_time = self.timestamps[self.RECEIVED]
            end_time = self.timestamps[end_stage]
            return (end_time - start_time).total_seconds()
        return 0.0
    
    def is_complete(self) -> bool:
        """Check if processing is complete."""
        return self.current_stage in [self.COMPLETED, self.ERROR]
