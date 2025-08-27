"""
Evidence search and verification functionality.
Handles searching for external evidence and evaluating source credibility.
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.utilities import GoogleSerperAPIWrapper
from config import Config

class EvidenceSearcher:
    """Handles searching for and evaluating evidence for fact-checking claims."""
    
    def __init__(self, serper_api_key):
        self.serper_api_key = serper_api_key
        self.credible_sources = Config.get_credible_sources()
        self.search = GoogleSerperAPIWrapper(
            type="news",
            tbs="qdr:y",  # Search within past year for evidence
            serper_api_key=serper_api_key
        )
    
    def get_full_evidence_content(self, url, max_chars=1200):
        """
        Load full content from a URL for evidence analysis.
        
        Args:
            url: URL to load content from
            max_chars: Maximum characters to extract
            
        Returns:
            str: Cleaned content or error message
        """
        try:
            loader = WebBaseLoader(url)
            content = loader.load()[0].page_content
            cleaned_content = ' '.join(content.split())[:max_chars]
            return cleaned_content if cleaned_content else "Content could not be extracted"
        except Exception as e:
            return f"Error loading content: {str(e)}"
    
    def calculate_source_credibility(self, source_domain):
        """
        Calculate credibility score for a source domain.
        
        Args:
            source_domain: Domain name of the source
            
        Returns:
            int: Credibility score (0-3)
        """
        if any(domain in source_domain for domain in self.credible_sources['tier1']):
            return 3
        elif any(domain in source_domain for domain in self.credible_sources['tier2']):
            return 2
        elif any(domain in source_domain for domain in self.credible_sources['diverse_sources']):
            return 1
        return 0
    
    def generate_search_queries(self, claim_text, search_terms):
        """
        Generate comprehensive search queries for a claim.
        
        Args:
            claim_text: The main claim to search for
            search_terms: Additional search terms for the claim
            
        Returns:
            list: List of search query strings
        """
        search_queries = []
        
        # Fact-checking sites first (highest priority)
        fact_check_sites = ['factcheck.org', 'snopes.com', 'politifact.com']
        for site in fact_check_sites:
            search_queries.append(f"site:{site} {search_terms[0]}")
        
        # Credible news sources
        news_sites = ['reuters.com', 'ap.org', 'bbc.com']
        for site in news_sites:
            search_queries.append(f"site:{site} {search_terms[0]}")
        
        # General fact-checking queries
        search_queries.append(f'"{search_terms[0]}" fact check')
        search_queries.append(f'"{search_terms[0]}" verified OR confirmed')
        
        # Research and analysis queries
        for term in search_terms[:2]:
            search_queries.append(f"{term} study OR research")
            search_queries.append(f"{term} report OR data")
        
        # Expert opinion queries
        for term in search_terms[:2]:
            search_queries.append(f"{term} analysis")
            search_queries.append(f"{term} expert opinion")
        
        return search_queries
    
    def search_for_evidence(self, claim_text, search_terms, sources_per_claim):
        """
        Search for evidence supporting or refuting a claim.
        
        Args:
            claim_text: The claim to verify
            search_terms: Search terms related to the claim
            sources_per_claim: Maximum number of sources to collect
            
        Returns:
            list: List of evidence items with content and metadata
        """
        all_evidence = []
        search_queries = self.generate_search_queries(claim_text, search_terms)
        
        sources_found = 0
        for query in search_queries:
            if sources_found >= sources_per_claim:
                break
                
            try:
                results = self.search.results(query)
                if results.get('news'):
                    for result in results['news'][:2]:  # Max 2 results per query
                        if sources_found >= sources_per_claim:
                            break
                        
                        source_url = result.get('link', '')
                        source_domain = source_url.split('/')[2] if '/' in source_url else ''
                        
                        credibility_score = self.calculate_source_credibility(source_domain)
                        
                        if credibility_score > 0:  # Only include credible sources
                            full_content = self.get_full_evidence_content(source_url, 1000)
                            
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
    
    def search_for_evidence_thread(self, claim_info, sources_per_claim):
        """
        Thread-safe wrapper for evidence searching.
        
        Args:
            claim_info: Dictionary containing claim and search terms
            sources_per_claim: Number of sources to search for
            
        Returns:
            list: Evidence search results
        """
        claim_text = claim_info['claim']
        search_terms = claim_info.get('search_terms', [claim_text])
        
        time.sleep(0.5)  # Rate limiting
        return self.search_for_evidence(claim_text, search_terms, sources_per_claim)

class ArticleSearcher:
    """Handles searching for news articles to analyze."""
    
    def __init__(self, serper_api_key):
        self.serper_api_key = serper_api_key
    
    def search_articles(self, config):
        """
        Search for news articles based on configuration.
        
        Args:
            config: Configuration dictionary with search parameters
            
        Returns:
            dict: Search results from Serper API
        """
        search = GoogleSerperAPIWrapper(
            type="news",
            tbs=config['time_range'],
            serper_api_key=self.serper_api_key
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
    
    def select_articles(self, search_results, num_articles):
        """
        Select articles from search results.
        
        Args:
            search_results: Results from article search
            num_articles: Number of articles to select
            
        Returns:
            list: Selected articles for analysis
        """
        news_articles = search_results['news']
        available_articles = min(len(news_articles), 10)
        
        print(f"\n📰 Found {len(news_articles)} articles. Showing top {available_articles}:")
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
