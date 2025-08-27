"""
Main entry point for the fact-checking system.
Run this file to start the interactive fact-checking agent.
"""

import warnings
warnings.filterwarnings('ignore')

from config import Config, get_user_inputs
from evidence_search import ArticleSearcher
from fact_checker import FactChecker
from utils import display_verification_results, load_fallacies_data

def main():
    """Main function to run the fact-checking system."""
    
    # Setup environment
    Config.setup_environment()
    
    # Load fallacies data
    fallacies_data = load_fallacies_data("fallacies.csv")
    
    # Get user configuration
    config = get_user_inputs()
    
    # Initialize components
    article_searcher = ArticleSearcher(Config.SERPER_API_KEY)
    fact_checker = FactChecker(
        gemini_api_key=Config.GEMINI_API_KEY,
        serper_api_key=Config.SERPER_API_KEY,
        fallacies_data=fallacies_data
    )
    
    # Search for articles
    search_results = article_searcher.search_articles(config)
    if not search_results:
        return
    
    # Select articles for analysis
    selected_articles = article_searcher.select_articles(
        search_results, 
        config['num_articles']
    )
    
    # Analyze each article
    for i, article in enumerate(selected_articles, 1):
        print(f"\n{'='*20} ARTICLE {i} of {len(selected_articles)} {'='*20}")
        
        result = fact_checker.analyze_article(
            article, 
            config['max_chars'], 
            config['sources_per_claim']
        )
        
        if result:
            display_verification_results(result)
        
        if i < len(selected_articles):
            input("\nPress Enter to continue to next article...")

if __name__ == "__main__":
    try:
        main()
        print("\n✅ Fact-checking agent completed successfully!")
    except KeyboardInterrupt:
        print("\n❌ Analysis cancelled by user.")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
