"""
Simple test script to verify the system components work correctly.

Run this script to test individual components without running the full pipeline.
"""

import sys
from pathlib import Path
import asyncio

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent / 'src'))

from src.config import Config
from src.models import ContentItem
from src.content_scanner import ContentScanner
from src.claim_detector import ClaimDetector
from src.fact_verifier import FactVerifier
from datetime import datetime


async def test_components():
    """Test each component individually."""
    
    print("🧪 Testing Fact-Check System Components")
    print("=" * 50)
    
    # Test 1: Configuration
    print("1. Testing Configuration...")
    config = Config()
    summary = config.get_summary()
    print(f"   ✅ Config loaded: {summary['crisis_keywords_count']} keywords, {summary['news_sources_count']} sources")
    
    # Test 2: Content Scanner (without API calls)
    print("\n2. Testing Content Scanner...")
    scanner = ContentScanner(config)
    # Create dummy content for testing
    dummy_content = [
        ContentItem(
            title="Breaking: New COVID variant detected",
            content="Scientists have reported a new COVID-19 variant with increased transmissibility.",
            source="Test News",
            url="https://example.com",
            published_at=datetime.now(),
            source_type="test"
        ),
        ContentItem(
            title="Economic news update",
            content="Stock markets showed mixed results today.",
            source="Business News",
            url="https://example.com",
            published_at=datetime.now(),
            source_type="test"
        )
    ]
    
    # Test crisis relevance scoring
    filtered_content = scanner._filter_crisis_content(dummy_content)
    print(f"   ✅ Filtered {len(filtered_content)} crisis-relevant items from {len(dummy_content)} total")
    
    # Test 3: Claim Detector
    print("\n3. Testing Claim Detector...")
    detector = ClaimDetector(config)
    
    if filtered_content:
        claims = await detector.extract_claims_from_content(filtered_content)
        print(f"   ✅ Extracted {len(claims)} claims")
        
        if claims:
            # Show first claim details
            first_claim = claims[0]
            print(f"   📝 Sample claim: '{first_claim.claim_text[:50]}...'")
            print(f"   🏷️  Type: {first_claim.claim_type}, Urgency: {first_claim.urgency}")
    else:
        print("   ⚠️  No crisis-relevant content to test claim detection")
    
    # Test 4: Fact Verifier
    print("\n4. Testing Fact Verifier...")
    verifier = FactVerifier(config)
    
    if 'claims' in locals() and claims:
        verified_claims = await verifier.verify_claims(claims[:1])  # Test with first claim only
        print(f"   ✅ Verified {len(verified_claims)} claims")
        
        if verified_claims and verified_claims[0].verification:
            verification = verified_claims[0].verification
            print(f"   📊 Sample verdict: {verification['verdict']} (confidence: {verification['confidence']:.2f})")
    else:
        print("   ⚠️  No claims available to test verification")
    
    print("\n" + "=" * 50)
    print("✅ Component testing completed!")
    print("\nNext steps:")
    print("1. Set up your API keys in .env file")
    print("2. Run 'python main.py' to start the full system")
    print("3. Choose option 1 for a single fact-check cycle")


async def test_configuration_validation():
    """Test configuration validation."""
    print("\n🔧 Testing Configuration Validation...")
    
    config = Config()
    issues = config.validate_config()
    
    if issues:
        print("   ⚠️  Configuration issues found:")
        for issue in issues:
            print(f"      - {issue}")
        print("\n   💡 These are expected if you haven't set up API keys yet.")
    else:
        print("   ✅ All configuration validated successfully!")


def main():
    """Main test function."""
    try:
        # Run async tests
        asyncio.run(test_components())
        
        # Run sync tests
        asyncio.run(test_configuration_validation())
        
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        print("This might be due to missing dependencies or configuration issues.")


if __name__ == "__main__":
    main()
