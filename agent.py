from dotenv import load_dotenv
import os
import pandas as pd
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")
serper_api_key = os.getenv("SERPER_API_KEY")
gemini_api_key = os.getenv("GEMINI_API_KEY")
os.environ["USER_AGENT"] = "factcheck/1.0"
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_google_genai import ChatGoogleGenerativeAI
import json
from pprint import pprint
import asyncio
import aiohttp
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import warnings
warnings.filterwarnings('ignore')
fallacies_df= pd.read_csv("fallacies.csv")
fallacies_list = "\n".join(
    f"{row['fine_class']}: {row['definition']}" for _, row in fallacies_df.iterrows()
)
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0, max_output_tokens=1024, google_api_key=gemini_api_key)
template1 = """
You are a neutral fact-checking communications analyst. Your tasks are:
(1) Summarize the article in five clear sentences (neutral, specific, no hype).
(2) Extract and verify check-worthy claims.
(3) Flag logical fallacies from the provided list.

Rules:
- Do not speculate or make things up.
- Cite reputable, independent sources with short quotes and URLs.
- If evidence is insufficient or conflicting, mark the claim as "Unverifiable" or "Needs context".
- Use the provided fallacies list only; if none apply, say "None found".
- Show only final answers. No hidden reasoning.

Article to analyze:
{content}

Fallacy reference list:
{fallacies_list}

## Tasks
1. **Summary**: Five-sentence neutral summary.
2. **Claim extraction**: List 5–10 key factual claims.
3. **Verification**: For each claim, give a verdict: True | False | Misleading | Needs context | Unverifiable.
   - Provide 1–3 short supporting/contradicting quotes with URLs and source dates.
   - Note if event dates match or conflict.
4. **Fallacies**: List matching fallacies (by name) for each claim.
5. **Red flags**: Note sensational language, anonymous sourcing, or inconsistencies (if any).
6. **Confidence**: Provide an overall confidence score between 0 and 1.

IMPORTANT: Respond ONLY with valid JSON. No additional text before or after. Use this exact structure:

{{
  "summary": "Five sentences summary here...",
  "claims": [
    {{
      "claim": "Specific claim text",
      "verdict": "True|False|Misleading|Needs context|Unverifiable",
      "evidence": [
        {{"quote": "Short quote", "url": "https://example.com", "source": "Source name", "published_date": "YYYY-MM-DD", "matches_event_date": true}}
      ],
      "fallacies": ["Fallacy name or None found"],
      "notes": "Brief notes if needed"
    }}
  ],
  "red_flags": ["Flag 1", "Flag 2"],
  "confidence": 0.8
}}
""" 
chain1 = LLMChain(
    llm=llm,
    prompt=PromptTemplate(
        template=template1,
        input_variables=["content", "fallacies_list"] 
    )
)
template2 = """You are an ethics professor reviewing a news article SUMMARY. Be succinct and easy to read, but ground your critique in core ethics principles (fairness, non-maleficence, duty of care, transparency). Use ONLY the fallacy names/definitions provided below. If no fallacy applies, say "None found" and explain why.

Article summary: {summary}

Fallacies to consider:
{fallacies_list}

Provide EXACTLY:
1) Most impactful fallacy: <name from list or "None found">
2) Why this could mislead readers: <1–3 sentences, plain language>
3) Counterfactual/counterpoint: <one plausible alternative interpretation for why this fallacy (or appearance of it) might be present>

Constraints:
- Do not invent facts beyond the summary and fallacy list.
- No step-by-step reasoning; show final answers only.
- Keep the total response under 120 words.

Professor:"""
chain2= LLMChain(
    llm=llm,
    prompt=PromptTemplate(
        template=template2,
        input_variables=["summary","fallacies_list"]
    )
)
search = GoogleSerperAPIWrapper(
    type="news",
    tbs="qdr:m1",  
    serper_api_key=serper_api_key
)

template_extract_claims = """
You are a neutral fact-checking analyst. Extract key factual claims from this article.

Article to analyze:
{content}

IMPORTANT: Respond ONLY with valid JSON. Extract 5-10 specific, verifiable factual claims.

{{
  "summary": "Five sentences neutral summary here...",
  "claims": [
    {{
      "claim": "Specific factual claim text",
      "claim_type": "statistical|event|quote|policy|prediction",
      "key_entities": ["entity1", "entity2"],
      "search_terms": ["term1", "term2", "term3"]
    }}
  ]
}}
"""

template_verify_claims = """
You are a neutral fact-checking analyst. Verify the given claim using the provided external evidence.

INSTRUCTIONS:
- Mark as 'True' if credible evidence supports the claim
- Mark as 'False' if credible evidence contradicts the claim  
- Mark as 'Misleading' if the claim is partially true but lacks important context
- Mark as 'Needs context' if evidence conflicts or is mixed
- Mark as 'Unverifiable' ONLY if no relevant evidence is found

Original Claim: {claim}

External Evidence Found:
{evidence}

Fallacy reference list:
{fallacies_list}

Evidence Quality Guidelines:
- Strong: Multiple credible sources agree
- Moderate: Some credible sources support, or single high-quality source
- Weak: Limited sources or lower credibility sources
- Insufficient: No relevant evidence found

Be thorough but reasonable - don't require absolute certainty for basic factual claims that have reasonable evidence support.

IMPORTANT: Respond ONLY with valid JSON:

{{
  "claim": "{claim}",
  "verdict": "True|False|Misleading|Needs context|Unverifiable",
  "reasoning": "Brief explanation of verdict based on evidence",
  "evidence_quality": "Strong|Moderate|Weak|Insufficient",
  "source_consensus": "High|Medium|Low|Conflicting",
  "fallacies": ["Fallacy name or None found"],
  "confidence": 0.0
}}
"""

chain_extract = LLMChain(
    llm=llm,
    prompt=PromptTemplate(
        template=template_extract_claims,
        input_variables=["content"]
    )
)

chain_verify = LLMChain(
    llm=llm,
    prompt=PromptTemplate(
        template=template_verify_claims,
        input_variables=["claim", "evidence", "fallacies_list"]
    )
)

def search_for_evidence_thread(claim_info, sources_per_claim):
    claim_text = claim_info['claim']
    search_terms = claim_info.get('search_terms', [claim_text])
    
    time.sleep(0.5)
    return search_for_evidence(claim_text, search_terms, sources_per_claim)

def verify_claim_thread(claim_info, evidence, fallacies_list):
    claim_text = claim_info['claim']
    evidence_formatted = format_evidence_for_llm(evidence)
    
    time.sleep(0.3)
    
    verification_response = chain_verify.invoke({
        "claim": claim_text,
        "evidence": evidence_formatted,
        "fallacies_list": fallacies_list
    })["text"]
    
    return extract_json_from_response(verification_response)

def get_user_inputs():
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
    if time_range not in ['h', 'd', 'w', 'm', 'y']:
        time_range = 'm'
    
    time_map = {'h': 'qdr:h', 'd': 'qdr:d', 'w': 'qdr:w', 'm': 'qdr:m1', 'y': 'qdr:y'}
    
    try:
        max_chars = int(input("Enter max characters to analyze (default: 3000): ").strip() or "3000")
        if max_chars <= 0:
            max_chars = 3000
    except ValueError:
        max_chars = 3000
        print(f"Invalid input, using default: {max_chars}")
    
    try:
        num_articles = int(input("Enter number of articles to analyze (default: 1): ").strip() or "1")
        if num_articles <= 0:
            num_articles = 1
    except ValueError:
        num_articles = 1
        print(f"Invalid input, using default: {num_articles}")
    
    print("\nVerification depth:")
    print("- quick: 5 sources per claim (faster)")
    print("- thorough: 8 sources per claim (more accurate)")
    depth = input("Enter verification depth [quick/thorough] (default: quick): ").strip().lower()
    if depth not in ['quick', 'thorough']:
        depth = 'quick'
    
    sources_per_claim = 5 if depth == 'quick' else 8
    
    return {
        'search_topic': search_topic,
        'site': site,
        'time_range': time_map[time_range],
        'max_chars': max_chars,
        'num_articles': num_articles,
        'sources_per_claim': sources_per_claim
    }

def get_credible_sources():
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

def search_articles(config):
    search = GoogleSerperAPIWrapper(
        type="news",
        tbs=config['time_range'],
        serper_api_key=serper_api_key
    )
    
    if config['site'] == 'any':
        search_query = config['search_topic']
    else:
        search_query = f"site:{config['site']} {config['search_topic']}"
    
    print(f"\nSearching for: {search_query}")
    search_results = search.results(search_query)
    
    if not search_results.get('news'):
        print("No articles found. Please try different search terms.")
        return None
    
    return search_results

def select_articles(search_results, num_articles):
    news_articles = search_results['news']
    available_articles = min(len(news_articles), 10)
    
    print(f"\n Found {len(news_articles)} articles. Showing top {available_articles}:")
    print("-" * 60)
    
    for i in range(available_articles):
        article = news_articles[i]
        print(f"{i+1}. {article['title']}")
        print(f"   Source: {article.get('source', 'Unknown')}")
        print(f"   Date: {article.get('date', 'Unknown')}")
        print()
    
    if num_articles == 1:
        try:
            choice = int(input(f"Select article number (1-{available_articles}): ").strip())
            if 1 <= choice <= available_articles:
                return [news_articles[choice-1]]
            else:
                print("Invalid selection, using first article.")
                return [news_articles[0]]
        except ValueError:
            print("Invalid input, using first article.")
            return [news_articles[0]]
    else:
        selected_count = min(num_articles, available_articles)
        print(f"Analyzing first {selected_count} articles...")
        return news_articles[:selected_count]

def get_full_evidence_content(url, max_chars=1200):
    try:
        loader = WebBaseLoader(url)
        content = loader.load()[0].page_content
        cleaned_content = ' '.join(content.split())[:max_chars]
        return cleaned_content if cleaned_content else "Content could not be extracted"
    except Exception as e:
        return f"Error loading content: {str(e)}"

def search_for_evidence(claim, search_terms, sources_per_claim):
    evidence_search = GoogleSerperAPIWrapper(
        type="news",
        tbs="qdr:y",
        serper_api_key=serper_api_key
    )
    
    all_evidence = []
    credible_sources = get_credible_sources()
    
    search_queries = []
    
    fact_check_sites = ['factcheck.org', 'snopes.com', 'politifact.com']
    for site in fact_check_sites:
        search_queries.append(f"site:{site} {search_terms[0]}")
    
    news_sites = ['reuters.com', 'ap.org', 'bbc.com']
    for site in news_sites:
        search_queries.append(f"site:{site} {search_terms[0]}")
    
    search_queries.append(f'"{search_terms[0]}" fact check')
    search_queries.append(f'"{search_terms[0]}" verified OR confirmed')
    
    for term in search_terms[:2]:
        search_queries.append(f"{term} study OR research")
        search_queries.append(f"{term} report OR data")
    
    for term in search_terms[:2]:
        search_queries.append(f"{term} analysis")
        search_queries.append(f"{term} expert opinion")
    
    sources_found = 0
    for query in search_queries:
        if sources_found >= sources_per_claim:
            break
            
        try:
            results = evidence_search.results(query)
            if results.get('news'):
                for result in results['news'][:2]:
                    if sources_found >= sources_per_claim:
                        break
                    
                    source_url = result.get('link', '')
                    source_domain = source_url.split('/')[2] if '/' in source_url else ''
                    
                    credibility_score = 0
                    if any(domain in source_domain for domain in credible_sources['tier1']):
                        credibility_score = 3
                    elif any(domain in source_domain for domain in credible_sources['tier2']):
                        credibility_score = 2
                    elif any(domain in source_domain for domain in credible_sources['diverse_sources']):
                        credibility_score = 1
                    
                    if credibility_score > 0:
                        full_content = get_full_evidence_content(source_url, 1000)
                        
                        evidence_item = {
                            'title': result.get('title', ''),
                            'snippet': result.get('snippet', ''),
                            'full_content': full_content,
                            'url': source_url,
                            'source': result.get('source', ''),
                            'date': result.get('date', ''),
                            'credibility_score': credibility_score,
                            'search_query': query
                        }
                        all_evidence.append(evidence_item)
                        sources_found += 1
        except Exception as e:
            print(f"Search error for '{query}': {str(e)}")
            continue
    
    return all_evidence

def format_evidence_for_llm(evidence_list):
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

def analyze_article_with_verification(article, max_chars, sources_per_claim):
    article_url = article['link']
    article_title = article['title']
    
    print(f"\nLoading article: {article_title}")
    
    try:
        loader = WebBaseLoader(article_url)
        article_text = ' '.join(loader.load()[0].page_content[:max_chars].split())
        
        
        print("Step 1: Extracting claims...")
        claims_response = chain_extract.invoke({"content": article_text})["text"]
        claims_data = extract_json_from_response(claims_response)
        
        if not claims_data.get('claims'):
            return None
        
        print(f"Extracted {len(claims_data['claims'])} claims")
        
        print("\nStep 2: Verifying claims in parallel...")
        verified_claims = []
        
        batch_size = 3
        claims_list = claims_data['claims']
        
        for batch_start in range(0, len(claims_list), batch_size):
            batch_end = min(batch_start + batch_size, len(claims_list))
            batch_claims = claims_list[batch_start:batch_end]
            
            print(f"Processing batch {batch_start//batch_size + 1}: claims {batch_start+1}-{batch_end}")
            
            with ThreadPoolExecutor(max_workers=3) as executor:
                evidence_futures = {
                    executor.submit(search_for_evidence_thread, claim_info, sources_per_claim): i 
                    for i, claim_info in enumerate(batch_claims)
                }
                
                evidence_results = {}
                for future in as_completed(evidence_futures):
                    claim_index = evidence_futures[future]
                    try:
                        evidence = future.result()
                        evidence_results[claim_index] = evidence
                        print(f"   ✓ Evidence found for claim {batch_start + claim_index + 1}")
                    except Exception as e:
                        print(f"   ✗ Evidence search failed for claim {batch_start + claim_index + 1}: {str(e)}")
                        evidence_results[claim_index] = []
            
            with ThreadPoolExecutor(max_workers=3) as executor:
                verification_futures = {
                    executor.submit(
                        verify_claim_thread, 
                        batch_claims[i], 
                        evidence_results.get(i, []), 
                        fallacies_list
                    ): i 
                    for i in range(len(batch_claims))
                }
                
                batch_results = {}
                for future in as_completed(verification_futures):
                    claim_index = verification_futures[future]
                    try:
                        verification_data = future.result()
                        batch_results[claim_index] = verification_data
                        print(f"   ✓ Verification complete for claim {batch_start + claim_index + 1}")
                    except Exception as e:
                        print(f"   ✗ Verification failed for claim {batch_start + claim_index + 1}: {str(e)}")
                        batch_results[claim_index] = {
                            "claim": batch_claims[claim_index]['claim'],
                            "verdict": "Unverifiable",
                            "reasoning": f"Verification failed: {str(e)}",
                            "evidence_quality": "Insufficient",
                            "source_consensus": "Low",
                            "fallacies": ["None found"],
                            "confidence": 0.0
                        }
            
            for i in range(len(batch_claims)):
                if i in batch_results:
                    verified_claims.append(batch_results[i])
            
            if batch_end < len(claims_list):
                print("   Waiting 2 seconds before next batch...")
                time.sleep(2)
        
        
        print("\nStep 3: Ethics analysis...")
        analysis = chain2.invoke({
            "summary": claims_data['summary'], 
            "fallacies_list": fallacies_list
        })["text"]
        
        return {
            'title': article_title,
            'url': article_url,
            'summary': claims_data['summary'],
            'verified_claims': verified_claims,
            'analysis': analysis
        }
        
    except Exception as e:
        print(f"Error analyzing article: {str(e)}")
        return None

def calculate_overall_confidence(verified_claims):
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

def run_fact_checking():
    
    config = get_user_inputs()
    
    search_results = search_articles(config)
    if not search_results:
        return
    
    selected_articles = select_articles(search_results, config['num_articles'])
   
    for i, article in enumerate(selected_articles, 1):
        print(f"\n{'='*20} ARTICLE {i} of {len(selected_articles)} {'='*20}")
        
        result = analyze_article_with_verification(
            article, 
            config['max_chars'], 
            config['sources_per_claim']
        )
        if result:
            display_verification_results(result)
        
        if i < len(selected_articles):
            input("\nPress Enter to continue to next article...")

def display_verification_results(result):
    print("=" * 80)
    print("FACT-CHECKING REPORT (WITH EXTERNAL VERIFICATION)")
    print("=" * 80)
    print(f"Article: {result['title']}")
    print(f"🔗 URL: {result['url']}")
    print("=" * 80)
    
    print("\n SUMMARY:")
    print("-" * 40)
    print(result['summary'])
    
    
    overall_confidence = calculate_overall_confidence(result['verified_claims'])
    print(f"\n OVERALL CONFIDENCE SCORE: {overall_confidence:.2f}")
    
    print("\n VERIFIED CLAIMS ANALYSIS:")
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

def extract_json_from_response(response_text):
    import re
    
    try:
        return json.loads(response_text.strip())
    except json.JSONDecodeError:
        pass
    
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
    
    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass
    
    return {
        "summary": "JSON parsing failed - raw response included below",
        "claims": [],
        "red_flags": ["Failed to parse LLM response as JSON"],
        "confidence": 0.0,
        "raw_response": response_text
    }

if __name__ == "__main__":
    try:
        run_fact_checking()
        print("\n Fact-checking agent completed successfully!")
    except KeyboardInterrupt:
        print("\n Analysis cancelled by user.")
    except Exception as e:
        print(f"\n Error: {str(e)}")
