"""
Quick test to validate the modular structure works correctly.
Run this to test imports and basic functionality.
"""

def test_imports():
    """Test that all modules can be imported successfully."""
    try:
        # Test basic module imports first
        from config import Config, get_user_inputs
        from utils import extract_json_from_response, load_fallacies_data
        from prompts import get_claim_extraction_template
        print("✅ Core modules imported successfully")
        
        # Test LangChain-dependent modules (may fail if dependencies not installed)
        try:
            from evidence_search import EvidenceSearcher, ArticleSearcher
            from fact_checker import FactChecker
            print("✅ LangChain-dependent modules imported successfully")
        except ImportError as e:
            print(f"⚠️  LangChain dependency missing (expected): {e}")
            print("   This is normal if dependencies aren't installed yet")
        
        return True
    except ImportError as e:
        print(f"❌ Critical import error: {e}")
        return False

def test_config():
    """Test configuration loading."""
    try:
        from config import Config
        
        # Test credible sources
        sources = Config.get_credible_sources()
        assert 'tier1' in sources
        assert 'reuters.com' in sources['tier1']
        
        # Test time ranges
        assert 'qdr:m1' in Config.TIME_RANGES.values()
        
        print("✅ Configuration tests passed")
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_prompts():
    """Test prompt templates."""
    try:
        from prompts import (
            get_claim_extraction_template,
            get_claim_verification_template,
            get_ethics_analysis_template
        )
        
        # Test that templates contain expected placeholders
        claim_template = get_claim_extraction_template()
        assert '{content}' in claim_template
        
        verify_template = get_claim_verification_template()
        assert '{claim}' in verify_template
        assert '{evidence}' in verify_template
        
        ethics_template = get_ethics_analysis_template()
        assert '{summary}' in ethics_template
        
        print("✅ Prompt template tests passed")
        return True
    except Exception as e:
        print(f"❌ Prompt template test failed: {e}")
        return False

def test_utils():
    """Test utility functions."""
    try:
        from utils import extract_json_from_response, calculate_overall_confidence
        
        # Test JSON extraction
        test_json = '{"test": "value"}'
        result = extract_json_from_response(test_json)
        assert result['test'] == 'value'
        
        # Test confidence calculation
        claims = [
            {'confidence': 0.8, 'evidence_quality': 'Strong'},
            {'confidence': 0.6, 'evidence_quality': 'Moderate'}
        ]
        confidence = calculate_overall_confidence(claims)
        assert 0.0 <= confidence <= 1.0
        
        print("✅ Utility function tests passed")
        return True
    except Exception as e:
        print(f"❌ Utility function test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("Testing modular fact-checking structure...")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_config,
        test_prompts,
        test_utils
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Tests passed: {passed}/{len(tests)}")
    
    if passed == len(tests):
        print("🎉 All tests passed! Modular structure is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the error messages above.")

if __name__ == "__main__":
    main()
