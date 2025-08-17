"""
Agentic Fact-Check System - Main Entry Point

This is the main script to run the fact-checking agent.
It provides a simple command-line interface to start the system.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent / 'src'))

from src.config import Config
from src.fact_checking_agent import FactCheckingAgent

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('fact_check.log')
    ]
)

logger = logging.getLogger(__name__)


async def main():
    """Main function to run the fact-checking system."""
    
    print("🔍 Agentic Fact-Check System")
    print("=" * 40)
    
    try:
        # Initialize configuration
        config = Config()
        
        # Create the fact-checking agent
        agent = FactCheckingAgent(config)
        
        # Validate setup
        if not agent.validate_setup():
            print("\n❌ System setup validation failed!")
            print("Please check your configuration and API keys.")
            return
        
        print("\n✅ System setup validated successfully!")
        print(f"📊 Configuration summary: {config.get_summary()}")
        
        # Ask user what they want to do
        print("\nChoose an option:")
        print("1. Run a single fact-check cycle")
        print("2. Start continuous monitoring")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            print("\n🚀 Running single fact-check cycle...")
            results = await agent.run_fact_check_cycle()
            print_results_summary(results)
            
        elif choice == "2":
            print("\n🔄 Starting continuous monitoring...")
            print("Press Ctrl+C to stop")
            await agent.run_continuous_monitoring()
            
        elif choice == "3":
            print("\n👋 Goodbye!")
            
        else:
            print("\n❌ Invalid choice. Please run the program again.")
    
    except KeyboardInterrupt:
        print("\n\n🛑 System stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\n💥 An error occurred: {e}")


def print_results_summary(results):
    """Print a summary of the fact-checking results."""
    print("\n" + "=" * 50)
    print("📋 FACT-CHECK RESULTS SUMMARY")
    print("=" * 50)
    
    cycle_info = results.get('cycle_info', {})
    content_summary = results.get('content_summary', {})
    claims_analysis = results.get('claims_analysis', {})
    verification_results = results.get('verification_results', {})
    alerts = results.get('alerts', {})
    
    # Basic stats
    print(f"⏱️  Processing time: {cycle_info.get('processing_time_seconds', 0):.2f} seconds")
    print(f"📰 Content items scanned: {content_summary.get('total_content_items', 0)}")
    print(f"🔍 Claims detected: {claims_analysis.get('total_claims', 0)}")
    
    # Verification breakdown
    if verification_results.get('total_claims', 0) > 0:
        print(f"\n📊 Verification Results:")
        verdict_breakdown = verification_results.get('verdict_breakdown', {})
        for verdict, count in verdict_breakdown.items():
            emoji = get_verdict_emoji(verdict)
            print(f"   {emoji} {verdict.title()}: {count}")
        
        avg_confidence = verification_results.get('average_confidence', 0)
        print(f"🎯 Average confidence: {avg_confidence:.2f}")
    
    # Alerts
    if alerts.get('requires_immediate_attention', False):
        print(f"\n🚨 ALERTS:")
        print(f"   ⚠️  Urgent false claims: {alerts.get('urgent_false_claims', 0)}")
        print(f"   📢 Total false/misleading: {alerts.get('total_false_misleading', 0)}")
    
    # Recommendations
    recommendations = results.get('recommendations', [])
    if recommendations:
        print(f"\n💡 Recommendations:")
        for rec in recommendations:
            print(f"   • {rec}")
    
    print("\n✅ Results saved to output/ directory")
    print("=" * 50)


def get_verdict_emoji(verdict):
    """Get emoji for different verdict types."""
    emoji_map = {
        'true': '✅',
        'false': '❌',
        'misleading': '⚠️',
        'needs_context': '📝',
        'unverifiable': '❓',
        'error': '💥'
    }
    return emoji_map.get(verdict, '❔')


if __name__ == "__main__":
    # Run the main function
    asyncio.run(main())
