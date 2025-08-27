"""
Core fact-checking functionality.
Contains the main FactChecker class that orchestrates the analysis pipeline.
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_community.document_loaders import WebBaseLoader
from langchain_google_genai import ChatGoogleGenerativeAI

from config import Config
from evidence_search import EvidenceSearcher
from prompts import (
    get_claim_extraction_template,
    get_claim_verification_template, 
    get_ethics_analysis_template
)
from utils import (
    extract_json_from_response,
    format_evidence_for_llm,
    calculate_overall_confidence,
    load_fallacies_data
)

class FactChecker:
    """Main fact-checking class that orchestrates the analysis pipeline."""
    
    def __init__(self, gemini_api_key, serper_api_key, fallacies_data=None):
        """
        Initialize the fact checker with API keys and configuration.
        
        Args:
            gemini_api_key: API key for Gemini LLM
            serper_api_key: API key for Serper search
            fallacies_data: Fallacies data string (optional)
        """
        # Initialize LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash", 
            temperature=0, 
            max_output_tokens=1024, 
            google_api_key=gemini_api_key
        )
        
        # Initialize search components
        self.evidence_searcher = EvidenceSearcher(serper_api_key)
        
        # Load fallacies data
        self.fallacies_list = fallacies_data or load_fallacies_data()
        
        # Initialize LLM chains
        self._setup_chains()
    
    def _setup_chains(self):
        """Set up LangChain LLM chains for different tasks."""
        # Claim extraction chain
        self.claim_extraction_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate(
                template=get_claim_extraction_template(),
                input_variables=["content"]
            )
        )
        
        # Claim verification chain
        self.claim_verification_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate(
                template=get_claim_verification_template(),
                input_variables=["claim", "evidence", "fallacies_list"]
            )
        )
        
        # Ethics analysis chain
        self.ethics_analysis_chain = LLMChain(
            llm=self.llm,
            prompt=PromptTemplate(
                template=get_ethics_analysis_template(),
                input_variables=["summary", "fallacies_list"]
            )
        )
    
    def extract_claims_from_article(self, article_content):
        """
        Extract verifiable claims from article content.
        
        Args:
            article_content: Text content of the article
            
        Returns:
            dict: Extracted claims and summary data
        """
        print("Step 1: Extracting claims...")
        
        claims_response = self.claim_extraction_chain.invoke({"content": article_content})["text"]
        claims_data = extract_json_from_response(claims_response)
        
        if not claims_data.get('claims'):
            return None
        
        print(f"✓ Extracted {len(claims_data['claims'])} claims")
        return claims_data
    
    def verify_claim_thread(self, claim_info, evidence):
        """
        Thread-safe claim verification function.
        
        Args:
            claim_info: Dictionary containing claim information
            evidence: List of evidence items for the claim
            
        Returns:
            dict: Verification results
        """
        claim_text = claim_info['claim']
        evidence_formatted = format_evidence_for_llm(evidence)
        
        time.sleep(0.3)  # Rate limiting
        
        verification_response = self.claim_verification_chain.invoke({
            "claim": claim_text,
            "evidence": evidence_formatted,
            "fallacies_list": self.fallacies_list
        })["text"]
        
        return extract_json_from_response(verification_response)
    
    def verify_claims_parallel(self, claims_list, sources_per_claim):
        """
        Verify claims in parallel batches for better performance.
        
        Args:
            claims_list: List of claims to verify
            sources_per_claim: Number of evidence sources per claim
            
        Returns:
            list: List of verified claims with verdicts
        """
        print("\nStep 2: Verifying claims in parallel...")
        verified_claims = []
        
        batch_size = Config.BATCH_SIZE
        
        for batch_start in range(0, len(claims_list), batch_size):
            batch_end = min(batch_start + batch_size, len(claims_list))
            batch_claims = claims_list[batch_start:batch_end]
            
            print(f"Processing batch {batch_start//batch_size + 1}: claims {batch_start+1}-{batch_end}")
            
            # Search for evidence in parallel
            with ThreadPoolExecutor(max_workers=3) as executor:
                evidence_futures = {
                    executor.submit(
                        self.evidence_searcher.search_for_evidence_thread, 
                        claim_info, 
                        sources_per_claim
                    ): i 
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
            
            # Verify claims in parallel
            with ThreadPoolExecutor(max_workers=3) as executor:
                verification_futures = {
                    executor.submit(
                        self.verify_claim_thread, 
                        batch_claims[i], 
                        evidence_results.get(i, [])
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
            
            # Collect batch results
            for i in range(len(batch_claims)):
                if i in batch_results:
                    verified_claims.append(batch_results[i])
            
            # Rate limiting between batches
            if batch_end < len(claims_list):
                print("   Waiting 2 seconds before next batch...")
                time.sleep(2)
        
        return verified_claims
    
    def generate_ethics_analysis(self, summary):
        """
        Generate ethics professor analysis of the article.
        
        Args:
            summary: Article summary text
            
        Returns:
            str: Ethics analysis text
        """
        print("\nStep 3: Ethics analysis...")
        
        analysis_response = self.ethics_analysis_chain.invoke({
            "summary": summary, 
            "fallacies_list": self.fallacies_list
        })["text"]
        
        return analysis_response
    
    def analyze_article(self, article, max_chars, sources_per_claim):
        """
        Complete analysis pipeline for a single article.
        
        Args:
            article: Article dictionary with title and link
            max_chars: Maximum characters to analyze
            sources_per_claim: Number of evidence sources per claim
            
        Returns:
            dict: Complete analysis results
        """
        article_url = article['link']
        article_title = article['title']
        
        print(f"\n📰 Loading article: {article_title}")
        
        try:
            # Load article content
            loader = WebBaseLoader(article_url)
            article_text = ' '.join(loader.load()[0].page_content[:max_chars].split())
            
            # Extract claims
            claims_data = self.extract_claims_from_article(article_text)
            if not claims_data:
                return None
            
            # Verify claims in parallel
            verified_claims = self.verify_claims_parallel(
                claims_data['claims'], 
                sources_per_claim
            )
            
            # Generate ethics analysis
            ethics_analysis = self.generate_ethics_analysis(claims_data['summary'])
            
            return {
                'title': article_title,
                'url': article_url,
                'summary': claims_data['summary'],
                'verified_claims': verified_claims,
                'analysis': ethics_analysis
            }
            
        except Exception as e:
            print(f"Error analyzing article: {str(e)}")
            return None
    
    def analyze_multiple_articles(self, articles, max_chars, sources_per_claim):
        """
        Analyze multiple articles sequentially.
        
        Args:
            articles: List of article dictionaries
            max_chars: Maximum characters to analyze per article
            sources_per_claim: Number of evidence sources per claim
            
        Returns:
            list: List of analysis results
        """
        results = []
        
        for i, article in enumerate(articles, 1):
            print(f"\n{'='*20} ARTICLE {i} of {len(articles)} {'='*20}")
            
            result = self.analyze_article(article, max_chars, sources_per_claim)
            if result:
                results.append(result)
            
            if i < len(articles):
                input("\nPress Enter to continue to next article...")
        
        return results
