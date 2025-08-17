# 🔍 Agentic Fact-Check System 

An AI-powered fact-checking agent that automatically detects and verifies misinformation during global crises. The system scans multiple content streams, identifies factual claims, verifies them against reliable sources, and provides accessible explanations.

## 🌟 Features

- **Multi-Source Content Scanning**: Monitors RSS feeds, news sources (with free APIs)
- **Advanced NLP Claim Detection**: Uses FREE libraries (NLTK, TextBlob) for claim analysis
- **Pattern-Based Fact Verification**: Rule-based verification system
- **Real-time Monitoring**: Continuous scanning with configurable intervals
- **Crisis-Focused**: Specifically designed for crisis-related misinformation
- **Comprehensive Reporting**: Detailed analysis and actionable recommendations
- **100% Local Processing**: Everything runs on your computer - no data sent to paid services

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/HetanshWaghela/agentic_factcheck.git
cd agentic_factcheck

# Install dependencies (all free!)
pip install -r requirements.txt
```

### 2. Configuration (Optional)

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env ONLY if you want optional features
nano .env
```

**The system works completely without any API keys!** Optional free API keys:
- **News API Key**: Free 500 requests/day from [newsapi.org](https://newsapi.org)
- **Twitter Bearer Token**: Free social media monitoring (optional)

### 3. Run the System

```bash
# Run the main script
python main.py
```

Choose from:
1. **Single Cycle**: Run one complete fact-checking cycle
2. **Continuous Monitoring**: Monitor continuously with automatic intervals
3. **Exit**: Stop the program


### Technologies Used
- 🆓 **NLTK**: Natural language processing
- 🆓 **TextBlob**: Sentiment analysis and text processing
- 🆓 **RSS Feeds**: News content from major outlets
- 🆓 **Regex Patterns**: Advanced pattern matching for claim detection
- 🆓 **Python Libraries**: All open-source 

## 📁 Project Structure

```
agentic_factcheck/
├── src/
│   ├── __init__.py
│   ├── config.py              # Configuration and settings
│   ├── models.py              # Data structures and models
│   ├── content_scanner.py     # Content source scanning
│   ├── claim_detector.py      # Claim extraction and detection
│   ├── fact_verifier.py       # Fact verification logic
│   └── fact_checking_agent.py # Main orchestrator
├── data/                      # Data storage (created automatically)
├── output/                    # Results and reports (created automatically)
├── tests/                     # Test files (for future development)
├── main.py                    # Main entry point
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
└── README.md                 # This file
```

## 🔧 How It Works

### The Pipeline

1. **Content Scanning** 📡
   - Scans news APIs, RSS feeds
   - Filters content for crisis relevance
   - Scores content by importance

2. **Claim Detection** 🔍
   - Extracts factual statements
   - Classifies claims by type (statistics, events, policies)
   - Assesses urgency and verifiability

3. **Fact Verification** ✅
   - Cross-references with reliable sources
   - Analyzes evidence quality
   - Provides confidence scores and verdicts

4. **Results Generation** 📊
   - Comprehensive analysis reports
   - Actionable recommendations
   - Alert system for urgent misinformation

### Sample Output

```json
{
  "cycle_info": {
    "processing_time_seconds": 15.3,
    "start_time": "2025-08-16T10:00:00"
  },
  "content_summary": {
    "total_content_items": 25,
    "content_sources": ["BBC", "Reuters", "CNN"]
  },
  "verification_results": {
    "total_claims": 12,
    "verdict_breakdown": {
      "true": 7,
      "false": 2,
      "misleading": 2,
      "needs_context": 1
    },
    "average_confidence": 0.75
  },
  "alerts": {
    "urgent_false_claims": 1,
    "requires_immediate_attention": true
  }
}
```

## ⚙️ Configuration

### Environment Variables (.env)

```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here
NEWS_API_KEY=your_news_api_key_here

# Optional
TWITTER_BEARER_TOKEN=your_twitter_token_here
SCAN_INTERVAL_MINUTES=60
MAX_CONTENT_AGE_HOURS=24
LLM_MODEL=gpt-4o-mini
BATCH_SIZE=20
LOG_LEVEL=INFO
```

### Crisis Keywords

The system monitors for crisis-related content using keywords like:
- Health: `pandemic`, `covid`, `outbreak`, `epidemic`
- Climate: `climate change`, `natural disaster`, `hurricane`, `wildfire`
- Geopolitical: `war`, `conflict`, `invasion`, `terrorism`
- Economic: `recession`, `inflation`, `market crash`

You can customize these in `src/config.py`.

## 📊 Understanding Results

### Claim Types
- **Statistic**: Numerical claims, percentages, research findings
- **Event**: Things that happened or will happen
- **Policy**: Government decisions, regulations, official announcements

### Verdicts
- **True** ✅: Claim is factually accurate
- **False** ❌: Claim is demonstrably false
- **Misleading** ⚠️: Partially true but missing crucial context
- **Needs Context** 📝: True but requires additional information
- **Unverifiable** ❓: Cannot be verified with available sources

### Urgency Scale (1-10)
- **1-3**: Low urgency, standard monitoring
- **4-6**: Medium urgency, increased attention
- **7-10**: High urgency, immediate response needed

## 🔮 Future Enhancements

This is a foundational system that can be extended with:

### Advanced Features
- **OpenAI Integration**: Full AI-powered claim analysis
- **Social Media Monitoring**: Real-time Twitter/Facebook scanning
- **Multilingual Support**: Content processing in multiple languages
- **Web Search**: Automated evidence gathering from the web
- **Human-in-the-Loop**: Expert validation workflows

### Technical Improvements
- **Rate Limiting**: Smart API usage management
- **Caching**: Reduce redundant API calls
- **Database Storage**: Persistent data storage
- **Web Dashboard**: Real-time monitoring interface
- **API Endpoints**: RESTful API for integration


**Built with ❤️ for fighting misinformation during crises**
