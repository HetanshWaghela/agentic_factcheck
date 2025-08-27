"""
Utility functions for the fact-checking system.
Contains helpers for JSON parsing, formatting, and data processing.
"""

import json
import re

def extract_json_from_response(response_text):
    """
    Extract JSON from LLM response text.
    Handles various JSON formatting issues from LLM outputs.
    """
    try:
        return json.loads(response_text.strip())
    except json.JSONDecodeError:
        pass
    
    # Try to find JSON in code blocks
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
    
    # Try to find any JSON-like structure
    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass
    
    # Return error structure if parsing fails
    return {
        "summary": "JSON parsing failed - raw response included below",
        "claims": [],
        "red_flags": ["Failed to parse LLM response as JSON"],
        "confidence": 0.0,
        "raw_response": response_text
    }

def format_evidence_for_llm(evidence_list):
    """
    Format evidence list for LLM consumption.
    Creates readable evidence summary from search results.
    """
    if not evidence_list:
        return "No external evidence found."
    
    formatted = "EXTERNAL EVIDENCE (FULL ARTICLES):\n\n"
    for i, evidence in enumerate(evidence_list, 1):
        formatted += f"Source {i} (Credibility: {evidence['credibility_score']}/3):\n"
        formatted += f"Title: {evidence['title']}\n"
        
        content = evidence.get('full_content', evidence.get('snippet', 'No content available'))
        formatted += f"Content: {content}\n"
        
        formatted += f"Source: {evidence['source']} ({evidence['date']})\n"
        formatted += f"URL: {evidence['url']}\n"
        formatted += f"Found via: {evidence['search_query']}\n\n"
    
    return formatted

def calculate_overall_confidence(verified_claims):
    """
    Calculate overall confidence score from individual claim confidences.
    Weights confidence by evidence quality.
    """
    if not verified_claims:
        return 0.0
    
    confidences = []
    for claim in verified_claims:
        claim_confidence = claim.get('confidence', 0.0)
        evidence_quality = claim.get('evidence_quality', 'Insufficient')
        
        quality_multiplier = {
            'Strong': 1.0,
            'Moderate': 0.8,
            'Weak': 0.6,
            'Insufficient': 0.3
        }
        
        adjusted_confidence = claim_confidence * quality_multiplier.get(evidence_quality, 0.3)
        confidences.append(adjusted_confidence)
    
    return sum(confidences) / len(confidences)

def display_verification_results(result):
    """Display formatted verification results to console."""
    print("=" * 80)
    print("FACT-CHECKING REPORT (WITH EXTERNAL VERIFICATION)")
    print("=" * 80)
    print(f"Article: {result['title']}")
    print(f"🔗 URL: {result['url']}")
    print("=" * 80)
    
    print("\n📄 SUMMARY:")
    print("-" * 40)
    print(result['summary'])
    
    overall_confidence = calculate_overall_confidence(result['verified_claims'])
    print(f"\n📊 OVERALL CONFIDENCE SCORE: {overall_confidence:.2f}")
    
    print("\n🔍 VERIFIED CLAIMS ANALYSIS:")
    print("-" * 40)
    
    for i, claim in enumerate(result['verified_claims'], 1):
        print(f"\n{i}. CLAIM: {claim.get('claim', 'N/A')}")
        print(f"   VERDICT: {claim.get('verdict', 'N/A')}")
        print(f"   CONFIDENCE: {claim.get('confidence', 'N/A')}")
        print(f"   EVIDENCE QUALITY: {claim.get('evidence_quality', 'N/A')}")
        print(f"   SOURCE CONSENSUS: {claim.get('source_consensus', 'N/A')}")
        
        reasoning = claim.get('reasoning', '')
        if reasoning:
            print(f"   REASONING: {reasoning}")
        
        fallacies = claim.get('fallacies', [])
        if fallacies and fallacies != ['None found']:
            print(f"   FALLACIES: {', '.join(fallacies)}")
    
    print("\n🎓 ETHICS PROFESSOR REVIEW:")
    print("-" * 40)
    print(result['analysis'])
    print("\n" + "=" * 80)

def load_fallacies_data(filepath="fallacies.csv"):
    """Load fallacies data from CSV file."""
    import pandas as pd
    
    try:
        fallacies_df = pd.read_csv(filepath)
        fallacies_list = "\n".join(
            f"{row['fine_class']}: {row['definition']}" for _, row in fallacies_df.iterrows()
        )
        return fallacies_list
    except Exception as e:
        print(f"Warning: Could not load fallacies from {filepath}: {e}")
        return "No fallacies data available"
