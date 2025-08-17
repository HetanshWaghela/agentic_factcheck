"""
Fact Verifier - Verifies claims against reliable sources.

This module checks claims against trusted sources and
provides verification results with confidence scores.
"""

import asyncio
import logging
from typing import List, Dict, Any
from datetime import datetime
from .config import Config
from .models import Claim, VerificationResult

logger = logging.getLogger(__name__)


class FactVerifier:
    """
    Verifies claims against reliable sources and provides verdicts.
    
    This class:
    1. Searches for evidence about claims
    2. Analyzes the evidence quality
    3. Provides verdicts with confidence scores
    """
    
    def __init__(self, config: Config = None):
        self.config = config or Config()
    
    async def verify_claims(self, claims: List[Claim]) -> List[Claim]:
        """
        Verify a list of claims and add verification results.
        
        Args:
            claims: List of claims to verify
            
        Returns:
            List of claims with verification results added
        """
        logger.info(f"Starting verification of {len(claims)} claims...")
        
        verified_claims = []
        
        for claim in claims:
            try:
                verification_result = await self.verify_single_claim(claim)
                claim.verification = verification_result.__dict__
                claim.verified_at = datetime.now()
                verified_claims.append(claim)
                
            except Exception as e:
                logger.error(f"Error verifying claim {claim.id}: {e}")
                # Add error verification result
                claim.verification = {
                    'verdict': 'error',
                    'confidence': 0.0,
                    'explanation': f"Verification failed: {str(e)}",
                    'key_evidence': [],
                    'context_needed': '',
                    'sources_used': []
                }
                claim.verified_at = datetime.now()
                verified_claims.append(claim)
        
        logger.info(f"Completed verification of {len(verified_claims)} claims")
        return verified_claims
    
    async def verify_single_claim(self, claim: Claim) -> VerificationResult:
        """
        Verify a single claim.
        
        For now, this is a simplified implementation.
        Later, you can enhance it with real web searches and AI analysis.
        """
        
        # Simple verification based on claim characteristics
        # In a real implementation, this would search the web and fact-check databases
        
        verdict, confidence, explanation = self._analyze_claim_simple(claim)
        
        return VerificationResult(
            verdict=verdict,
            confidence=confidence,
            explanation=explanation,
            key_evidence=self._get_dummy_evidence(claim),
            context_needed=self._assess_context_needs(claim),
            sources_used=self._get_dummy_sources(claim),
            evidence_quality_score=confidence,
            source_diversity_score=0.7
        )
    
    def _analyze_claim_simple(self, claim: Claim) -> tuple[str, float, str]:
        """
        Simple claim analysis based on patterns.
        
        This is a placeholder implementation. In reality, you'd:
        1. Search for evidence online
        2. Check fact-checking databases
        3. Use AI to analyze the evidence
        
        Returns:
            (verdict, confidence, explanation)
        """
        claim_text = claim.claim_text.lower()
        
        # Look for suspicious patterns
        suspicious_patterns = [
            'doctors hate this', 'secret that', 'they don\'t want you to know',
            'miracle cure', 'shocking truth', 'big pharma', 'conspiracy'
        ]
        
        if any(pattern in claim_text for pattern in suspicious_patterns):
            return 'false', 0.8, 'Claim contains common misinformation patterns'
        
        # Look for overly dramatic language
        dramatic_words = ['shocking', 'devastating', 'incredible', 'unbelievable', 'amazing']
        dramatic_count = sum(1 for word in dramatic_words if word in claim_text)
        
        if dramatic_count >= 2:
            return 'misleading', 0.6, 'Claim uses overly dramatic language that may be misleading'
        
        # Check for statistical claims without sources
        if claim.claim_type == 'statistic':
            if 'study' not in claim_text and 'research' not in claim_text:
                return 'needs_context', 0.5, 'Statistical claim lacks source information'
        
        # Check for very recent events (harder to verify)
        hours_since_published = (datetime.now() - claim.source_item.published_at).total_seconds() / 3600
        if hours_since_published < 2:
            return 'unverifiable', 0.3, 'Claim is too recent to verify with confidence'
        
        # Default: assume true but with low confidence for demo
        if claim.claim_type == 'policy':
            return 'true', 0.7, 'Policy claims from reliable sources are generally accurate'
        elif claim.claim_type == 'event':
            return 'true', 0.6, 'Event reported by multiple sources'
        else:
            return 'needs_context', 0.4, 'Claim requires additional context for full understanding'
    
    def _get_dummy_evidence(self, claim: Claim) -> List[str]:
        """
        Get dummy evidence for demonstration.
        
        In a real implementation, this would be actual evidence found during verification.
        """
        return [
            f"Evidence point 1 for {claim.claim_type} claim",
            f"Evidence point 2 from {claim.source_item.source}",
            "Cross-reference with additional sources"
        ]
    
    def _assess_context_needs(self, claim: Claim) -> str:
        """
        Assess what additional context might be needed.
        """
        context_templates = {
            'statistic': 'This statistic may need background information about methodology and sample size.',
            'event': 'Additional context about the circumstances and verification from multiple sources may be helpful.',
            'policy': 'Context about the policy\'s implications and implementation timeline would be valuable.',
        }
        
        return context_templates.get(claim.claim_type, 'Additional context may help with understanding.')
    
    def _get_dummy_sources(self, claim: Claim) -> List[str]:
        """
        Get dummy sources for demonstration.
        
        In a real implementation, these would be actual sources consulted.
        """
        base_sources = ['reuters.com', 'apnews.com', 'bbc.com']
        
        if claim.claim_type == 'policy':
            base_sources.extend(['government website', 'official statement'])
        elif claim.claim_type == 'statistic':
            base_sources.extend(['research database', 'academic source'])
        
        return base_sources[:3]  # Return first 3 sources
    
    def get_verification_summary(self, verified_claims: List[Claim]) -> Dict[str, Any]:
        """
        Generate a summary of verification results.
        
        Args:
            verified_claims: List of verified claims
            
        Returns:
            Summary statistics about verification results
        """
        total_claims = len(verified_claims)
        if total_claims == 0:
            return {'total_claims': 0}
        
        verdict_counts = {}
        confidence_scores = []
        
        for claim in verified_claims:
            if claim.verification:
                verdict = claim.verification.get('verdict', 'unknown')
                confidence = claim.verification.get('confidence', 0.0)
                
                verdict_counts[verdict] = verdict_counts.get(verdict, 0) + 1
                confidence_scores.append(confidence)
        
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        return {
            'total_claims': total_claims,
            'verdict_breakdown': verdict_counts,
            'average_confidence': round(avg_confidence, 2),
            'false_or_misleading_count': verdict_counts.get('false', 0) + verdict_counts.get('misleading', 0),
            'high_confidence_claims': len([c for c in confidence_scores if c > 0.7])
        }
