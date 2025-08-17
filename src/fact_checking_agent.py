"""
Main Fact-Checking Agent

This is the central orchestrator that coordinates all components
of the fact-checking system.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from .config import Config
from .content_scanner import ContentScanner
from .claim_detector import ClaimDetector
from .fact_verifier import FactVerifier
from .models import ContentItem, Claim

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FactCheckingAgent:
    """
    Main fact-checking agent that orchestrates the entire pipeline.
    
    This agent:
    1. Scans content from multiple sources
    2. Detects factual claims
    3. Verifies claims against reliable sources
    4. Generates reports and explanations
    """
    
    def __init__(self, config: Config = None):
        """Initialize the fact-checking agent."""
        self.config = config or Config()
        
        # Initialize components
        self.content_scanner = ContentScanner(self.config)
        self.claim_detector = ClaimDetector(self.config)
        self.fact_verifier = FactVerifier(self.config)
        
        # Ensure output directory exists
        Path('output').mkdir(exist_ok=True)
        
        logger.info("Fact-checking agent initialized")
        logger.info(f"Configuration: {self.config.get_summary()}")
    
    async def run_fact_check_cycle(self) -> Dict[str, Any]:
        """
        Run a complete fact-checking cycle.
        
        Returns:
            Dictionary containing results of the fact-checking cycle
        """
        cycle_start_time = datetime.now()
        logger.info("=== Starting Fact-Check Cycle ===")
        
        try:
            # Step 1: Scan content from various sources
            logger.info("Step 1: Scanning content sources...")
            content_items = await self.content_scanner.scan_all_sources()
            
            if not content_items:
                logger.warning("No content found during scanning")
                return self._create_empty_results(cycle_start_time)
            
            # Step 2: Extract claims from content
            logger.info("Step 2: Extracting factual claims...")
            claims = await self.claim_detector.extract_claims_from_content(content_items)
            
            if not claims:
                logger.warning("No claims detected in content")
                return self._create_results_with_content_only(content_items, cycle_start_time)
            
            # Step 3: Prioritize claims for verification
            logger.info("Step 3: Prioritizing claims...")
            prioritized_claims = await self.claim_detector.prioritize_claims(claims)
            
            # Step 4: Verify claims
            logger.info("Step 4: Verifying claims...")
            verified_claims = await self.fact_verifier.verify_claims(prioritized_claims)
            
            # Step 5: Generate results and save
            logger.info("Step 5: Generating results...")
            results = await self._generate_results(
                content_items, verified_claims, cycle_start_time
            )
            
            # Step 6: Save results
            await self._save_results(results)
            
            logger.info("=== Fact-Check Cycle Complete ===")
            return results
            
        except Exception as e:
            logger.error(f"Error in fact-check cycle: {e}")
            return self._create_error_results(cycle_start_time, str(e))
    
    async def _generate_results(self, content_items: List[ContentItem], 
                               verified_claims: List[Claim], 
                               cycle_start_time: datetime) -> Dict[str, Any]:
        """Generate comprehensive results from the fact-checking cycle."""
        
        cycle_end_time = datetime.now()
        processing_time = (cycle_end_time - cycle_start_time).total_seconds()
        
        # Get verification summary
        verification_summary = self.fact_verifier.get_verification_summary(verified_claims)
        
        # Analyze false/misleading claims
        false_misleading_claims = [
            claim for claim in verified_claims
            if claim.verification and claim.verification.get('verdict') in ['false', 'misleading']
        ]
        
        # Generate alerts for high-urgency false claims
        urgent_false_claims = [
            claim for claim in false_misleading_claims
            if claim.urgency >= 7
        ]
        
        results = {
            'cycle_info': {
                'start_time': cycle_start_time.isoformat(),
                'end_time': cycle_end_time.isoformat(),
                'processing_time_seconds': round(processing_time, 2)
            },
            'content_summary': {
                'total_content_items': len(content_items),
                'content_sources': list(set(item.source for item in content_items)),
                'content_types': list(set(item.source_type for item in content_items)),
                'avg_relevance_score': round(
                    sum(item.crisis_relevance_score for item in content_items) / len(content_items), 2
                ) if content_items else 0
            },
            'claims_analysis': {
                'total_claims': len(verified_claims),
                'claims_by_type': self._count_claims_by_type(verified_claims),
                'avg_urgency': round(
                    sum(claim.urgency for claim in verified_claims) / len(verified_claims), 1
                ) if verified_claims else 0,
                'avg_verifiability': round(
                    sum(claim.verifiability for claim in verified_claims) / len(verified_claims), 1
                ) if verified_claims else 0
            },
            'verification_results': verification_summary,
            'alerts': {
                'urgent_false_claims': len(urgent_false_claims),
                'total_false_misleading': len(false_misleading_claims),
                'requires_immediate_attention': len(urgent_false_claims) > 0
            },
            'detailed_claims': [self._serialize_claim(claim) for claim in verified_claims],
            'recommendations': self._generate_recommendations(verified_claims)
        }
        
        return results
    
    def _count_claims_by_type(self, claims: List[Claim]) -> Dict[str, int]:
        """Count claims by their type."""
        type_counts = {}
        for claim in claims:
            claim_type = claim.claim_type
            type_counts[claim_type] = type_counts.get(claim_type, 0) + 1
        return type_counts
    
    def _serialize_claim(self, claim: Claim) -> Dict[str, Any]:
        """Convert a Claim object to a dictionary for JSON serialization."""
        return {
            'id': claim.id,
            'claim_text': claim.claim_text,
            'claim_type': claim.claim_type,
            'entities': claim.entities,
            'urgency': claim.urgency,
            'verifiability': claim.verifiability,
            'source_info': {
                'source': claim.source_item.source,
                'title': claim.source_item.title,
                'url': claim.source_item.url,
                'published_at': claim.source_item.published_at.isoformat()
            },
            'verification': claim.verification,
            'detected_at': claim.detected_at.isoformat(),
            'verified_at': claim.verified_at.isoformat() if claim.verified_at else None
        }
    
    def _generate_recommendations(self, verified_claims: List[Claim]) -> List[str]:
        """Generate actionable recommendations based on results."""
        recommendations = []
        
        false_claims = [c for c in verified_claims 
                       if c.verification and c.verification.get('verdict') == 'false']
        misleading_claims = [c for c in verified_claims 
                           if c.verification and c.verification.get('verdict') == 'misleading']
        
        if len(false_claims) > 3:
            recommendations.append("High number of false claims detected - increase monitoring frequency")
        
        if len(misleading_claims) > 5:
            recommendations.append("Many misleading claims found - consider issuing clarifications")
        
        urgent_claims = [c for c in verified_claims if c.urgency >= 8]
        if urgent_claims:
            recommendations.append("Urgent claims detected - consider immediate response")
        
        if not recommendations:
            recommendations.append("Continue regular monitoring - situation appears stable")
        
        return recommendations
    
    def _create_empty_results(self, start_time: datetime) -> Dict[str, Any]:
        """Create results structure when no content is found."""
        return {
            'cycle_info': {
                'start_time': start_time.isoformat(),
                'end_time': datetime.now().isoformat(),
                'processing_time_seconds': 0
            },
            'content_summary': {'total_content_items': 0},
            'claims_analysis': {'total_claims': 0},
            'verification_results': {'total_claims': 0},
            'alerts': {'requires_immediate_attention': False},
            'detailed_claims': [],
            'recommendations': ['No content found - check content sources configuration']
        }
    
    def _create_results_with_content_only(self, content_items: List[ContentItem], 
                                         start_time: datetime) -> Dict[str, Any]:
        """Create results when content is found but no claims detected."""
        return {
            'cycle_info': {
                'start_time': start_time.isoformat(),
                'end_time': datetime.now().isoformat(),
                'processing_time_seconds': (datetime.now() - start_time).total_seconds()
            },
            'content_summary': {
                'total_content_items': len(content_items),
                'content_sources': list(set(item.source for item in content_items))
            },
            'claims_analysis': {'total_claims': 0},
            'verification_results': {'total_claims': 0},
            'alerts': {'requires_immediate_attention': False},
            'detailed_claims': [],
            'recommendations': ['Content found but no verifiable claims detected - adjust claim detection parameters']
        }
    
    def _create_error_results(self, start_time: datetime, error_message: str) -> Dict[str, Any]:
        """Create results structure when an error occurs."""
        return {
            'cycle_info': {
                'start_time': start_time.isoformat(),
                'end_time': datetime.now().isoformat(),
                'error': error_message
            },
            'content_summary': {'total_content_items': 0},
            'claims_analysis': {'total_claims': 0},
            'verification_results': {'total_claims': 0},
            'alerts': {'requires_immediate_attention': True, 'error': True},
            'detailed_claims': [],
            'recommendations': [f'System error occurred: {error_message}']
        }
    
    async def _save_results(self, results: Dict[str, Any]) -> None:
        """Save results to a JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"output/fact_check_results_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Results saved to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")
    
    async def run_continuous_monitoring(self, interval_minutes: int = None) -> None:
        """
        Run continuous monitoring with specified interval.
        
        Args:
            interval_minutes: Minutes between cycles (uses config default if None)
        """
        interval = interval_minutes or self.config.SCAN_INTERVAL_MINUTES
        logger.info(f"Starting continuous monitoring (interval: {interval} minutes)")
        
        try:
            while True:
                # Run a fact-checking cycle
                await self.run_fact_check_cycle()
                
                # Wait for the specified interval
                logger.info(f"Waiting {interval} minutes until next cycle...")
                await asyncio.sleep(interval * 60)
                
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
        except Exception as e:
            logger.error(f"Error in continuous monitoring: {e}")
    
    def validate_setup(self) -> bool:
        """
        Validate that the system is properly configured.
        
        Returns:
            True if setup is valid, False otherwise
        """
        issues = self.config.validate_config()
        
        if issues:
            logger.warning("Configuration issues found:")
            for issue in issues:
                logger.warning(f"  - {issue}")
            return False
        
        logger.info("System configuration validated successfully")
        return True
